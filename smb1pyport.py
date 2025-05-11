import asyncio
import platform
import pygame

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 256, 240  # NES resolution
SCALE = 2
SCREEN_WIDTH, SCREEN_HEIGHT = WIDTH * SCALE, HEIGHT * SCALE
FPS = 60
TILE_SIZE = 16

# Colors
# NES Palette (NTSC, from ROM Detectives Wiki)
# Each color is an (R, G, B) tuple
NES_PALETTE = [
    (124, 124, 124), (0, 0, 252), (0, 0, 188), (68, 40, 188), (148, 0, 132), (168, 0, 32), (168, 16, 0), (136, 20, 0),
    (80, 48, 0), (0, 120, 0), (0, 104, 0), (0, 88, 0), (0, 64, 88), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (188, 188, 188), (0, 120, 248), (0, 88, 248), (104, 68, 252), (216, 0, 204), (228, 0, 88), (248, 56, 0), (228, 92, 16),
    (172, 124, 0), (0, 184, 0), (0, 168, 0), (0, 168, 68), (0, 136, 136), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (248, 248, 248), (60, 188, 252), (104, 136, 252), (152, 120, 248), (248, 120, 248), (248, 88, 152), (248, 120, 88), (252, 160, 68),
    (248, 184, 0), (184, 248, 24), (88, 216, 84), (88, 248, 152), (0, 232, 216), (120, 120, 120), (0, 0, 0), (0, 0, 0),
    (252, 252, 252), (164, 228, 252), (184, 184, 248), (216, 184, 248), (248, 184, 248), (248, 164, 192), (240, 208, 176), (252, 224, 168),
    (248, 216, 120), (216, 248, 120), (184, 248, 184), (184, 248, 216), (0, 252, 252), (248, 216, 248), (0, 0, 0), (0, 0, 0)
]

# Mapping game colors to NES palette indices (approximate choices)
NES_BLACK = NES_PALETTE[0x0F] # True black
NES_MARIO_RED = NES_PALETTE[0x16] # A good red for Mario
NES_GROUND_BLUE = NES_PALETTE[0x12] # A dark blue for ground/bricks
NES_GOOMBA_BROWN = NES_PALETTE[0x07] # Darker brown for Goomba
NES_ITEM_YELLOW = NES_PALETTE[0x28] # Bright yellow for ? blocks and coins
NES_PIPE_GREEN = NES_PALETTE[0x1A] # A green for pipes
NES_EMPTY_BLOCK_GRAY = NES_PALETTE[0x00] # Dark gray for used blocks
NES_SKY_BLUE = NES_PALETTE[0x31] # A light blue for sky (used as background)
NES_WHITE = NES_PALETTE[0x30] # Brightest white

BLACK = NES_BLACK
RED = NES_MARIO_RED
BLUE = NES_GROUND_BLUE
BROWN = NES_GOOMBA_BROWN
YELLOW = NES_ITEM_YELLOW
GREEN = NES_PIPE_GREEN
GRAY = NES_EMPTY_BLOCK_GRAY
WHITE = NES_WHITE

# Tile colors dictionary
TILE_COLORS = {
    0: BLACK,      # Empty
    1: BLUE,       # Ground
    2: GRAY,       # Empty block
    3: YELLOW,     # Question block
    4: GREEN,      # Pipe
    5: YELLOW      # Coin
}

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario Bros. Expanded - Pygame")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Game variables
mario_x = 50
mario_y = HEIGHT - TILE_SIZE
mario_vel_x = 0
mario_vel_y = 0
gravity = 0.5
jump_strength = -10
on_ground = True
camera_x = 0
score = 0

# Level design (100 tiles wide, 15 tiles high)
level = [[0] * 100 for _ in range(15)]
# Ground layer
level[14] = [1] * 100
# Platform at y=10, x=20-29
for x in range(20, 30):
    level[10][x] = 1
# Question block and coin
level[8][25] = 3    # Question block
level[7][25] = 5    # Coin above it
# Pit at x=40-49
for x in range(40, 50):
    level[14][x] = 0
# Additional platform at y=8, x=60-70
for x in range(60, 70):
    level[8][x] = 1

# Enemy class
class Goomba:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_x = -1
        self.vel_y = 0
        self.on_ground = False

    def update(self):
        # Apply gravity and movement
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += gravity

        # Vertical collision with solid tiles
        potential_y = self.y + self.vel_y
        enemy_rect = pygame.Rect(self.x, potential_y, TILE_SIZE, TILE_SIZE)
        colliding_tiles = [tile for tile in get_overlapping_tiles(self.x, potential_y) if level[tile[1]][tile[0]] in [1, 2, 3, 4]]
        if colliding_tiles and self.vel_y > 0:
            topmost_tile_y = min(tile[1] for tile in colliding_tiles)
            self.y = topmost_tile_y * TILE_SIZE - TILE_SIZE
            self.vel_y = 0
            self.on_ground = True
        else:
            self.y = potential_y
            self.on_ground = False

        # Turn around at edges
        if self.on_ground:
            tile_x_left = int((self.x - 1) // TILE_SIZE)
            tile_x_right = int((self.x + TILE_SIZE) // TILE_SIZE)
            tile_y_below = int((self.y + TILE_SIZE) // TILE_SIZE) + 1
            if tile_y_below < len(level):
                if self.vel_x < 0 and tile_x_left >= 0 and level[tile_y_below][tile_x_left] == 0:
                    self.vel_x = 1
                elif self.vel_x > 0 and tile_x_right < len(level[0]) and level[tile_y_below][tile_x_right] == 0:
                    self.vel_x = -1

    def draw(self):
        screen_x = self.x - camera_x
        if 0 <= screen_x < WIDTH:
            pygame.draw.rect(screen, BROWN, (screen_x * SCALE, self.y * SCALE, TILE_SIZE * SCALE, TILE_SIZE * SCALE))

# Initial enemies
enemies = [Goomba(100, HEIGHT - TILE_SIZE), Goomba(150, HEIGHT - TILE_SIZE), Goomba(200, HEIGHT - TILE_SIZE)]

# Helper functions
def get_overlapping_tiles(x, y):
    tiles = []
    min_tile_x = int(x // TILE_SIZE)
    max_tile_x = int((x + TILE_SIZE - 1) // TILE_SIZE)
    min_tile_y = int(y // TILE_SIZE)
    max_tile_y = int((y + TILE_SIZE - 1) // TILE_SIZE)
    for ty in range(min_tile_y, max_tile_y + 1):
        for tx in range(min_tile_x, max_tile_x + 1):
            if 0 <= tx < len(level[0]) and 0 <= ty < len(level):
                tiles.append((tx, ty))
    return tiles

def handle_input():
    global mario_vel_x, mario_vel_y, on_ground
    keys = pygame.key.get_pressed()
    mario_vel_x = 0
    if keys[pygame.K_LEFT]:
        mario_vel_x = -2
    if keys[pygame.K_RIGHT]:
        mario_vel_x = 2
    if keys[pygame.K_SPACE] and on_ground:
        mario_vel_y = jump_strength
        on_ground = False

def update_camera():
    global camera_x
    camera_x = max(0, min(mario_x - WIDTH / 2, len(level[0]) * TILE_SIZE - WIDTH))

def draw_level():
    start_x = int(camera_x // TILE_SIZE)
    end_x = min(start_x + int(WIDTH / TILE_SIZE) + 1, len(level[0]))
    for y in range(len(level)):
        for x in range(start_x, end_x):
            tile = level[y][x]
            if tile in TILE_COLORS:
                screen_x = (x * TILE_SIZE - camera_x) * SCALE
                pygame.draw.rect(screen, TILE_COLORS[tile], (screen_x, y * TILE_SIZE * SCALE, TILE_SIZE * SCALE, TILE_SIZE * SCALE))

def draw_mario():
    screen_x = mario_x - camera_x
    if 0 <= screen_x < WIDTH:
        pygame.draw.rect(screen, RED, (screen_x * SCALE, mario_y * SCALE, TILE_SIZE * SCALE, TILE_SIZE * SCALE))

def mario_die():
    global mario_x, mario_y, mario_vel_x, mario_vel_y, on_ground
    mario_x = 50
    mario_y = HEIGHT - TILE_SIZE
    mario_vel_x = 0
    mario_vel_y = 0
    on_ground = True

# Setup function
def setup():
    pass  # All initialization is done above for simplicity

# Update loop
def update_loop():
    global mario_x, mario_y, mario_vel_y, on_ground, score

    # Handle input
    handle_input()

    # Horizontal movement and collision
    potential_x = mario_x + mario_vel_x
    mario_rect = pygame.Rect(potential_x, mario_y, TILE_SIZE, TILE_SIZE)
    colliding_tiles = [tile for tile in get_overlapping_tiles(potential_x, mario_y) if level[tile[1]][tile[0]] in [1, 2, 3, 4]]
    if colliding_tiles:
        if mario_vel_x > 0:
            mario_x = min(tile[0] for tile in colliding_tiles) * TILE_SIZE - TILE_SIZE
        elif mario_vel_x < 0:
            mario_x = (max(tile[0] for tile in colliding_tiles) + 1) * TILE_SIZE
    else:
        mario_x = potential_x

    # Vertical movement and collision
    potential_y = mario_y + mario_vel_y
    mario_rect = pygame.Rect(mario_x, potential_y, TILE_SIZE, TILE_SIZE)
    colliding_tiles = [tile for tile in get_overlapping_tiles(mario_x, potential_y) if level[tile[1]][tile[0]] in [1, 2, 3, 4]]
    if colliding_tiles:
        if mario_vel_y > 0:
            topmost_tile_y = min(tile[1] for tile in colliding_tiles)
            mario_y = topmost_tile_y * TILE_SIZE - TILE_SIZE
            mario_vel_y = 0
            on_ground = True
        elif mario_vel_y < 0:
            bottommost_tile_y = max(tile[1] for tile in colliding_tiles)
            mario_y = (bottommost_tile_y + 1) * TILE_SIZE
            mario_vel_y = 0
            # Check for question block activation
            for tx, ty in colliding_tiles:
                if level[ty][tx] == 3:
                    level[ty][tx] = 2  # Change to empty block
                    score += 100
    else:
        mario_y = potential_y
        on_ground = False

    # Apply gravity
    mario_vel_y += gravity

    # Check for pit death
    if mario_y > HEIGHT:
        mario_die()

    # Update enemies
    for enemy in enemies[:]:
        enemy.update()

    # Enemy collision with Mario
    mario_rect = pygame.Rect(mario_x, mario_y, TILE_SIZE, TILE_SIZE)
    for enemy in enemies[:]:
        enemy_rect = pygame.Rect(enemy.x, enemy.y, TILE_SIZE, TILE_SIZE)
        if mario_rect.colliderect(enemy_rect):
            if mario_vel_y > 0 and mario_rect.bottom <= enemy_rect.top + 5:
                enemies.remove(enemy)
                score += 100
                mario_vel_y = jump_strength / 2
            else:
                mario_die()

    # Check for level completion
    if mario_x >= (len(level[0]) - 1) * TILE_SIZE:
        print("Level Complete")
        return False  # End the game

    # Update camera
    update_camera()

    # Draw everything
    screen.fill(NES_SKY_BLUE) # Changed from BLACK to a sky blue color
    draw_level()
    draw_mario()
    for enemy in enemies:
        enemy.draw()

    # Draw score
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Scale and display
    pygame.display.flip()
    return True

# Main async game loop
async def main():
    setup()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        running = update_loop()
        await asyncio.sleep(1.0 / FPS)

# Run the game
if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
