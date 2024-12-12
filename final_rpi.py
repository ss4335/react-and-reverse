import math
import os
import subprocess
import time
import cv2
import mediapipe
import numpy as np
import pygame
import RPi.GPIO as GPIO
from module import findnameoflandmark, findpostion, speak

# Create a black image as the background
width, height = 640, 480
background = np.zeros((height, width, 3), dtype=np.uint8)
font = cv2.FONT_HERSHEY_DUPLEX
white = (255, 255, 255)

# Tabs & Pages
main_tabs = ["Tutorial", "Light", "Fan", "Speaker"]
tutorial_tabs = ["Return"]
light_tabs = ["On/Off", "Brightness", "Return"]
power_tabs = ["Brightness", "Return"]
brightness_tabs = ["On/Off", "Return"]
speaker_tabs = ["Song List", "Return"]
song_tabs = ["Playback", "Return"]
fan_tabs = ["Return"]
double_prev = 0
double_next = 0

MAIN_PAGE = 0
TUTORIAL_PAGE = 1
POWER_PAGE = 2
BRIGHTNESS_PAGE = 3
SPEAKER_PAGE = 4
SONG_PAGE = 5
FAN_PAGE = 6
current_page = MAIN_PAGE
window_name = "HI HELLO :)))"

# Light Settings
colors = ["RED: ", "BLUE: ", "GREEN: ", "YELLOW: "]
red_light = False
blue_light = False
green_light = False
yellow_light = False
red_pin = 4  # gpio4
blue_pin = 17  # gpio17
green_pin = 27  # gpio27
yellow_pin = 22  # gpio22
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(red_pin, GPIO.OUT)
GPIO.setup(blue_pin, GPIO.OUT)
GPIO.setup(green_pin, GPIO.OUT)
GPIO.setup(yellow_pin, GPIO.OUT)
red_freq = 100
red_duty_cycle = 100
red_pwm = GPIO.PWM(red_pin, red_freq)
blue_freq = 100
blue_duty_cycle = 100
blue_pwm = GPIO.PWM(blue_pin, blue_freq)
green_freq = 100
green_duty_cycle = 100
green_pwm = GPIO.PWM(green_pin, green_freq)
yellow_freq = 100
yellow_duty_cycle = 100
yellow_pwm = GPIO.PWM(yellow_pin, yellow_freq)
GPIO.output(red_pin, GPIO.LOW)
GPIO.output(blue_pin, GPIO.LOW)
GPIO.output(yellow_pin, GPIO.LOW)
GPIO.output(green_pin, GPIO.LOW)

# Setting Up Motor
motor_pwm = 26  # gpio4
motor_run = 6
motor_freq = 150
motor_duty_cycle = 3
motor_on = False
GPIO.setmode(GPIO.BCM)
GPIO.setup(motor_pwm, GPIO.OUT)
GPIO.setup(motor_run, GPIO.OUT)
motor_pwm = GPIO.PWM(motor_pwm, motor_freq)
GPIO.output(motor_run, GPIO.LOW)

# Setting Up Shutdown Button
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def shutdown():
    subprocess.call(['sudo shutdown -h now'], shell=True)


# Drawing the Different Pages
def draw_tutorial_page(tabs):
    global background
    num_tabs = len(tabs)
    tab_width = width // num_tabs
    for i in range(num_tabs):
        text_position = ((i * tab_width) + tab_width // 2 - 30, 35)
        cv2.putText(
            background, tabs[i], text_position, font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, "- Use 1 finger to navigate and click", (35, 100), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, "- Use 2 fingers to adjust the brightness of the LEDs, speed of the",
        (35, 140), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, "  fan, and volume of the speaker",
        (35, 180), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, "  -> Make sure to have your fingers inside the box displayed",
        (35, 220), font, 0.5, white, 1, cv2.LINE_AA)


def draw_home_page(tabs):
    global background
    num_tabs = len(tabs)
    tab_width = width // num_tabs
    for i in range(num_tabs):
        text_position = ((i * tab_width) + tab_width // 2 - 30, 35)
        cv2.putText(
            background, tabs[i], text_position, font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, "Quit", (580, 400), font, 0.5, white, 1, cv2.LINE_AA)


def draw_power_page(tabs):
    global background
    num_tabs = len(tabs)
    tab_width = width // num_tabs
    # Draw the navigation bar
    for i in range(num_tabs):
        text_position = ((i * tab_width) + tab_width // 2 - 30, 35)
        cv2.putText(
            background, tabs[i], text_position, font, 0.5, white, 1, cv2.LINE_AA)
    # Draw Colors Options
    cv2.putText(
        background, 'ON/OFF', (235, 75), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, colors[0], (35, 150), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, colors[1], (35, 225), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, colors[2], (35, 300), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, colors[3], (35, 375), font, 0.5, white, 1, cv2.LINE_AA)
    # Draw Power
    if (red_light):
        cv2.putText(
            background, "ON", (235, 150), font, 0.5, white, 1, cv2.LINE_AA)
        red_pwm.start(100)
    else:
        cv2.putText(
            background, 'OFF', (235, 150), font, 0.5, white, 1, cv2.LINE_AA)
        red_pwm.start(0)
    if (blue_light):
        cv2.putText(
            background, "ON", (235, 225), font, 0.5, white, 1, cv2.LINE_AA)
        blue_pwm.start(100)
    else:
        cv2.putText(
            background, 'OFF', (235, 225), font, 0.5, white, 1, cv2.LINE_AA)
        blue_pwm.start(0)
    if (green_light):
        cv2.putText(
            background, "ON", (235, 300), font, 0.5, white, 1, cv2.LINE_AA)
        green_pwm.start(100)
    else:
        cv2.putText(
            background, 'OFF', (235, 300), font, 0.5, white, 1, cv2.LINE_AA)
        green_pwm.start(0)
    if (yellow_light):
        cv2.putText(
            background, "ON", (235, 375), font, 0.5, white, 1, cv2.LINE_AA)
        yellow_pwm.start(100)
    else:
        cv2.putText(
            background, 'OFF', (235, 375), font, 0.5, white, 1, cv2.LINE_AA)
        yellow_pwm.start(0)


def draw_brightness_page(tabs):
    global background
    num_tabs = len(tabs)
    tab_width = width // num_tabs
    # Draw the navigation bar
    for i in range(num_tabs):
        text_position = ((i * tab_width) + tab_width // 2 - 30, 35)
        cv2.putText(
            background, tabs[i], text_position, font, 0.5, white, 1, cv2.LINE_AA)
    # Draw Colors Options
    cv2.putText(
        background, 'SET BRIGHTNESS', (250, 75), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, colors[0], (85, 105), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.rectangle(background, (85, 125), (285, 250), white, 2)
    cv2.putText(
        background, colors[1], (390, 105), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.rectangle(background, (390, 125), (590, 250), white, 2)
    cv2.putText(
        background, colors[2], (85, 280), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.rectangle(background, (85, 300), (285, 425), white, 2)
    cv2.putText(
        background, colors[3], (390, 280), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.rectangle(background, (390, 300), (590, 425), white, 2)


def draw_speaker_page(tabs):
    global background
    num_tabs = len(tabs)
    tab_width = width // num_tabs
    # Draw the navigation bar
    for i in range(num_tabs):
        text_position = ((i * tab_width) + tab_width // 2 - 30, 35)
        cv2.putText(background, tabs[i], text_position,
                    font, 0.5, white, 1, cv2.LINE_AA)
    # Draw Playback Options
    speaker_playback = ["Play/Pause", "Previous Track", "Skip Track"]
    cv2.putText(
        background, speaker_playback[0], (35, 110), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, speaker_playback[1], (35, 260), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.putText(
        background, speaker_playback[2], (35, 410), font, 0.5, white, 1, cv2.LINE_AA)
    cv2.rectangle(background, (240, 110), (580, 400), white, 2)


def draw_song_page(tabs):
    global background
    num_tabs = len(tabs)
    tab_width = width // num_tabs
    # Draw the navigation bar
    for i in range(num_tabs):
        text_position = ((i * tab_width) + tab_width // 2 - 30, 35)
        cv2.putText(background, tabs[i], text_position,
                    font, 0.5, white, 1, cv2.LINE_AA)
    # Draw Song List
    music_folder = "/home/pi/project2/song_list"
    music_files = [f for f in os.listdir(music_folder)]
    song_height = (height - 50) // len(music_files)
    for i in range(len(music_files)):
        text_position = (35, (i * song_height) + song_height // 2 + 50)
        cv2.putText(background, music_files[i], text_position,
                    font, 0.5, white, 1, cv2.LINE_AA)


def draw_fan_page(tabs):
    global background, motor_on
    num_tabs = len(tabs)
    tab_width = width // num_tabs
    # Draw the navigation bar
    for i in range(num_tabs):
        text_position = ((i * tab_width) + tab_width // 2 - 30, 35)
        cv2.putText(background, tabs[i], text_position,
                    font, 0.5, white, 1, cv2.LINE_AA)
    cv2.rectangle(background, (240, 110), (580, 400), white, 2)
    if (motor_on):
        cv2.putText(
            background, "ON", (35, 110), font, 0.5, white, 1, cv2.LINE_AA)
        GPIO.output(motor_run, GPIO.HIGH)
    else:
        cv2.putText(
            background, 'OFF', (35, 110), font, 0.5, white, 1, cv2.LINE_AA)
        GPIO.output(motor_run, GPIO.LOW)


# SPEAKER SETTINGS
# Initializations
pygame.init()
pygame.mixer.pre_init()
pygame.mixer.init()
pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
screen = pygame.display.set_mode((640, 480))

# Access Music
music_folder = "/home/pi/project2/song_list"
music_files = [f for f in os.listdir(music_folder)]

# Set initial values & Load the first song
current_track_index = 0
paused = False
volume = 0.5
current_track = os.path.join(music_folder, music_files[current_track_index])
pygame.mixer.music.load(current_track)
pygame.mixer.music.set_volume(volume)


# Functions for controlling music


def play_pause():
    global paused
    with open('audio.txt', 'a') as file:
        if paused:
            file.write('play\n')
            paused = False
        else:
            file.write('pause\n')
            paused = True


def next_track():
    global double_next
    with open('audio.txt', 'a') as file:
        if double_next:
            file.write('next\n')
            double_next = 0
        else:
            file.write('nextnext\n')
            double_next = 1


def prev_track():
    global double_prev
    with open('audio.txt', 'a') as file:
        if double_prev:
            file.write('prev\n')
            double_prev = 0
        else:
            file.write('prevprev\n')
            double_prev = 1


def load_and_play():
    global paused
    current_track = os.path.join(
        music_folder, music_files[current_track_index])
    pygame.mixer.music.load(current_track)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play()
    paused = False


# Navigating Through The Navigation Bar & The Page Functions


def handle_mouse_event(x, y, dist):
    global red_duty_cycle, blue_duty_cycle, yellow_duty_cycle, green_duty_cycle
    global speed, motor_on
    global start_time
    start_time = time.time()
    global current_page, red_light, blue_light, green_light, yellow_light
    global volume, paused
    if current_page == MAIN_PAGE:
        if 0 < y < 50:
            if 0 < x < 160:
                current_page = TUTORIAL_PAGE
            elif 160 < x < 320:
                current_page = POWER_PAGE
            elif 320 < x < 480:
                current_page = FAN_PAGE
            elif 480 < x < 640:
                current_page = SPEAKER_PAGE
        if 550 < x < 650 and 350 < y < 450:
            print("quit from text")
            clean()
    elif current_page == TUTORIAL_PAGE:
        if 0 < y < 50 and 213 < x < 426:
            current_page = MAIN_PAGE
    elif current_page == POWER_PAGE:
        if 0 < y < 50:
            if 0 < x < 320:
                current_page = BRIGHTNESS_PAGE
            elif 320 < x < 640:
                current_page = MAIN_PAGE
        elif 200 < x < 270 and 120 < y < 180:
            red_light = not red_light
        elif 200 < x < 270 and 195 < y < 255:
            blue_light = not blue_light
        elif 200 < x < 270 and 270 < y < 320:
            green_light = not green_light
        elif 200 < x < 270 and 345 < y < 395:
            yellow_light = not yellow_light
    elif current_page == BRIGHTNESS_PAGE:
        if 0 < y < 50:
            if 0 < x < 320:
                current_page = POWER_PAGE
            elif 320 < x < 640:
                current_page = MAIN_PAGE
        elif 85 < x < 285 and 125 < y < 250:
            if red_light:
                start_time = start_time - 2
                red_duty_cycle = min(dist, 100)
                red_pwm.start(red_duty_cycle)
                print(dist)
                print(red_duty_cycle)
                print("adjusting red light")
        elif 390 < x < 590 and 125 < y < 250:
            if blue_light:
                start_time = start_time - 2
                blue_duty_cycle = min(dist, 100)
                blue_pwm.start(blue_duty_cycle)
                print("adjusting blue light")
        elif 85 < x < 285 and 300 < y < 425:
            if green_light:
                start_time = start_time - 3
                green_duty_cycle = min(dist, 100)
                green_pwm.start(green_duty_cycle)
                print("adjusting green light")
        elif 390 < x < 590 and 300 < y < 425:
            if yellow_light:
                start_time = start_time - 2
                yellow_duty_cycle = min(dist, 100)
                yellow_pwm.start(yellow_duty_cycle)
                print("adjusting yellow light")
    elif current_page == SPEAKER_PAGE:
        if 0 < y < 50:
            if 0 < x < 320:
                current_page = SONG_PAGE
            elif 320 < x < 640:
                current_page = MAIN_PAGE
        elif y > 50 and 35 < x < 160:
            if 60 < y < 160:
                print("play/pause")
                play_pause()
            elif 210 < y < 310:
                print("prev")
                prev_track()
            elif 360 < y < 460:
                print("next")
                next_track()
        elif 400 > y > 110 and 240 < x < 580:
            if not paused:
                start_time = start_time - 2
                volume = min(dist, 98) + 1
                with open('audio.txt', 'a') as file:
                    file.write('v' + str(int(volume)) + '\n')
    elif current_page == SONG_PAGE:
        if 0 < y < 50:
            if 0 < x < 320:
                current_page = SPEAKER_PAGE
            elif 320 < x < 640:
                current_page = MAIN_PAGE
    elif current_page == FAN_PAGE:
        if 0 < y < 50 and 213 < x < 426:
            current_page = MAIN_PAGE
        elif 50 < y < 160 and 0 < x < 100:
            motor_on = not motor_on
        elif 400 > y > 110 and 240 < x < 580:
            if motor_on:
                start_time = start_time - 2
                speed = min(dist / 10, 15)
                motor_pwm.start(speed)
                print(dist)
                print(speed)
                print("adjusting motor speed")


pipe = None  # Used to send data from CV component to GUI
pos_history = []
paused = True

drawingModule = mediapipe.solutions.drawing_utils
handsModule = mediapipe.solutions.hands
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 5)
not_quit = 1


def main():
    global background
    global frame1
    global start_time
    global not_quit
    start_time = time.time()
    try:
        with handsModule.Hands(static_image_mode=False, min_detection_confidence=0.8, min_tracking_confidence=0.8,
                               max_num_hands=1) as hands:
            while not_quit:
                if GPIO.input(21) == 0:
                    shutdown()
                if current_page == MAIN_PAGE:
                    background = np.zeros((height, width, 3), dtype=np.uint8)
                    draw_home_page(main_tabs)
                elif current_page == TUTORIAL_PAGE:
                    background = np.zeros((height, width, 3), dtype=np.uint8)
                    draw_tutorial_page(tutorial_tabs)
                elif current_page == POWER_PAGE:
                    background = np.zeros((height, width, 3), dtype=np.uint8)
                    draw_power_page(power_tabs)
                elif current_page == BRIGHTNESS_PAGE:
                    background = np.zeros((height, width, 3), dtype=np.uint8)
                    draw_brightness_page(brightness_tabs)
                elif current_page == SPEAKER_PAGE:
                    background = np.zeros((height, width, 3), dtype=np.uint8)
                    draw_speaker_page(speaker_tabs)
                elif current_page == SONG_PAGE:
                    background = np.zeros((height, width, 3), dtype=np.uint8)
                    draw_song_page(song_tabs)
                elif current_page == FAN_PAGE:
                    background = np.zeros((height, width, 3), dtype=np.uint8)
                    draw_fan_page(fan_tabs)

                for event in pygame.event.get():
                    if event.type == pygame.USEREVENT + 1:
                        next_track()

                output = cv(hands)
                if output is not None:
                    cv2.circle(background, output[1], 5, (0, 0, 255), -1)
                    if (time.time() - start_time > 2):
                        handle_mouse_event(
                            output[1][0], output[1][1], output[0])

                # Combine & Display the navigation bar with the camera frame
                combined_frame = cv2.addWeighted(
                    frame1, 0.4, background, 0.6, 0)
                combined_frame = cv2.cvtColor(
                    combined_frame, cv2.COLOR_BGR2RGB)
                img_surface = pygame.surfarray.make_surface(
                    combined_frame.astype(np.uint8))
                rotated_screen = pygame.transform.rotate(img_surface, -90)
                flipped_image = pygame.transform.flip(
                    rotated_screen, True, False)
                screen.blit(flipped_image, (0, 0))
                pygame.display.flip()

                # Break the loop if the 'q' key is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except KeyboardInterrupt:
        clean()
    clean()


def clean():
    global not_quit
    cv2.destroyAllWindows()
    pygame.quit()
    red_pwm.stop()
    yellow_pwm.stop()
    blue_pwm.stop()
    green_pwm.stop()
    cap.release()
    GPIO.output(red_pin, GPIO.LOW)
    GPIO.output(green_pin, GPIO.LOW)
    GPIO.output(blue_pin, GPIO.LOW)
    GPIO.output(yellow_pin, GPIO.LOW)
    GPIO.cleanup()
    not_quit = 0
    with open('audio.txt', 'a') as file:
        file.write('clean\n')


def cv(hands):
    global drawingModule
    global handsModule
    global frame1
    ret, frame = cap.read()

    # Setting Frame
    frame1 = cv2.resize(frame, (640, 480))
    frame1 = cv2.flip(frame1, 1)

    coor = (0, 0)
    t_coor = (0, 0)

    # Making Hand Outline
    results = hands.process(cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB))

    if results.multi_hand_landmarks != None:
        for handLandmarks in results.multi_hand_landmarks:
            drawingModule.draw_landmarks(
                frame1, handLandmarks, handsModule.HAND_CONNECTIONS)

            normalizedLandmark = handLandmarks.landmark[8]
            coor = drawingModule._normalized_to_pixel_coordinates(
                normalizedLandmark.x, normalizedLandmark.y, 640, 480)

            normalizedLandmark = handLandmarks.landmark[4]
            t_coor = drawingModule._normalized_to_pixel_coordinates(
                normalizedLandmark.x, normalizedLandmark.y, 640, 480)
    if coor != (0, 0) and coor != None:
        if t_coor != (0, 0) and t_coor != None:
            dist = math.sqrt((coor[0] - t_coor[0]) ** 2 + (coor[1] - t_coor[1]) ** 2)
            return (dist, (coor))
        else:
            return (0, (coor))
    else:
        return None


if __name__ == '__main__':
    main()
