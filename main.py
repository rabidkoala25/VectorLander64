# need to use async for pages deployment
import pygame 
import asyncio
import math
import random


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLACK = (0,0,0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
AMBER = (255, 255, 0)
FRAMES_PER_SECOND = 120
TURN_SPEED = 120  # degrees per second
GRAVITY = 20.0  # pixels per second per second, pulling down
THRUST = 48.0

START_FUEL = 1000.0
FUEL_PER_SECOND = 70.0



LANDER_PIECES = [
    # hull: up the left side, round the ogive nose, down the right side
    [(-6, 26), (-6, -24), (-6, -28), (-5, -32), (-3, -36), (-1, -38),
     (1, -38), (3, -36), (5, -32), (6, -28), (6, -24), (6, 26), (-6, 26)],
    [(-4, -31), (4, -31), (4, -29), (-4, -29), (-4, -31)],  # crew window band
    [(-2, -31), (-2, -29)],  # window divider
    [(0, -31), (0, -29)],  # window divider
    [(2, -31), (2, -29)],  # window divider
    [(-6, -21), (-8, -20), (-8, -17), (-6, -16)],  # left landing-thruster pod
    [(6, -21), (8, -20), (8, -17), (6, -16)],  # right landing-thruster pod
    [(-6, -14), (6, -14)],  # solar band top
    [(-6, -10), (6, -10)],  # solar band bottom
    [(-3, -14), (-3, -10)],  # solar panel divider
    [(0, -14), (0, -10)],  # solar panel divider
    [(3, -14), (3, -10)],  # solar panel divider
    [(-6, 8), (6, 8)],  # tank seam (common dome between fuel and oxidiser)
    [(-6, 20), (6, 20)],  # aft skirt seam
    [(-4, 26), (-5.5, 30), (-2.5, 30), (-3, 26)],  # left vacuum Raptor bell
    [(-0.5, 26), (-1.5, 29), (1.5, 29), (0.5, 26)],  # centre sea-level Raptor
    [(3, 26), (2.5, 30), (5.5, 30), (4, 26)],  # right vacuum Raptor bell
    [(-6, 20), (-10, 32), (-6, 26)],  # left leg (strut + brace)
    [(-12, 32), (-8, 32)],  # left foot
    [(6, 20), (10, 32), (6, 26)],  # right leg (strut + brace)
    [(8, 32), (12, 32)],  # right foot
]


# draws lines between points
def draw_lander(surface, lander):
    for shape in LANDER_PIECES:
        pygame.draw.lines(surface, GREEN, False, [place_point(point, lander) for point in shape], 2)
    if lander['thrusting']:
        flame_length = random.uniform(5,15)
        flame1 = [(-6, 30), (-5, 30 + flame_length), (0, 30)]
        flame2 = [(0, 30), (5, 30 + flame_length), (6, 30)]
        pygame.draw.lines(surface, AMBER, False, [place_point(point, lander) for point in flame1], 2)
        pygame.draw.lines(surface, AMBER, False, [place_point(point, lander) for point in flame2], 2)

#rotates lander around (0, 0)
def rotate_point(x, y, angle_degrees):
    angle = math.radians(angle_degrees)
    return (
        x * math.cos(angle) - y* math.sin(angle),
        x * math.sin(angle) + y * math.cos(angle),
    )

#places rotated points
def place_point(point, lander):
    turned_x, turned_y = rotate_point(point[0], point[1], lander['angle'])
    return (lander['x'] + turned_x, lander['y'] + turned_y)

def new_lander(fuel):
    return {
        'x': random.uniform(150, SCREEN_WIDTH - 150),
        'y': 60.0,
        'speed_x': random.uniform(-30, 30),
        'speed_y': 0.0,
        'angle': 0.0, #degrees
        'fuel': fuel,
        'thrusting': False,

    }

def update_lander(lander, keys, dt):
    
    if keys[pygame.K_LEFT]:
        lander['angle'] -= TURN_SPEED * dt
    if keys[pygame.K_RIGHT]:
        lander['angle'] += TURN_SPEED * dt

    lander['thrusting'] = keys[pygame.K_UP] and lander['fuel'] > 0
    acceleration_x = 0.0
    acceleration_y = GRAVITY
    if lander['thrusting']:
        
        nose_x, nose_y = rotate_point(0, -1, lander['angle'])
        acceleration_x += nose_x * THRUST
        acceleration_y += nose_y * THRUST
        lander['fuel'] = max(0.0, lander['fuel'] - FUEL_PER_SECOND * dt)

    
    lander['speed_x'] += acceleration_x * dt
    lander['speed_y'] += acceleration_y * dt
    lander['x'] += lander['speed_x'] * dt
    lander['y'] += lander['speed_y'] * dt

    
    lander['x'] %= SCREEN_WIDTH
    lander['y'] %= SCREEN_HEIGHT

    print(lander['fuel'])
    
    

async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('VectorLander64')
    clock = pygame.time.Clock()

    lander = new_lander(1000)
    running = True
    while running: 
        dt = min(clock.tick(FRAMES_PER_SECOND) / 1000, 0.05)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        update_lander(lander, keys, dt)

        screen.fill(BLACK)
        draw_lander(screen, lander)
        pygame.display.flip()
        
        await asyncio.sleep(0)
    pygame.quit()

asyncio.run(main())