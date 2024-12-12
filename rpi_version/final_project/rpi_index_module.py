import cv2
import mediapipe as mp
import numpy as np
import pygame
import threading
from picamera2 import Picamera2

class GestureRecognition:
    def __init__(self):
        # Initialize MediaPipe Hands module
        self.handsModule = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize variables
        self.current_gesture = None
        self.gesture_lock = threading.Lock()
        self.frame = None
        self.frame_lock = threading.Lock()
        self.running = True
        
        # Initialize PiCamera2
        self.cap = Picamera2()
        preview_config = self.cap.create_preview_configuration(
            main={"size": (1920, 1080), "format": "RGB888"}
        )
        self.cap.configure(preview_config)
        self.cap.start()
        
        # Create hand detector
        self.hands = self.handsModule.Hands(
            static_image_mode=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            max_num_hands=1
        )

    def get_finger_direction(self, landmarks):
        wrist = landmarks[0]  # Wrist point
        index_finger_tip = landmarks[8]  # Index finger tip
        dx = index_finger_tip.x - wrist.x
        dy = index_finger_tip.y - wrist.y

        # Add threshold to determine if direction is clear
        threshold = 0.1  # Adjust threshold as needed

        if abs(dx) < threshold and abs(dy) < threshold:
            return "None"  # Return None when direction is unclear
        elif abs(dx) > abs(dy):
            if dx > 0:
                return "Left"
            else:
                return "Right"
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
            # Capture frame
            frame = self.cap.capture_array()
            frame = cv2.resize(frame, (640, 480))
            
            # Convert to RGB format for gesture recognition
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame for hand detection
            results = self.hands.process(frame_rgb)
            
            # Update current gesture state
            with self.gesture_lock:
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Get finger direction
                        direction = self.get_finger_direction(hand_landmarks.landmark)
                        
                        # Draw hand landmarks
                        self.mp_drawing.draw_landmarks(
                            frame, 
                            hand_landmarks, 
                            self.handsModule.HAND_CONNECTIONS
                        )
                        
                        # Draw red circle at fingertip
                        index_finger_tip = hand_landmarks.landmark[8]
                        h, w, _ = frame.shape
                        cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                        
                        # Update current gesture
                        self.current_gesture = direction
                else:
                    # Set to None when no hand is detected
                    self.current_gesture = "None"
            
            # Update current frame
            with self.frame_lock:
                self.frame = frame

    def start(self):
        self.process_thread = threading.Thread(target=self.process_frame)
        self.process_thread.start()

    def stop(self):
        self.running = False
        if hasattr(self, 'process_thread'):
            self.process_thread.join()
        self.cap.stop() 