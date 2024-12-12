import pygame

# 初始化pygame
pygame.init()

# 创建一个窗口
window = pygame.display.set_mode((400, 300))

# 循环检测按键事件
running = True
while running:
    try:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                # 检测到按键按下事件
                if event.key == pygame.K_UP:
                    # 按下了上箭头键
                    print("Up Arrow Key Pressed")
                elif event.key == pygame.K_DOWN:
                    # 按下了下箭头键
                    print("Down Arrow Key Pressed")
                elif event.key == pygame.K_LEFT:
                    # 按下了左箭头键
                    print("Left Arrow Key Pressed")
                elif event.key == pygame.K_RIGHT:
                    # 按下了右箭头键
                    print("Right Arrow Key Pressed")
                elif event.key == pygame.K_q:
                    # quit
                    print("q Key Pressed")
                    running = False
                elif event.key == pygame.K_ESCAPE:
                    # quit
                    print("esc Key Pressed")
                    running = False

            elif event.type == pygame.KEYUP:
                # 检测到按键释放事件
                if event.key == pygame.K_UP:
                    # 释放了上箭头键
                    print("Up Arrow Key Released")
                elif event.key == pygame.K_DOWN:
                    # 释放了下箭头键
                    print("Down Arrow Key Released")
                elif event.key == pygame.K_LEFT:
                    # 释放了左箭头键
                    print("Left Arrow Key Released")
                elif event.key == pygame.K_RIGHT:
                    # 释放了右箭头键
                    print("Right Arrow Key Released")

            elif event.type == pygame.QUIT:
                # 检测到退出事件
                running = False
    except KeyboardInterrupt:
        running = False

# 退出pygame
pygame.quit()