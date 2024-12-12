import pygame
import random
import os
import cv2
import numpy as np
import time
import math
from laptop_index_module import GestureRecognition

class ArrowGame:
    def __init__(self):
        # 初始化Pygame
        pygame.init()
        
        # 设置窗口大小和标题
        self.WINDOW_WIDTH = 800
        self.WINDOW_HEIGHT = 600
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
        arrow_size = (50, 50)  # 可以根据需要调整大小
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
        self.camera_width = 213
        self.camera_height = 160
        self.camera_x = self.WINDOW_WIDTH - self.camera_width - 10
        self.camera_y = self.WINDOW_HEIGHT - self.camera_height - 10
        
        # 启动手势识别
        self.gesture_recognition.start()
        
        # 添加连击相关变量
        self.combo = 0
        self.max_combo = 0
        
        # 添加连击显示的动画效果相关变量
        self.combo_display_time = 0
        self.combo_display_duration = 0.5  # 连击数字放大显示的持时间
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
                "size": 72,              # 较大字号
                "scale": 1.5             # 较大缩放效果
            },
            "MISS": {
                "color": (255, 0, 0),    # 红色
                "size": 64,              # 中等字号
                "scale": 1.3             # 中等缩放效果
            }
        }
        
        # 添加标志来记录当前箭头是否已经被判定过
        self.current_arrow_judged = False

    def generate_new_arrow(self):
        # 随机选择方向（0-3）
        direction_num = random.randint(0, 3)
        self.arrow_direction = self.direction_map[direction_num]
        self.current_arrow = self.arrows[self.arrow_direction]
        
        # 设置箭头初始位置（从屏幕左边开始）
        arrow_width = self.current_arrow.get_width()
        arrow_height = self.current_arrow.get_height()
        
        # 箭头从屏幕中央开始
        self.arrow_pos = [
            (self.WINDOW_WIDTH - arrow_width) // 2,
            (self.WINDOW_HEIGHT - arrow_height) // 2
        ]
        self.current_arrow_judged = False  # 新箭头生成时重置判定标志

    def update_arrow(self):
        if not self.is_pausing:
            # 移动箭头
            self.arrow_pos[0] += 5
            
            # 如果箭头完全移出屏幕，进行判定并开始短暂停顿
            if self.arrow_pos[0] > self.WINDOW_WIDTH:
                self.is_pausing = True
                self.pause_start_time = time.time()
                
                # 获取当前手势进行判定
                gesture = self.gesture_recognition.get_current_gesture()
                if gesture and gesture == self.arrow_direction:
                    print(f"Hit! Combo: {self.combo + 1}")  # 调试信息
                    self.show_judge_result("HIT")
                    self.combo += 1
                    self.max_combo = max(self.max_combo, self.combo)
                    combo_bonus = min(self.combo, 20)
                    score_gain = 1 * combo_bonus
                    self.current_score += score_gain
                else:
                    print("Miss!")  # 调试信息
                    self.show_judge_result("MISS")
                    self.combo = 0
        else:
            # 在停顿阶段
            current_time = time.time()
            if current_time - self.pause_start_time > self.pause_duration:
                # 停顿结束，生成新箭头
                self.is_pausing = False
                self.current_arrow_judged = False  # 重置判定标志
                self.generate_new_arrow()

    def check_gesture(self):
        # 这个方法现在只用于更新手势识别，不进行判定
        pass

    def show_judge_result(self, result):
        self.judge_result = result
        self.judge_display_time = time.time()
        self.judge_scale = self.JUDGE_PROPERTIES[result]["scale"]

    def get_combo_color(self):
        # 根据连击数返回对应的颜色
        color = self.COMBO_COLORS[1]  # 默认白色
        for threshold, c in sorted(self.COMBO_COLORS.items()):
            if self.combo >= threshold:
                color = c
        return color

    def draw(self):
        # 清空屏幕（填充黑色背景）
        self.screen.fill((0, 0, 0))
        
        # 显示得分和最大连击
        score_text = self.font.render(f"Score: {self.current_score}", True, (255, 255, 255))
        max_combo_text = self.font.render(f"Max Combo: {self.max_combo}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(max_combo_text, (10, 50))
        
        # 显示当前连击数（带动画效果）
        if self.combo > 1:
            # 计算动画效果
            time_since_last_combo = time.time() - self.combo_display_time
            if time_since_last_combo < self.combo_display_duration:
                # 计算缩放效果
                progress = time_since_last_combo / self.combo_display_duration
                current_scale = 1.0 + (self.combo_scale - 1.0) * (1.0 - progress)
                
                # 创建放大的连击文本
                combo_font = pygame.font.Font(None, int(36 * current_scale))
                combo_text = combo_font.render(f"Combo: {self.combo}!", True, self.get_combo_color())
                combo_rect = combo_text.get_rect(center=(self.WINDOW_WIDTH//2, 150))
                self.screen.blit(combo_text, combo_rect)
            else:
                # 正常显示连击数
                combo_text = self.font.render(f"Combo: {self.combo}!", True, self.get_combo_color())
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
        
        # 如果不在判定阶段，显示箭头
        elif self.current_arrow:
            self.screen.blit(self.current_arrow, self.arrow_pos)
        
        # 获取并显示摄像头画面
        frame = self.gesture_recognition.get_current_frame()
        if frame is not None:
            # 调整大小
            frame = cv2.resize(frame, (self.camera_width, self.camera_height))
            # OpenCV的BGR格式转换为RGB格式
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 转换为Pygame可以处理的格式
            frame = np.rot90(frame)
            frame = pygame.surfarray.make_surface(frame)
            # 在右下角显示摄像头画面
            self.screen.blit(frame, (self.camera_x, self.camera_y))
            
            # 绘制摄像头画面的边框
            pygame.draw.rect(
                self.screen,
                (255, 255, 255),  # 白色边框
                (self.camera_x, self.camera_y, self.camera_width, self.camera_height),
                2  # 边框宽度
            )
            
            # 显示当前手势方向（如果有）
            gesture = self.gesture_recognition.get_current_gesture()
            if gesture:
                font = pygame.font.Font(None, 36)
                text = font.render(f"Gesture: {gesture}", True, (255, 255, 255))
                text_rect = text.get_rect()
                text_rect.x = self.camera_x
                text_rect.y = self.camera_y - 30
                self.screen.blit(text, text_rect)
        
        # 绘制判定结果
        current_time = time.time()
        if self.judge_result and current_time - self.judge_display_time < self.judge_display_duration:
            # 计算动画效果
            progress = (current_time - self.judge_display_time) / self.judge_display_duration
            
            properties = self.JUDGE_PROPERTIES[self.judge_result]
            base_size = properties["size"]
            max_scale = properties["scale"]
            
            # 不同类型的判定有不同的动画效果
            if self.judge_result == "HIT":
                # 放大后缩小，带弹性效果
                current_scale = 1.0 + (max_scale - 1.0) * (1.0 - progress) * (1.0 + math.sin(progress * 3.14))
            else:  # MISS
                # 左右摇晃效果
                shake = math.sin(progress * 20) * (1.0 - progress) * 20
                current_scale = 1.0 + (max_scale - 1.0) * (1.0 - progress)
            
            # 创建判定文本
            judge_font = pygame.font.Font(None, int(base_size * current_scale))
            judge_text = judge_font.render(self.judge_result, True, properties["color"])
            judge_rect = judge_text.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2))
            
            # 应用摇晃效果（只对MISS生效）
            if self.judge_result == "MISS":
                judge_rect.x += shake
            
            # 设置透明度
            alpha = int(255 * (1.0 - progress))
            judge_text.set_alpha(alpha)
            
            self.screen.blit(judge_text, judge_rect)
        
        # 更新显示
        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False

    def run(self):
        # 生成第一个箭头
        self.generate_new_arrow()
        
        # 主游戏循环
        while self.running:
            self.handle_events()
            self.update_arrow()
            self.check_gesture()
            self.draw()
            self.clock.tick(60)  # 限制帧率为60FPS
        
        # 停止手势识别
        self.gesture_recognition.stop()
        pygame.quit()

if __name__ == "__main__":
    game = ArrowGame()
    game.run()
