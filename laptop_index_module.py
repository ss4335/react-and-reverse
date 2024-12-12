import cv2
import mediapipe as mp
import numpy as np
import pygame
import threading

class GestureRecognition:
    def __init__(self):
        # 初始化 MediaPipe Hands 模块
        self.handsModule = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        
        # 初始化变量
        self.current_gesture = None
        self.gesture_lock = threading.Lock()
        self.frame = None
        self.frame_lock = threading.Lock()
        self.running = True
        
        # 初始化摄像头
        self.cap = cv2.VideoCapture(0)
        
        # 创建手部识别器
        self.hands = self.handsModule.Hands(
            static_image_mode=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            max_num_hands=1
        )

    def get_finger_direction(self, landmarks):
        wrist = landmarks[0]  # 手腕
        index_finger_tip = landmarks[8]  # 食指尖端
        dx = index_finger_tip.x - wrist.x
        dy = index_finger_tip.y - wrist.y

        if abs(dx) > abs(dy):
            if dx > 0:
                return "Right"
            else:
                return "Left"
        else:
            if dy > 0:
                return "Down"
            else:
                return "Up"

    def get_current_gesture(self):
        with self.gesture_lock:
            return self.current_gesture

    def get_current_frame(self):
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None

    def process_frame(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # 翻转图像
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(frame_rgb)

            # 处理手势识别
            direction = None
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # 获取手指方向
                    direction = self.get_finger_direction(hand_landmarks.landmark)
                    
                    # 绘制手部关键点
                    self.mp_drawing.draw_landmarks(
                        frame, 
                        hand_landmarks, 
                        self.handsModule.HAND_CONNECTIONS
                    )
                    
                    # 在指尖位置绘制红色圆圈
                    index_finger_tip = hand_landmarks.landmark[8]
                    h, w, _ = frame.shape
                    cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

            # 更新当前手势和帧
            with self.gesture_lock:
                self.current_gesture = direction
            
            with self.frame_lock:
                self.frame = frame

    def start(self):
        # 启动处理线程
        self.process_thread = threading.Thread(target=self.process_frame)
        self.process_thread.start()

    def stop(self):
        # 停止处理
        self.running = False
        if hasattr(self, 'process_thread'):
            self.process_thread.join()
        self.cap.release()
