import pygame
import time

# 初始化pygame
pygame.init()

# 创建一个窗口
window = pygame.display.set_mode((400, 300))

running = True

try:
    # 循环检测按键事件
    while running:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
                # 其他按键处理省略

            elif event.type == pygame.QUIT:
                running = False

        # 添加适当的时间延迟
        time.sleep(0.01)

except KeyboardInterrupt:
    print("Keyboard Interrupt detected, exiting the program...")

# 退出pygame
pygame.quit()
