import pygame
import random
import os
import cv2
import numpy as np
import time
import math
import RPi.GPIO as GPIO
from rpi_index_module import GestureRecognition

class ArrowGame:
    def __init__(self):
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)  # Use BCM numbering mode
        GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set GPIO17 as input with pull-up resistor
        GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set GPIO22 as input with pull-up resistor
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set GPIO23 as input with pull-up resistor
        
        # Initialize Pygame
        pygame.init()
        
        # Set window size and title
        self.WINDOW_WIDTH = 1280
        self.WINDOW_HEIGHT = 960
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Gesture Arrow Game")
        
        # Load arrow images
        self.arrows = {
            "Up": pygame.image.load(os.path.join("assets", "arrow_up.png")),
            "Down": pygame.image.load(os.path.join("assets", "arrow_down.png")),
            "Left": pygame.image.load(os.path.join("assets", "arrow_left.png")),
            "Right": pygame.image.load(os.path.join("assets", "arrow_right.png"))
        }
        
        # Resize all arrow images
        arrow_size = (100, 100)
        for direction in self.arrows:
            self.arrows[direction] = pygame.transform.scale(self.arrows[direction], arrow_size)
        
        # Direction mapping
        self.direction_map = {
            0: "Up",
            1: "Down",
            2: "Left",
            3: "Right"
        }
        
        # Arrow state variables
        self.current_arrow = None
        self.arrow_pos = [0, 0]
        self.arrow_direction = None
        
        # Judgment related states
        self.judging = False
        self.judge_start_time = 0
        self.JUDGE_DURATION = 2
        self.current_score = 0
        
        # Add fonts
        self.font = pygame.font.Font(None, 36)
        
        # Game state control
        self.running = True
        self.clock = pygame.time.Clock()
        
        # Camera settings
        self.gesture_recognition = GestureRecognition()
        self.camera_width = 320  # Larger preview window
        self.camera_height = 240
        self.camera_x = self.WINDOW_WIDTH - self.camera_width - 10
        self.camera_y = self.WINDOW_HEIGHT - self.camera_height - 10
        
        # Start gesture recognition
        self.gesture_recognition.start()
        
        # Combo related variables
        self.combo = 0
        self.max_combo = 0
        
        # Combo display animation variables
        self.combo_display_time = 0
        self.combo_display_duration = 0.5  # Duration of combo number scale animation
        self.combo_scale = 1.0  # For combo number scaling effect
        
        # Combo color thresholds
        self.COMBO_COLORS = {
            1: (255, 255, 255),  # White
            5: (255, 255, 0),    # Yellow
            10: (255, 165, 0),   # Orange
            15: (255, 0, 0),     # Red
            20: (255, 0, 255)    # Purple
        }
        
        # Judgment result properties
        self.judge_result = None  # "HIT" or "MISS"
        self.judge_display_time = 0
        self.judge_display_duration = 1.0
        self.judge_scale = 1.5
        
        # Pause duration settings
        self.pause_duration = 0.5  # 0.5 second pause
        self.pause_start_time = 0
        self.is_pausing = False
        
        # Judgment result properties
        self.JUDGE_PROPERTIES = {
            "HIT": {
                "color": (0, 255, 0),    # Green
                "size": 120,
                "scale": 1.5
            },
            "MISS": {
                "color": (255, 0, 0),    # Red
                "size": 120,
                "scale": 1.5
            }
        }
        
        # Flag to track current arrow judgment
        self.current_arrow_judged = False
        
        # Game state control
        self.game_state = "TITLE"  # Possible states: "TITLE", "RULES", "TUTORIAL", "COUNTDOWN", "PLAYING"
        
        # Title and instruction fonts
        self.title_font = pygame.font.Font(None, 150)
        self.instruction_font = pygame.font.Font(None, 40)
        
        # Tutorial related states
        self.tutorial_state = 0
        self.tutorial_gestures = ["Up", "Down", "Left", "Right"]
        self.tutorial_completed = False
        self.tutorial_start_time = 0
        self.tutorial_text_alpha = 255
        self.gesture_confirmed = False
        self.gesture_confirm_time = 0
        self.GESTURE_CONFIRM_DURATION = 1.0  # 1 second confirmation time
        
        # Game over related variables
        self.miss_count = 0  # Miss counter
        self.MAX_MISS = 3    # Maximum allowed misses
        self.final_score = 0  # Store final score
        
        # Speed related variables
        self.base_speed = 6      # Base movement speed
        self.current_speed = 6   # Current movement speed
        self.speed_increment = 2 # Speed increase per threshold
        self.combo_speed_threshold = 5  # Combo threshold for speed increase
        
        # Position variables with floating point precision
        self.arrow_pos_float = [0.0, 0.0]
        
        # Reverse mode variables
        self.is_reverse_mode = False  # Current reverse mode state
        self.reverse_threshold = 10   # Combo threshold for reverse mode
        
        # Reverse mode display font
        self.reverse_font = pygame.font.Font(None, 80)
        self.reverse_color = (0, 255, 255)  # Cyan color for reverse mode

    def generate_new_arrow(self):
        # Randomly select direction (0-3)
        direction_num = random.randint(0, 3)
        self.arrow_direction = self.direction_map[direction_num]
        self.current_arrow = self.arrows[self.arrow_direction]
        
        # Set arrow initial position (start from left side)
        arrow_width = self.current_arrow.get_width()
        arrow_height = self.current_arrow.get_height()
        
        # Arrow starts from left side, vertically centered
        self.arrow_pos_float = [
            0.0,  # Start from x=0
            float((self.WINDOW_HEIGHT - arrow_height) // 2)  # Vertically centered
        ]
        self.arrow_pos = [int(self.arrow_pos_float[0]), int(self.arrow_pos_float[1])]
        self.current_arrow_judged = False  # Reset judgment flag for new arrow
        
        # 50% chance to enter reverse mode when max_combo >= threshold
        if self.max_combo >= self.reverse_threshold:
            self.is_reverse_mode = random.choice([True, False])
        else:
            self.is_reverse_mode = False

    def get_opposite_direction(self, direction):
        # Return opposite direction
        opposites = {
            "Up": "Down",
            "Down": "Up",
            "Left": "Right",
            "Right": "Left",
            "None": "None"
        }
        return opposites.get(direction, direction)

    def update_arrow(self):
        if not self.is_pausing:
            # Calculate current speed based on max_combo
            speed_level = self.max_combo // self.combo_speed_threshold
            self.current_speed = self.base_speed + (speed_level * self.speed_increment)
            
            # Update position using floating point calculation
            self.arrow_pos_float[0] += self.current_speed
            self.arrow_pos = [int(self.arrow_pos_float[0]), int(self.arrow_pos_float[1])]
            
            # If arrow moves off screen, judge and start pause
            if self.arrow_pos[0] > self.WINDOW_WIDTH:
                self.is_pausing = True
                self.pause_start_time = time.time()
                
                gesture = self.gesture_recognition.get_current_gesture()
                if gesture == "None":
                    self.show_judge_result("MISS")
                else:
                    expected_gesture = self.get_opposite_direction(self.arrow_direction) if self.is_reverse_mode else self.arrow_direction
                    if gesture == expected_gesture and not self.current_arrow_judged:
                        self.show_judge_result("HIT")
                        self.current_arrow_judged = True
                    else:
                        self.show_judge_result("MISS")
        else:
            # During pause phase
            current_time = time.time()
            if current_time - self.pause_start_time > self.pause_duration:
                # End pause, generate new arrow
                self.is_pausing = False
                self.current_arrow_judged = False  # Reset judgment flag
                self.generate_new_arrow()

    def check_gesture(self):
        # This method is now only used for gesture recognition, not for judging
        pass

    def show_judge_result(self, result):
        self.judge_result = result
        self.judge_display_time = time.time()
        self.judge_scale = self.JUDGE_PROPERTIES[result]["scale"]
        
        if result == "HIT":
            print(f"Hit! Combo: {self.combo + 1}")
            self.combo += 1
            self.max_combo = max(self.max_combo, self.combo)
            combo_bonus = min(self.combo, 20)
            score_gain = 1 * combo_bonus
            self.current_score += score_gain
            
            # Trigger combo animation
            self.combo_display_time = time.time()
            self.combo_scale = 2.0
        else:
            print("Miss!")
            self.combo = 0
            self.miss_count += 1  # Increment MISS counter
            
            # Check if game is over
            if self.miss_count >= self.MAX_MISS:
                self.game_state = "GAME_OVER"
                self.final_score = self.current_score

    def get_combo_color(self):
        # Return corresponding color based on combo count
        color = self.COMBO_COLORS[1]  # Default white
        for threshold, c in sorted(self.COMBO_COLORS.items()):
            if self.combo >= threshold:
                color = c
        return color

    def draw_title_screen(self):
        # Use black background
        self.screen.fill((0, 0, 0))
        
        # Add glow effect to title
        glow_size = 2
        for i in range(3):
            glow_text = self.title_font.render("React & Reverse", True, (0, 100 + i*50, 255))
            glow_rect = glow_text.get_rect(center=(
                self.WINDOW_WIDTH//2 + math.sin(time.time()*2) * glow_size * (i+1),
                self.WINDOW_HEIGHT//3 + math.cos(time.time()*2) * glow_size * (i+1)
            ))
            self.screen.blit(glow_text, glow_rect)
        
        # Main title text (using neon blue)
        title_text = self.title_font.render("React & Reverse", True, (0, 255, 255))
        title_rect = title_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3))
        self.screen.blit(title_text, title_rect)
        
        # Use same font size and color as tutorial screen
        small_font = pygame.font.Font(None, 30)
        bright_yellow = (255, 255, 0)
        
        # Use same color as tutorial screen but larger font
        title_prompt_font = pygame.font.Font(None, 50)  # Changed to 50
        bright_yellow = (255, 255, 0)
        
        # Add start game prompt
        start_text = title_prompt_font.render("Press SPACE or GPIO17 to start", True, bright_yellow)
        start_rect = start_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4))
        self.screen.blit(start_text, start_rect)
        
        pygame.display.flip()

    def draw_tutorial_screen(self):
        self.screen.fill((0, 0, 0))
        
        if self.tutorial_state == 0:
            # Display initial tutorial prompt
            instruction_text = [
                "Welcome to the Tutorial!",
                "Please raise your hand in front of the camera",
                "Make a fist and extend your index finger",
                "Press SPACE or GPIO17 when you're ready"
            ]
            
            for i, text in enumerate(instruction_text):
                text_surface = self.instruction_font.render(text, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(self.WINDOW_WIDTH//2, 
                                                        self.WINDOW_HEIGHT//3 + i*50))
                self.screen.blit(text_surface, text_rect)
            
            # Use bright yellow (255, 255, 0)
            bright_yellow = (255, 255, 0)
            
            # Use smaller font (30) to display these prompts
            small_font = pygame.font.Font(None, 30)
            
            # Add key prompts (removed start prompt)
            key_prompts = [
                "Press S or GPIO22 to skip tutorial",
                "Press Q or GPIO23 to quit game"
            ]
            
            # Display all prompts, with 30 pixels between each line
            for i, prompt in enumerate(key_prompts):
                text = small_font.render(prompt, True, bright_yellow)
                rect = text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4 + i*30))
                self.screen.blit(text, rect)
        
        elif 1 <= self.tutorial_state <= 4:
            current_gesture = self.tutorial_gestures[self.tutorial_state - 1]
            # Set direction prompt to yellow, other text to white
            direction_text = self.instruction_font.render(f"Show the {current_gesture} gesture", True, (255, 255, 0))  # Yellow
            instruction_text = self.instruction_font.render("Point your finger in the indicated direction", True, (255, 255, 255))
            
            direction_rect = direction_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3))
            instruction_rect = instruction_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3 + 50))
            
            self.screen.blit(direction_text, direction_rect)
            self.screen.blit(instruction_text, instruction_rect)
            
            # If gesture confirmation is in progress, display progress or confirmation
            if self.gesture_confirmed:
                progress = min(1.0, (time.time() - self.gesture_confirm_time) / self.GESTURE_CONFIRM_DURATION)
                progress_text = self.instruction_font.render(f"Holding: {int(progress * 100)}%", True, (255, 255, 255))
                progress_rect = progress_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3 + 100))
                self.screen.blit(progress_text, progress_rect)
        
        # Display camera frame
        frame = self.gesture_recognition.get_current_frame()
        if frame is not None:
            frame = cv2.resize(frame, (self.camera_width, self.camera_height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (self.camera_x, self.camera_y))
            
            # Display current gesture detected
            gesture = self.gesture_recognition.get_current_gesture()
            if gesture:
                # Use "Gesture: xxx" format
                display_text = f"Gesture: {gesture}"
                text = self.instruction_font.render(display_text, True, (0, 255, 0))
                text_rect = text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*2//3))
                self.screen.blit(text, text_rect)
        
        pygame.display.flip()

    def update_tutorial(self):
        if self.tutorial_state >= 1 and self.tutorial_state <= 4:
            current_gesture = self.tutorial_gestures[self.tutorial_state - 1]
            detected_gesture = self.gesture_recognition.get_current_gesture()
            
            current_time = time.time()
            
            if detected_gesture == current_gesture:
                if not self.gesture_confirmed:
                    # One correct gesture detected
                    self.gesture_confirmed = True
                    self.gesture_confirm_time = current_time
                elif current_time - self.gesture_confirm_time >= self.GESTURE_CONFIRM_DURATION:
                    # Gesture held for long enough
                    self.tutorial_state += 1
                    self.gesture_confirmed = False
                    if self.tutorial_state > 4:
                        self.start_countdown()
            else:
                # If gesture is incorrect, reset confirmation state
                self.gesture_confirmed = False

    def start_countdown(self):
        self.game_state = "COUNTDOWN"
        self.countdown_start_time = time.time()
        self.countdown_duration = 3  # 3 seconds countdown

    def draw_countdown(self):
        self.screen.fill((0, 0, 0))
        
        elapsed_time = time.time() - self.countdown_start_time
        count = 3 - int(elapsed_time)
        
        if count > 0:
            # Animation effect calculation
            progress = elapsed_time % 1.0  # Progress per second (0-1)
            scale = 1.5 + math.sin(progress * math.pi) * 0.3  # Scale between 1.2-1.8
            
            # Use larger base font size
            base_size = 200
            current_size = int(base_size * scale)
            
            # Color gradient effect
            color = (
                255,  # R
                int(255 * (1 - progress)),  # G
                int(255 * (1 - progress))   # B
            )
            
            # Create countdown text
            countdown_font = pygame.font.Font(None, current_size)
            text = countdown_font.render(str(count), True, color)
        else:
            # "START!" text special effects
            progress = elapsed_time - 3  # START! display time progress
            if progress < 1:  # Display for 1 second
                scale = 1.0 + math.sin(progress * math.pi * 2) * 0.3
                base_size = 180
                current_size = int(base_size * scale)
                
                # Rainbow color effect
                hue = (progress * 360) % 360
                color = pygame.Color(0)
                color.hsva = (hue, 100, 100, 100)
                
                countdown_font = pygame.font.Font(None, current_size)
                text = countdown_font.render("START!", True, color)
            else:
                self.game_state = "PLAYING"
                return
        
        # Center text on screen
        text_rect = text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))
        
        # Add glow effect
        for i in range(10, 0, -1):
            size = i * 2
            glow_color = (*color[:3], 25)  # Same color with lower alpha
            glow_text = countdown_font.render(str(count) if count > 0 else "START!", True, glow_color)
            glow_rect = glow_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))
            glow_rect.inflate_ip(size, size)  # Expand rectangle for glow effect
            self.screen.blit(glow_text, glow_rect)
        
        # Draw main text
        self.screen.blit(text, text_rect)
        
        pygame.display.flip()

    def draw_game_over(self):
        self.screen.fill((0, 0, 0))  # Black background
        
        # Calculate animation timing
        time_since_game_over = time.time() - self.judge_display_time
        
        # "GAME OVER" text with animation
        game_over_size = 150
        scale = 1.0 + math.sin(time_since_game_over * 2) * 0.1  # Gentle pulsing effect
        current_size = int(game_over_size * scale)
        
        # Render game over text in red
        game_over_font = pygame.font.Font(None, current_size)
        game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3))
        
        # Display final score
        score_font = pygame.font.Font(None, 80)
        score_text = score_font.render(f"Final Score: {self.final_score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))
        
        # Display max combo achieved
        combo_font = pygame.font.Font(None, 60)
        combo_text = combo_font.render(f"Max Combo: {self.max_combo}", True, (255, 255, 255))
        combo_rect = combo_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2 + 80))
        
        # Use consistent font style for prompts
        small_font = pygame.font.Font(None, 30)
        bright_yellow = (255, 255, 0)
        
        # Restart and quit prompts
        restart_text = small_font.render("Press SPACE or GPIO17 to restart", True, bright_yellow)
        restart_rect = restart_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4))
        
        quit_text = small_font.render("Press Q or GPIO23 to quit game", True, bright_yellow)
        quit_rect = quit_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4 + 40))
        
        # Draw all elements
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(combo_text, combo_rect)
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(quit_text, quit_rect)
        
        pygame.display.flip()  # Update display

    def draw_rules_screen(self):
        self.screen.fill((0, 0, 0))
        
        # Title
        title_text = self.title_font.render("Game Rules", True, (0, 255, 255))
        title_rect = title_text.get_rect(center=(self.WINDOW_WIDTH//2, 100))
        
        # Rules text
        rules = [
            "1. Game ends after 3 misses in total",
            "2. Arrow speed increases for every 5 combos",
            "3. When combo > 10, 'REVERSE' appears randomly - make opposite gesture",
            "4. Each correct gesture earns points equal to current combo"
        ]
        
        # Display rules
        for i, rule in enumerate(rules):
            rule_text = self.instruction_font.render(rule, True, (255, 255, 255))
            rule_rect = rule_text.get_rect(center=(self.WINDOW_WIDTH//2, 250 + i*70))
            self.screen.blit(rule_text, rule_rect)
        
        # Continue prompt
        small_font = pygame.font.Font(None, 30)
        bright_yellow = (255, 255, 0)
        
        continue_text = small_font.render("Press SPACE or GPIO17 to continue", True, bright_yellow)
        continue_rect = continue_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4))
        
        quit_text = small_font.render("Press Q or GPIO23 to quit game", True, bright_yellow)
        quit_rect = quit_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4 + 40))
        
        # Draw all text
        self.screen.blit(title_text, title_rect)
        self.screen.blit(continue_text, continue_rect)
        self.screen.blit(quit_text, quit_rect)
        
        pygame.display.flip()

    def draw(self):
        if self.game_state == "TITLE":
            self.draw_title_screen()
        elif self.game_state == "RULES":
            self.draw_rules_screen()
        elif self.game_state == "TUTORIAL":
            self.draw_tutorial_screen()
        elif self.game_state == "COUNTDOWN":
            self.draw_countdown()
        elif self.game_state == "GAME_OVER":
            self.draw_game_over()
        else:
            # Clear screen with black background
            self.screen.fill((0, 0, 0))
            
            # Display score and max combo in top left
            score_text = self.font.render(f"Score: {self.current_score}", True, (255, 255, 255))
            max_combo_text = self.font.render(f"Max Combo: {self.max_combo}", True, (255, 255, 255))
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(max_combo_text, (10, 50))
            
            # Display current combo with animation effect
            if self.combo > 1:
                # Calculate animation timing
                time_since_last_combo = time.time() - self.combo_display_time
                if time_since_last_combo < self.combo_display_duration:
                    # Calculate scale animation
                    progress = time_since_last_combo / self.combo_display_duration
                    current_scale = 1.0 + (self.combo_scale - 1.0) * (1.0 - progress)
                    
                    # Set font size and render combo text
                    base_size = 50
                    combo_font = pygame.font.Font(None, int(base_size * current_scale))
                    combo_text = combo_font.render(f"Combo: {self.combo}", True, self.get_combo_color())
                    combo_rect = combo_text.get_rect(center=(self.WINDOW_WIDTH//2, 150))
                    self.screen.blit(combo_text, combo_rect)
            
            # If in judging phase, display countdown
            if self.judging:
                time_left = self.JUDGE_DURATION - (time.time() - self.judge_start_time)
                if time_left > 0:
                    timer_text = self.font.render(f"Time: {time_left:.1f}", True, (255, 255, 255))
                    timer_rect = timer_text.get_rect(center=(self.WINDOW_WIDTH//2, 50))
                    self.screen.blit(timer_text, timer_rect)
                    
                    # Display prompt text
                    direction_text = self.font.render(f"Show {self.arrow_direction} gesture!", True, (255, 255, 255))
                    direction_rect = direction_text.get_rect(center=(self.WINDOW_WIDTH//2, 100))
                    self.screen.blit(direction_text, direction_rect)
            
            # If in judging phase, display arrow
            elif self.current_arrow:
                self.screen.blit(self.current_arrow, self.arrow_pos)
            
            # Get and display camera frame
            frame = self.gesture_recognition.get_current_frame()
            if frame is not None:
                frame = cv2.resize(frame, (self.camera_width, self.camera_height))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                frame = pygame.surfarray.make_surface(frame)
                self.screen.blit(frame, (self.camera_x, self.camera_y))
                
                # Draw camera frame border
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),  # White border
                    (self.camera_x, self.camera_y, self.camera_width, self.camera_height),
                    2  # Border width
                )
                
                # Display current gesture direction (if any)
                gesture = self.gesture_recognition.get_current_gesture()
                if gesture:
                    font = pygame.font.Font(None, 36)
                    # Display gesture value directly, including "None"
                    display_text = f"Gesture: {gesture}"
                    text = font.render(display_text, True, (255, 255, 255))
                    text_rect = text.get_rect()
                    text_rect.x = self.camera_x
                    text_rect.y = self.camera_y - 30
                    self.screen.blit(text, text_rect)
            
            # Draw judgment result
            current_time = time.time()
            if self.judge_result and current_time - self.judge_display_time < self.judge_display_duration:
                # Calculate animation effect
                progress = (current_time - self.judge_display_time) / self.judge_display_duration
                
                properties = self.JUDGE_PROPERTIES[self.judge_result]
                base_size = properties["size"]
                max_scale = properties["scale"]
                
                # Different types of judgment have different animation effects
                if self.judge_result == "HIT":
                    # Expand and shrink with elastic effect
                    current_scale = 1.0 + (max_scale - 1.0) * (1.0 - progress) * (1.0 + math.sin(progress * 3.14))
                else:  # MISS
                    # Shake effect
                    shake = math.sin(progress * 20) * (1.0 - progress) * 20
                    current_scale = 1.0 + (max_scale - 1.0) * (1.0 - progress)
                
                # Create judgment text
                judge_font = pygame.font.Font(None, int(base_size * current_scale))
                judge_text = judge_font.render(self.judge_result, True, properties["color"])
                judge_rect = judge_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))
                
                # Use shake effect (only for MISS)
                if self.judge_result == "MISS":
                    judge_rect.x += int(shake)  # Explicitly convert to int for display
                
                # Set transparency
                alpha = int(255 * (1.0 - progress))
                judge_text.set_alpha(alpha)
                
                self.screen.blit(judge_text, judge_rect)
            
            # If in reverse mode, display REVERSE prompt
            if self.is_reverse_mode and self.current_arrow:
                reverse_text = self.reverse_font.render("REVERSE!", True, self.reverse_color)
                reverse_rect = reverse_text.get_rect(center=(self.WINDOW_WIDTH//2, 50))
                self.screen.blit(reverse_text, reverse_rect)
            
            # New display
            pygame.display.flip()

    def handle_events(self):
        # Check GPIO button state
        if GPIO.input(17) == GPIO.LOW:  # LOW when button is pressed
            # Simulate space bar functionality
            if self.game_state == "TITLE":
                self.game_state = "RULES"  # Move to rules screen
            elif self.game_state == "RULES":
                self.game_state = "TUTORIAL"  # Move to tutorial
                self.tutorial_state = 0
            elif self.game_state == "TUTORIAL" and self.tutorial_state == 0:
                self.tutorial_state = 1
            elif self.game_state == "GAME_OVER":
                # Reset game state
                self.game_state = "COUNTDOWN"
                self.countdown_start_time = time.time()
                self.current_score = 0
                self.combo = 0
                self.max_combo = 0
                self.miss_count = 0
                self.current_arrow = None
            time.sleep(0.2)  # Add short delay to prevent button bounce
        
        if GPIO.input(22) == GPIO.LOW:  # GPIO22 simulate S key
            if self.game_state == "TUTORIAL":
                # Skip tutorial, start game directly
                self.game_state = "COUNTDOWN"
                self.countdown_start_time = time.time()
            time.sleep(0.2)  # Delay to prevent button bounce
        
        if GPIO.input(23) == GPIO.LOW:  # GPIO23 simulate Q key
            self.running = False
            time.sleep(0.2)  # Delay to prevent button bounce
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    if self.game_state == "TITLE":
                        self.game_state = "RULES"  # Move to rules screen
                    elif self.game_state == "RULES":
                        self.game_state = "TUTORIAL"  # Move to tutorial
                        self.tutorial_state = 0
                    elif self.game_state == "TUTORIAL" and self.tutorial_state == 0:
                        self.tutorial_state = 1
                    elif self.game_state == "GAME_OVER":
                        # Reset game state
                        self.game_state = "COUNTDOWN"
                        self.countdown_start_time = time.time()
                        self.current_score = 0
                        self.combo = 0
                        self.max_combo = 0
                        self.miss_count = 0
                        self.current_arrow = None
                elif event.key == pygame.K_s and self.game_state == "TUTORIAL":
                    # Skip tutorial, start game directly
                    self.game_state = "COUNTDOWN"
                    self.countdown_start_time = time.time()

    def run(self):
        try:
            while self.running:
                self.handle_events()
                if self.game_state == "PLAYING":
                    if self.current_arrow is None:
                        self.generate_new_arrow()
                    self.update_arrow()
                    self.check_gesture()
                elif self.game_state == "TUTORIAL":
                    self.update_tutorial()
                elif self.game_state == "COUNTDOWN":
                    self.draw_countdown()
                self.draw()
                self.clock.tick(75)  # Changed to 75Hz to match display refresh rate
        finally:
            self.gesture_recognition.stop()
            GPIO.cleanup()
            pygame.quit()

if __name__ == "__main__":
    game = ArrowGame()
    game.run()
