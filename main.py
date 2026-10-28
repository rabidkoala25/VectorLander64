# need to use async for pages deployment
import pygame 
import asyncio

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLACK = (0,0,0)
WHITE = (255, 255, 255)
FRAMES_PER_SECOND = 120
clock = pygame.time.Clock()
async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('VectorLander64')
    clock = pygame.time.Clock()

    running = True
    while running: 
        dt = min(clock.tick(FRAMES_PER_SECOND) / 1000, 0.05)
        print(dt)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BLACK)
        pygame.display.flip()
        await asyncio.sleep(0)
    pygame.quit()

asyncio.run(main())