import cv2
import mediapipe as mp
import numpy as np
import pygame
import time

# 初始化 MediaPipe Hands 模块
handsModule = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# 初始化 Pygame
pygame.init()
width, height = 640, 480
screen = pygame.display.set_mode((width, height))
font = pygame.font.Font(None, 74)

# 定义全局变量
not_quit = True
background = np.zeros((height, width, 3), dtype=np.uint8)


# 用于判断手指方向的辅助函数
def get_finger_direction(landmarks):
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


# 主循环
def main():
    global not_quit
    with handsModule.Hands(static_image_mode=False, min_detection_confidence=0.7, min_tracking_confidence=0.7,
                           max_num_hands=1) as hands:
        cap = cv2.VideoCapture(0)
        try:
            while not_quit:
                ret, frame = cap.read()
                if not ret:
                    break

                # 翻转图像，使其看起来更自然
                frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(frame_rgb)

                # 重置背景
                background = np.zeros((height, width, 3), dtype=np.uint8)
                direction_text = ""

                # 检测到手部
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # 获取手指方向
                        direction = get_finger_direction(hand_landmarks.landmark)
                        direction_text = f"Direction: {direction}"

                        # 在图像上绘制手部关键点
                        mp_drawing.draw_landmarks(frame, hand_landmarks, handsModule.HAND_CONNECTIONS)
                        # 在指尖位置绘制红色圆圈
                        index_finger_tip = hand_landmarks.landmark[8]
                        h, w, _ = frame.shape
                        cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

                # 使用 Pygame 显示方向和摄像头图像
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_surface = pygame.surfarray.make_surface(frame)
                rotated_screen = pygame.transform.rotate(frame_surface, -90)
                screen.blit(rotated_screen, (0, 0))
                if direction_text:
                    text_surface = font.render(direction_text, True, (255, 255, 255))
                    screen.blit(text_surface, (50, 50))
                pygame.display.flip()

                # 检测退出事件
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        not_quit = False
                    if event.type == pygame.KEYDOWN:
                    # 检测到按键按下事件
                        if event.key == pygame.K_UP:
                            # 按下了上箭头键
                            print("Up Arrow Key Pressed")
                        elif event.key == pygame.K_q:
                            # quit
                            print("q Key Pressed")
                            not_quit = False
                # # 按下 'q' 键退出
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     not_quit = False
        except KeyboardInterrupt:
            # pass
            not_quit = False
        finally:
            cap.release()
            pygame.quit()


if __name__ == "__main__":
    main()
