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
        # 初始化GPIO
        GPIO.setmode(GPIO.BCM)  # 使用BCM编号方式
        GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 设置GPIO17为输入，启用内部上拉电阻
        GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 设置GPIO22为输入，启用内部上拉电阻
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 设置GPIO23为输入，启用内部上拉电阻
        
        # 初始化Pygame
        pygame.init()
        
        # 设置窗口大小和标题
        self.WINDOW_WIDTH = 1280  # 修改为1280
        self.WINDOW_HEIGHT = 960  # 修改为960
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Gesture Arrow Game")
        
        # 加载箭头图片
        self.arrows = {
            "Up": pygame.image.load(os.path.join("assets", "arrow_up.png")),
            "Down": pygame.image.load(os.path.join("assets", "arrow_down.png")),
            "Left": pygame.image.load(os.path.join("assets", "arrow_left.png")),
            "Right": pygame.image.load(os.path.join("assets", "arrow_right.png"))
        }
        
        # 调整所有箭头图片的大小
        arrow_size = (100, 100)  # 从50x50改为100x100
        for direction in self.arrows:
            self.arrows[direction] = pygame.transform.scale(self.arrows[direction], arrow_size)
        
        # 方向映射
        self.direction_map = {
            0: "Up",
            1: "Down",
            2: "Left",
            3: "Right"
        }
        
        # 箭头状态
        self.current_arrow = None
        self.arrow_pos = [0, 0]
        self.arrow_direction = None
        
        # 判定相关的状态
        self.judging = False
        self.judge_start_time = 0
        self.JUDGE_DURATION = 2
        self.current_score = 0
        
        # 添加字体
        self.font = pygame.font.Font(None, 36)
        
        # 游戏状态
        self.running = True
        self.clock = pygame.time.Clock()
        
        # 摄像头相关设置
        self.gesture_recognition = GestureRecognition()
        self.camera_width = 320  # 增大预览窗口
        self.camera_height = 240
        self.camera_x = self.WINDOW_WIDTH - self.camera_width - 10
        self.camera_y = self.WINDOW_HEIGHT - self.camera_height - 10
        
        # 启动手势识别
        self.gesture_recognition.start()
        
        # 添加连击相关变量
        self.combo = 0
        self.max_combo = 0
        
        # 添加连击显示的动画效果相关变量
        self.combo_display_time = 0
        self.combo_display_duration = 0.5  # 连击数字放大显的持时间
        self.combo_scale = 1.0  # 用于连击数字的缩放效果
        
        # 添加颜色常量
        self.COMBO_COLORS = {
            1: (255, 255, 255),  # 白色
            5: (255, 255, 0),    # 黄色
            10: (255, 165, 0),   # 橙色
            15: (255, 0, 0),     # 红色
            20: (255, 0, 255)    # 紫色
        }
        
        # 修改判定结果相关变量
        self.judge_result = None  # "HIT" 或 "MISS"
        self.judge_display_time = 0
        self.judge_display_duration = 1.0
        self.judge_scale = 1.5
        
        # 添加短暂停顿的时间设置
        self.pause_duration = 0.5  # 0.5秒的停顿
        self.pause_start_time = 0
        self.is_pausing = False
        
        # 修改判定结果的属性
        self.JUDGE_PROPERTIES = {
            "HIT": {
                "color": (0, 255, 0),    # 绿色
                "size": 120,             # 从100改为120
                "scale": 1.5             # 保持1.5
            },
            "MISS": {
                "color": (255, 0, 0),    # 红色
                "size": 120,             # 从100改为120
                "scale": 1.5             # 保持1.5
            }
        }
        
        # 添加标志来记录当前箭头
        self.current_arrow_judged = False
        
        # 添加游戏状态控制
        self.game_state = "TITLE"  # 可能的状态: "TITLE", "RULES", "TUTORIAL", "COUNTDOWN", "PLAYING"
        
        # 添加标题字体
        self.title_font = pygame.font.Font(None, 150)
        self.instruction_font = pygame.font.Font(None, 40)
        
        # 添加教程相关的状态
        self.tutorial_state = 0
        self.tutorial_gestures = ["Up", "Down", "Left", "Right"]
        self.tutorial_completed = False
        self.tutorial_start_time = 0
        self.tutorial_text_alpha = 255
        self.gesture_confirmed = False
        self.gesture_confirm_time = 0
        self.GESTURE_CONFIRM_DURATION = 1.0  # 1秒确认时间
        
        # 添加游戏结束相关变量
        self.miss_count = 0  # 连续MISS计数
        self.MAX_MISS = 3    # 最大允许MISS次数
        self.game_state = "TITLE"  # 添加新状态 "GAME_OVER"
        self.final_score = 0  # 保存最终得分
        
        # 修改速度相关变量
        self.base_speed = 6      # 保持6
        self.current_speed = 6   # 保持6
        self.speed_increment = 2 # 保持2
        self.combo_speed_threshold = 5  # 从10改为5
        
        self.arrow_pos_float = [0.0, 0.0]  # 使用浮点数存储精确位置
        
        # 添加反向模式相关变量
        self.is_reverse_mode = False  # 当前是否是反向模式
        self.reverse_threshold = 10   # 从15改为10
        
        # 加载或创建 REVERSE 提示的字体
        self.reverse_font = pygame.font.Font(None, 80)  # 从120改为80
        self.reverse_color = (0, 255, 255)  # 保持青色 (cyan)

    def generate_new_arrow(self):
        # 随机选择方向（0-3）
        direction_num = random.randint(0, 3)
        self.arrow_direction = self.direction_map[direction_num]
        self.current_arrow = self.arrows[self.arrow_direction]
        
        # 设置箭头初始位置（从屏幕左边开始）
        arrow_width = self.current_arrow.get_width()
        arrow_height = self.current_arrow.get_height()
        
        # 箭头从屏幕左侧开始，垂直位置保持在中央
        self.arrow_pos_float = [
            0.0,  # 从x=0开始
            float((self.WINDOW_HEIGHT - arrow_height) // 2)  # 垂直居中
        ]
        self.arrow_pos = [int(self.arrow_pos_float[0]), int(self.arrow_pos_float[1])]
        self.current_arrow_judged = False  # 新箭头生成时重置判定标志
        
        # 在max_combo>=10时，有50%概率进入反向模式
        if self.max_combo >= self.reverse_threshold:
            self.is_reverse_mode = random.choice([True, False])
        else:
            self.is_reverse_mode = False

    def get_opposite_direction(self, direction):
        # 返回相反的方向
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
            # 根据max_combo计算当前速度（改用max_combo）
            speed_level = self.max_combo // self.combo_speed_threshold
            self.current_speed = self.base_speed + (speed_level * self.speed_increment)
            
            # 使用浮点数进行位置计算
            self.arrow_pos_float[0] += self.current_speed
            self.arrow_pos = [int(self.arrow_pos_float[0]), int(self.arrow_pos_float[1])]
            
            # 如果箭头完全移出屏幕，进行判定并开始短暂停顿
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
            # 在停顿阶段
            current_time = time.time()
            if current_time - self.pause_start_time > self.pause_duration:
                # 停顿结束，生成新箭头
                self.is_pausing = False
                self.current_arrow_judged = False  # 重置判定标志
                self.generate_new_arrow()

    def check_gesture(self):
        # 这个方法现在只用于更手识别，不进行判定
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
            
            # 触发combo动画
            self.combo_display_time = time.time()
            self.combo_scale = 2.0
        else:
            print("Miss!")
            self.combo = 0
            self.miss_count += 1  # 增加MISS计数
            
            # 检查是否游戏结束
            if self.miss_count >= self.MAX_MISS:
                self.game_state = "GAME_OVER"
                self.final_score = self.current_score

    def get_combo_color(self):
        # 根据连击数返回对应的颜色
        color = self.COMBO_COLORS[1]  # 默认白色
        for threshold, c in sorted(self.COMBO_COLORS.items()):
            if self.combo >= threshold:
                color = c
        return color

    def draw_title_screen(self):
        # 使用黑色背景
        self.screen.fill((0, 0, 0))
        
        # 添加标题辉光效果
        glow_size = 2
        for i in range(3):
            glow_text = self.title_font.render("React & Reverse", True, (0, 100 + i*50, 255))
            glow_rect = glow_text.get_rect(center=(
                self.WINDOW_WIDTH//2 + math.sin(time.time()*2) * glow_size * (i+1),
                self.WINDOW_HEIGHT//3 + math.cos(time.time()*2) * glow_size * (i+1)
            ))
            self.screen.blit(glow_text, glow_rect)
        
        # 主标题文本（使用霓虹蓝色）
        title_text = self.title_font.render("React & Reverse", True, (0, 255, 255))
        title_rect = title_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3))
        self.screen.blit(title_text, title_rect)
        
        # 使用与教程界面相同的字体大小和颜色
        small_font = pygame.font.Font(None, 30)
        bright_yellow = (255, 255, 0)
        
        # 使用与教程界面相同的颜色，但字体更大
        title_prompt_font = pygame.font.Font(None, 50)  # 改为50
        bright_yellow = (255, 255, 0)
        
        # 添加开始游戏提示
        start_text = title_prompt_font.render("Press SPACE or GPIO17 to start", True, bright_yellow)
        start_rect = start_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4))
        self.screen.blit(start_text, start_rect)
        
        pygame.display.flip()

    def draw_tutorial_screen(self):
        self.screen.fill((0, 0, 0))
        
        if self.tutorial_state == 0:
            # 显示初始教程提示
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
            
            # 使用鲜艳的黄色 (255, 255, 0)
            bright_yellow = (255, 255, 0)
            
            # 使用更小的字体(30)来显示这些提示
            small_font = pygame.font.Font(None, 30)
            
            # 添加按键和GPIO提示（移除了start提示
            key_prompts = [
                "Press S or GPIO22 to skip tutorial",
                "Press Q or GPIO23 to quit game"
            ]
            
            # 显示所有提示，每行间隔30像素
            for i, prompt in enumerate(key_prompts):
                text = small_font.render(prompt, True, bright_yellow)
                rect = text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4 + i*30))
                self.screen.blit(text, rect)
        
        elif 1 <= self.tutorial_state <= 4:
            current_gesture = self.tutorial_gestures[self.tutorial_state - 1]
            # 将方向提示设置为黄色，其他文本保持白色
            direction_text = self.instruction_font.render(f"Show the {current_gesture} gesture", True, (255, 255, 0))  # 黄色
            instruction_text = self.instruction_font.render("Point your finger in the indicated direction", True, (255, 255, 255))
            
            direction_rect = direction_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3))
            instruction_rect = instruction_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3 + 50))
            
            self.screen.blit(direction_text, direction_rect)
            self.screen.blit(instruction_text, instruction_rect)
            
            # 如果正在确认手势，显示进度或确信息
            if self.gesture_confirmed:
                progress = min(1.0, (time.time() - self.gesture_confirm_time) / self.GESTURE_CONFIRM_DURATION)
                progress_text = self.instruction_font.render(f"Holding: {int(progress * 100)}%", True, (255, 255, 255))
                progress_rect = progress_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3 + 100))
                self.screen.blit(progress_text, progress_rect)
        
        # 显示摄像头画面
        frame = self.gesture_recognition.get_current_frame()
        if frame is not None:
            frame = cv2.resize(frame, (self.camera_width, self.camera_height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (self.camera_x, self.camera_y))
            
            # 显示前检测到的手势
            gesture = self.gesture_recognition.get_current_gesture()
            if gesture:
                # 统一使用 "Gesture: xxx" 格式
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
                    # 一次测到正确手
                    self.gesture_confirmed = True
                    self.gesture_confirm_time = current_time
                elif current_time - self.gesture_confirm_time >= self.GESTURE_CONFIRM_DURATION:
                    # 手势保持了足够长的时间
                    self.tutorial_state += 1
                    self.gesture_confirmed = False
                    if self.tutorial_state > 4:
                        self.start_countdown()
            else:
                # 如果手势不正确，置确认状态
                self.gesture_confirmed = False

    def start_countdown(self):
        self.game_state = "COUNTDOWN"
        self.countdown_start_time = time.time()
        self.countdown_duration = 3  # 3秒倒时

    def draw_countdown(self):
        self.screen.fill((0, 0, 0))
        
        elapsed_time = time.time() - self.countdown_start_time
        count = 3 - int(elapsed_time)
        
        if count > 0:
            # 计算动画效果
            progress = elapsed_time % 1.0  # 每秒的进度(0-1)
            scale = 1.5 + math.sin(progress * math.pi) * 0.3  # 1.2-1.8之间缩放
            
            # 使用更大的基础字号
            base_size = 200  # 增大基字号
            current_size = int(base_size * scale)
            
            # 颜色渐变效果
            color = (
                255,  # R
                int(255 * (1 - progress)),  # G
                int(255 * (1 - progress))   # B
            )
            
            # 创建文本
            countdown_font = pygame.font.Font(None, current_size)
            text = countdown_font.render(str(count), True, color)
        else:
            # "START!"文本的特殊效果
            progress = elapsed_time - 3  # START!显示的时间进度
            if progress < 1:  # 显示1秒
                scale = 1.0 + math.sin(progress * math.pi * 2) * 0.3
                base_size = 180
                current_size = int(base_size * scale)
                
                # 彩虹效果
                hue = (progress * 360) % 360
                color = pygame.Color(0)
                color.hsva = (hue, 100, 100, 100)
                
                countdown_font = pygame.font.Font(None, current_size)
                text = countdown_font.render("START!", True, color)
            else:
                self.game_state = "PLAYING"
                return
        
        # 居中示文本
        text_rect = text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))
        
        # 添加单的发光效果
        for i in range(10, 0, -1):
            size = i * 2
            glow_color = (*color[:3], 25)  # 用相同颜色但透明度较低
            glow_text = countdown_font.render(str(count) if count > 0 else "START!", True, glow_color)
            glow_rect = glow_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))
            glow_rect.inflate_ip(size, size)  # 扩大矩形区域
            self.screen.blit(glow_text, glow_rect)
        
        # 绘制主文本
        self.screen.blit(text, text_rect)
        
        pygame.display.flip()

    def draw_game_over(self):
        self.screen.fill((0, 0, 0))
        
        # 计算动画效果
        time_since_game_over = time.time() - self.judge_display_time
        
        # "GAME OVER" 文本画
        game_over_size = 150
        scale = 1.0 + math.sin(time_since_game_over * 2) * 0.1  # 轻微的缩放果
        current_size = int(game_over_size * scale)
        
        game_over_font = pygame.font.Font(None, current_size)
        game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3))
        
        # 最终得分文本
        score_font = pygame.font.Font(None, 80)
        score_text = score_font.render(f"Final Score: {self.final_score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))
        
        # 最大连击文本
        combo_font = pygame.font.Font(None, 60)
        combo_text = combo_font.render(f"Max Combo: {self.max_combo}", True, (255, 255, 255))
        combo_rect = combo_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2 + 80))
        
        # 使用与教程界面相同的字体大小和颜色
        small_font = pygame.font.Font(None, 30)  # 改为30
        bright_yellow = (255, 255, 0)  # 使用鲜艳的黄色
        
        # 重新开始提示
        restart_text = small_font.render("Press SPACE or GPIO17 to restart", True, bright_yellow)
        restart_rect = restart_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4))
        
        # 添加退出提示
        quit_text = small_font.render("Press Q or GPIO23 to quit game", True, bright_yellow)
        quit_rect = quit_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4 + 40))
        
        # 绘制所有文本
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(combo_text, combo_rect)
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(quit_text, quit_rect)
        
        pygame.display.flip()

    def draw_rules_screen(self):
        self.screen.fill((0, 0, 0))
        
        # 标题
        title_text = self.title_font.render("Game Rules", True, (0, 255, 255))
        title_rect = title_text.get_rect(center=(self.WINDOW_WIDTH//2, 100))
        
        # 规则文本
        rules = [
            "1. Game ends after 3 misses in total",
            "2. Arrow speed increases for every 5 combos",
            "3. When combo > 10, 'REVERSE' appears randomly - make opposite gesture",
            "4. Each correct gesture earns points equal to current combo"
        ]
        
        # 显示规则
        for i, rule in enumerate(rules):
            rule_text = self.instruction_font.render(rule, True, (255, 255, 255))
            rule_rect = rule_text.get_rect(center=(self.WINDOW_WIDTH//2, 250 + i*70))
            self.screen.blit(rule_text, rule_rect)
        
        # 继续提示
        small_font = pygame.font.Font(None, 30)
        bright_yellow = (255, 255, 0)
        
        continue_text = small_font.render("Press SPACE or GPIO17 to continue", True, bright_yellow)
        continue_rect = continue_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4))
        
        quit_text = small_font.render("Press Q or GPIO23 to quit game", True, bright_yellow)
        quit_rect = quit_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT*3//4 + 40))
        
        # 绘制所有文本
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
            # 清空屏幕（填充黑色背景）
            self.screen.fill((0, 0, 0))
            
            # 显示得分和最大连击
            score_text = self.font.render(f"Score: {self.current_score}", True, (255, 255, 255))
            max_combo_text = self.font.render(f"Max Combo: {self.max_combo}", True, (255, 255, 255))
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(max_combo_text, (10, 50))
            
            # 显示当前击数（带动画果）
            if self.combo > 1:
                # 计算动画效果
                time_since_last_combo = time.time() - self.combo_display_time
                if time_since_last_combo < self.combo_display_duration:
                    # 计算缩放效果
                    progress = time_since_last_combo / self.combo_display_duration
                    current_scale = 1.0 + (self.combo_scale - 1.0) * (1.0 - progress)
                    
                    # 使用同大小的字号
                    base_size = 50
                    combo_font = pygame.font.Font(None, int(base_size * current_scale))
                    
                    # 渲染 "Combo: x" 格式的文本
                    combo_text = combo_font.render(f"Combo: {self.combo}", True, self.get_combo_color())
                    combo_rect = combo_text.get_rect(center=(self.WINDOW_WIDTH//2, 150))
                    
                    # 绘制文本
                    self.screen.blit(combo_text, combo_rect)
                else:
                    # 常显示
                    base_size = 50
                    combo_font = pygame.font.Font(None, base_size)
                    combo_text = combo_font.render(f"Combo: {self.combo}", True, self.get_combo_color())
                    combo_rect = combo_text.get_rect(center=(self.WINDOW_WIDTH//2, 150))
                    self.screen.blit(combo_text, combo_rect)
            
            # 如果在判定阶段，显示倒计时
            if self.judging:
                time_left = self.JUDGE_DURATION - (time.time() - self.judge_start_time)
                if time_left > 0:
                    timer_text = self.font.render(f"Time: {time_left:.1f}", True, (255, 255, 255))
                    timer_rect = timer_text.get_rect(center=(self.WINDOW_WIDTH//2, 50))
                    self.screen.blit(timer_text, timer_rect)
                    
                    # 显示提示文本
                    direction_text = self.font.render(f"Show {self.arrow_direction} gesture!", True, (255, 255, 255))
                    direction_rect = direction_text.get_rect(center=(self.WINDOW_WIDTH//2, 100))
                    self.screen.blit(direction_text, direction_rect)
            
            # 果在判阶段，显示箭头
            elif self.current_arrow:
                self.screen.blit(self.current_arrow, self.arrow_pos)
            
            # 获取并显示摄像头画面
            frame = self.gesture_recognition.get_current_frame()
            if frame is not None:
                frame = cv2.resize(frame, (self.camera_width, self.camera_height))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                frame = pygame.surfarray.make_surface(frame)
                self.screen.blit(frame, (self.camera_x, self.camera_y))
                
                # 绘制摄像头画的边框
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),  # 白色边框
                    (self.camera_x, self.camera_y, self.camera_width, self.camera_height),
                    2  # 边度
                )
                
                # 显示当前手势方向（如果有）
                gesture = self.gesture_recognition.get_current_gesture()
                if gesture:
                    font = pygame.font.Font(None, 36)
                    # 直接显示 gesture 值，包括 "None"
                    display_text = f"Gesture: {gesture}"
                    text = font.render(display_text, True, (255, 255, 255))
                    text_rect = text.get_rect()
                    text_rect.x = self.camera_x
                    text_rect.y = self.camera_y - 30
                    self.screen.blit(text, text_rect)
            
            # 绘制判定结果
            current_time = time.time()
            if self.judge_result and current_time - self.judge_display_time < self.judge_display_duration:
                # 算动画效果
                progress = (current_time - self.judge_display_time) / self.judge_display_duration
                
                properties = self.JUDGE_PROPERTIES[self.judge_result]
                base_size = properties["size"]
                max_scale = properties["scale"]
                
                # 不同类型的判定有不的动画效果
                if self.judge_result == "HIT":
                    # 放后缩小带弹性效
                    current_scale = 1.0 + (max_scale - 1.0) * (1.0 - progress) * (1.0 + math.sin(progress * 3.14))
                else:  # MISS
                    # 左右摇晃效果
                    shake = math.sin(progress * 20) * (1.0 - progress) * 20
                    current_scale = 1.0 + (max_scale - 1.0) * (1.0 - progress)
                
                # 创建判定文本
                judge_font = pygame.font.Font(None, int(base_size * current_scale))
                judge_text = judge_font.render(self.judge_result, True, properties["color"])
                judge_rect = judge_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))
                
                # 用摇晃效果（只对MISS生效）
                if self.judge_result == "MISS":
                    judge_rect.x += int(shake)  # 使用 int() 进行显式换
                
                # 设置透明度
                alpha = int(255 * (1.0 - progress))
                judge_text.set_alpha(alpha)
                
                self.screen.blit(judge_text, judge_rect)
            
            # 如果是反向模式，显示 REVERSE 提示
            if self.is_reverse_mode and self.current_arrow:
                reverse_text = self.reverse_font.render("REVERSE!", True, self.reverse_color)
                reverse_rect = reverse_text.get_rect(center=(self.WINDOW_WIDTH//2, 50))
                self.screen.blit(reverse_text, reverse_rect)
            
            # 新显示
            pygame.display.flip()

    def handle_events(self):
        # 检查GPIO按钮状态
        if GPIO.input(17) == GPIO.LOW:  # 按钮被按下时为LOW
            # 模拟空格键的功能
            if self.game_state == "TITLE":
                self.game_state = "RULES"  # 从标题界面进入规则界面
            elif self.game_state == "RULES":
                self.game_state = "TUTORIAL"  # 从规则界面进入教程
                self.tutorial_state = 0
            elif self.game_state == "TUTORIAL" and self.tutorial_state == 0:
                self.tutorial_state = 1
            elif self.game_state == "GAME_OVER":
                # 重置游戏状态
                self.game_state = "COUNTDOWN"
                self.countdown_start_time = time.time()
                self.current_score = 0
                self.combo = 0
                self.max_combo = 0
                self.miss_count = 0
                self.current_arrow = None
            time.sleep(0.2)  # 添加短暂延时防止按钮抖动
        
        if GPIO.input(22) == GPIO.LOW:  # GPIO22 模拟 S 键
            if self.game_state == "TUTORIAL":
                # 跳过教程，直接开始游戏
                self.game_state = "COUNTDOWN"
                self.countdown_start_time = time.time()
            time.sleep(0.2)  # 防抖动延时
        
        if GPIO.input(23) == GPIO.LOW:  # GPIO23 模拟 Q 键
            self.running = False
            time.sleep(0.2)  # 防抖动延时
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    if self.game_state == "TITLE":
                        self.game_state = "RULES"  # 从标题界面进入规则界面
                    elif self.game_state == "RULES":
                        self.game_state = "TUTORIAL"  # 从规则界面进入教程
                        self.tutorial_state = 0
                    elif self.game_state == "TUTORIAL" and self.tutorial_state == 0:
                        self.tutorial_state = 1
                    elif self.game_state == "GAME_OVER":
                        # 重置游戏状态
                        self.game_state = "COUNTDOWN"
                        self.countdown_start_time = time.time()
                        self.current_score = 0
                        self.combo = 0
                        self.max_combo = 0
                        self.miss_count = 0
                        self.current_arrow = None
                elif event.key == pygame.K_s and self.game_state == "TUTORIAL":
                    # 跳过程，直接开始游戏
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
                self.clock.tick(75)  # 改为75Hz以匹配显示刷新率
        finally:
            self.gesture_recognition.stop()
            GPIO.cleanup()
            pygame.quit()

if __name__ == "__main__":
    game = ArrowGame()
    game.run()
