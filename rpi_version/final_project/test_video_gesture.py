import cv2
import time
import os
import pygame
from pygame.locals import *
import numpy as np
from picamera2 import Picamera2
import RPi.GPIO as GPIO
import mediapipe as mp

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_hands=1
)

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize pygame
print("Setting up environment variables...")
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')

print("Initializing pygame...")
pygame.init()

# Setup display
# DISPLAY_WIDTH = 320
# DISPLAY_HEIGHT = 240
# DISPLAY_WIDTH = 640
# DISPLAY_HEIGHT = 480
DISPLAY_WIDTH = 1080
DISPLAY_HEIGHT = 720
pygame.mouse.set_visible(False)
lcd = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))

# Initialize camera
print("Initializing camera...")
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(
    main={"size": (1920, 1080), "format": "RGB888"}
)
picam2.configure(preview_config)
picam2.start()
time.sleep(2)

def get_finger_direction(landmarks):
    wrist = landmarks[0]
    index_finger_tip = landmarks[8]
    dx = index_finger_tip.x - wrist.x
    dy = index_finger_tip.y - wrist.y
    
    threshold = 0.1
    if abs(dx) > abs(dy):
        if dx > threshold:
            return "Right"
        elif dx < -threshold:
            return "Left"
    else:
        if dy > threshold:
            return "Down"
        elif dy < -threshold:
            return "Up"
    return None  # Return None instead of "Center"

def cv2_frame_to_pygame(frame):
    frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
    frame = cv2.flip(frame, -1)
    frame = np.rot90(frame, k=3)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return pygame.surfarray.make_surface(frame)

try:
    running = True
    frame_count = 0
    start_time = time.time()
    
    while running:
        # Capture and preprocess frame
        frame = picam2.capture_array()
        frame = cv2.resize(frame, (1920, 1080))
        
        # Process frame for hand detection
        results = hands.process(frame)
        
        # Handle hand detection and drawing
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on frame
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Get and print direction
                direction = get_finger_direction(hand_landmarks.landmark)
                if direction:  # Only print if direction is not None
                    print(f"\rDirection: {direction}", end="", flush=True)
                
                # Draw red circle at index finger tip
                index_finger_tip = hand_landmarks.landmark[8]
                h, w, _ = frame.shape
                cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        
        # Convert and display frame on PiTFT
        pygame_frame = cv2_frame_to_pygame(frame)
        lcd.blit(pygame_frame, (0,0))
        pygame.display.flip()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_q:
                    running = False
        
        # Check GPIO button for quit
        if not GPIO.input(22):
            running = False
            time.sleep(0.3)
        
        frame_count += 1
        if frame_count % 30 == 0:
            end_time = time.time()
            fps = 30 / (end_time - start_time)
            print(f"\nFPS: {fps:.2f}")
            start_time = time.time()

except KeyboardInterrupt:
    print("\nProgram stopped by user")
finally:
    picam2.stop()
    pygame.quit()
    GPIO.cleanup() 