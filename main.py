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
DIM_GREEN = (0, 200, 0)
AMBER = (255, 255, 0)
FRAMES_PER_SECOND = 120
TURN_SPEED = 120  # degrees per second
GRAVITY = 20.0  # pixels per second per second, pulling down
THRUST = 48.0

START_FUEL = 1000.0
FUEL_PER_SECOND = 70.0

# landing limits: touch down slower and straighter than these, or it is a crash
SAFE_DOWN_SPEED = 25.0  # pixels per second
SAFE_SIDEWAYS_SPEED = 12.0
SAFE_TILT = 10.0  # degrees from upright

TERRAIN_STEP = 40 # terrain resolution
AVERAGE_HEIGHT = 500
HEIGHT_RANGE = 80

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
LEFT_FOOT = (-10, 32)
RIGHT_FOOT = (10, 32)
CONTACT_POINTS = [LEFT_FOOT, RIGHT_FOOT, (-12, 32), (12, 32), (-5.5, 30), (5.5, 30), (-8, -20), (8, -20), (-6, -24), (6, -24), (0, -38)]

def check_touchdown(lander, points, pads):
    touching = False
    for point in CONTACT_POINTS:
        x, y = place_point(point, lander)
        if y >= ground_height_at(points, x):
            touching = True
    if not touching:
        return None

    left_x, _ = place_point(LEFT_FOOT, lander)
    right_x, _ = place_point(RIGHT_FOOT, lander)
    left_pad = pad_under(pads, left_x)
    both_feet_on_one_pad = left_pad is not None and left_pad is pad_under(pads, right_x)
    gentle = lander['speed_y'] <= SAFE_DOWN_SPEED and abs(lander['speed_x']) <= SAFE_SIDEWAYS_SPEED
    upright = tilt_from_upright(lander['angle']) <= SAFE_TILT
    if both_feet_on_one_pad and gentle and upright:
        return ('landed', left_pad)
    return ('crashed', None)

def tilt_from_upright(angle_degrees):
    angle = angle_degrees % 360
    return min(angle, 360 - angle)

def make_terrain():
    point_count = SCREEN_WIDTH // TERRAIN_STEP + 1
    heights = []
    height = random.uniform ((AVERAGE_HEIGHT - HEIGHT_RANGE), (AVERAGE_HEIGHT + HEIGHT_RANGE))
    for index in range(point_count):
        height += random.uniform(-(HEIGHT_RANGE // 2), (HEIGHT_RANGE // 2))
        height = max(330, min(570, height))
        heights.append(height)

        #landing pads
    pad_sizes = [(3, 2), (2, 3), (1, 5)]
    random.shuffle(pad_sizes)
    pads = []
    zone_width = point_count // len(pad_sizes)  # one pad in each third of the screen
    for zone, (steps, multiplier) in enumerate(pad_sizes):
        start = zone * zone_width + random.randint(1, max(1, zone_width - steps - 2))
        pad_height = heights[start]
        for index in range(start, start + steps + 1):
            heights[index] = pad_height  # flatten it
        pads.append({
            'left': start * TERRAIN_STEP,
            'right': (start + steps) * TERRAIN_STEP,
            'height': pad_height,
            'multiplier': multiplier,
        })

    points = [(index * TERRAIN_STEP, heights[index]) for index in range(point_count)]
    return points, pads

def draw_terrain(surface, points, pads, font):
    pygame.draw.lines(surface, GREEN, False, points, 2)
    for pad in pads:
        pygame.draw.line(surface, GREEN, (pad['left'], pad['height']), (pad['right'], pad['height']), 5)
        label = font.render(f"x{pad['multiplier']}", True, GREEN)
        surface.blit(label, ((pad['left'] + pad['right']) / 2 - label.get_width() / 2, pad['height'] + 8))
            
def ground_height_at(points, x):
    """The terrain's screen y at any x, between the points (linear interpolation)."""
    x = max(0, min(SCREEN_WIDTH, x))
    index = min(int(x // TERRAIN_STEP), len(points) - 2)
    left_x, left_height = points[index]
    right_x, right_height = points[index + 1]
    how_far_along = (x - left_x) / (right_x - left_x)
    return left_height + (right_height - left_height) * how_far_along


def pad_under(pads, x):
    """The pad at this x, or None."""
    for pad in pads:
        if pad['left'] <= x <= pad['right']:
            return pad
    return None

# draws lines between points
def draw_lander(surface, lander):
    for shape in LANDER_PIECES:
        pygame.draw.lines(surface, GREEN, False, [place_point(point, lander) for point in shape], 1)
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

# GUI
def draw_text(surface, font, text, centre_x, y, colour=GREEN):
    label = font.render(text, True, colour)
    surface.blit(label, (centre_x - label.get_width() / 2, y))


def draw_hud(surface, font, lander, points, score, high_score):

    altitude = max(0, ground_height_at(points, lander['x']) - lander['y'] -32)

    down_colour = AMBER if lander['speed_y'] > SAFE_DOWN_SPEED else GREEN
    side_colour = AMBER if abs(lander['speed_x']) > SAFE_SIDEWAYS_SPEED else GREEN
    fuel_colour = AMBER if lander['fuel'] < 200 else GREEN

    readings = [
        (f"FUEL {lander['fuel']:04.0f}", fuel_colour),
        (f"ALT {altitude:04.0f}", GREEN),
        (f"VX {lander['speed_x']:05.1f}", side_colour),
        (f"Vy {lander['speed_y']:05.1f}", down_colour),
        (f"SCORE {score:04d}", GREEN),
        (f"HI {high_score:04d}", DIM_GREEN),

    ]
    x = 16
    for text, colour in readings:
        label = font.render(text, True, colour)
        surface.blit(label, (x, 12))
        x+= label.get_width() + 22
    

async def main():
    pygame.init()
    random.seed(1)  # same terrain every run, for testing - delete for the real game
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('VectorLander64')
    clock = pygame.time.Clock()

    small_font = pygame.font.Font(None, 26)
    points, pads = make_terrain()
    lander = new_lander(START_FUEL)
    message = ''  # empty while flying; set when the round ends
    running = True

    big_font = pygame.font.Font(None, 72)
    state = 'title'
    score = 0
    high_score = 0
    while running: 
        dt = min(clock.tick(FRAMES_PER_SECOND) / 1000, 0.05)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # R for testing: new terrain and a new lander
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif state == 'title':
                    state = 'playing'
                    score = 0
                    lander = new_lander(START_FUEL)
                    points, pads = make_terrain()
                elif state in ('landed', 'crashed') and event.key == pygame.K_SPACE:
                    if lander['fuel'] <= 0:
                        state = 'game_over'
                    else:
                        state = 'playing'
                        points, pads = make_terrain()
                        lander = new_lander(lander['fuel'])
                elif state == 'game_over' and event.key == pygame.K_SPACE:
                    state = 'title'

        if state == 'playing':
            update_lander(lander, pygame.key.get_pressed(), dt)
            result = check_touchdown(lander, points, pads)
            if result:
                outcome, pad = result
                lander['thrusting'] = False
                message = 'LANDED' if outcome == 'landed' else 'CRASHED'
                state = outcome  # 'landed' or 'crashed' (step 29 adds the score)

        screen.fill(BLACK)
        draw_terrain(screen, points, pads, small_font)

        if state == 'title':
            draw_text(screen, big_font, 'VECTOR LANDER', SCREEN_WIDTH / 2, 170)
            draw_text(screen, small_font, 'PRESS ANY KEY', SCREEN_WIDTH / 2, 330, AMBER)
        else:
            draw_lander(screen, lander)
            draw_hud(screen, small_font, lander, points, score, high_score)
            if state in ('landed', 'crashed'):
                draw_text(screen, big_font, message, SCREEN_WIDTH / 2, 200, AMBER if state == 'crashed' else GREEN)
                hint = 'OUT OF FUEL  -  PRESS SPACE' if lander['fuel'] <= 0 else 'PRESS SPACE FOR THE NEXT ROUND'
                draw_text(screen, small_font, hint, SCREEN_WIDTH / 2, 260)
            if state == 'game_over':
                draw_text(screen, big_font, 'GAME OVER', SCREEN_WIDTH / 2, 200, AMBER)
                draw_text(screen, small_font, f'SCORE {score:04d}   PRESS SPACE', SCREEN_WIDTH / 2, 260)

        pygame.display.flip()
        await asyncio.sleep(0)
            

        
    pygame.quit()

asyncio.run(main())