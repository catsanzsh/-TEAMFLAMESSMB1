import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 256, 240  # NES resolution
SCALE = 2  # Scale factor for modern displays
SCREEN_WIDTH, SCREEN_HEIGHT = WIDTH * SCALE, HEIGHT * SCALE
FPS = 60

# Colors
BLACK = (0, 0, 0)
RED = (255, 0, 0)  # Mario
BLUE = (0, 0, 255)  # Ground
BROWN = (139, 69, 19)  # Goomba

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario Bros. 1 - Pygame")
clock = pygame.time.Clock()

# Mario properties
mario_x = 50
mario_y = HEIGHT - 32
mario_vel_x = 0
mario_vel_y = 0
gravity = 0.5
jump_strength = -10
on_ground = True

# Camera
camera_x = 0

# Level design (0: empty, 1: ground tile)
TILE_SIZE = 16
level = [
    [0] * 16 for _ in range(14)
] + [[1] * 16]  # Simple flat ground at the bottom

# Enemy class
class Goomba:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_x = -1  # Moves left

    def update(self):
        self.x += self.vel_x

    def draw(self):
        screen_x = self.x - camera_x
        if 0 <= screen_x < WIDTH:
            pygame.draw.rect(screen, BROWN, (screen_x * SCALE, self.y * SCALE, TILE_SIZE * SCALE, TILE_SIZE * SCALE))

# Initial enemies
enemies = [Goomba(100, HEIGHT - 32)]

# Input handling
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

# Drawing functions
def draw_mario(x, y):
    screen_x = x - camera_x
    if 0 <= screen_x < WIDTH:
        pygame.draw.rect(screen, RED, (screen_x * SCALE, y * SCALE, TILE_SIZE * SCALE, TILE_SIZE * SCALE))

def draw_level():
    for y, row in enumerate(level):
        for x, tile in enumerate(row):
            if tile == 1:
                screen_x = x * TILE_SIZE - camera_x
                if 0 <= screen_x < WIDTH:
                    pygame.draw.rect(screen, BLUE, (screen_x * SCALE, y * TILE_SIZE * SCALE, TILE_SIZE * SCALE, TILE_SIZE * SCALE))

# Collision detection
def check_collision(x, y):
    tile_x = int(x // TILE_SIZE)
    tile_y = int(y // TILE_SIZE)
    if 0 <= tile_x < len(level[0]) and 0 <= tile_y < len(level):
        return level[tile_y][tile_x] == 1
    return False

# Camera update
def update_camera():
    global camera_x
    if mario_x > WIDTH / 2:
        camera_x = mario_x - WIDTH / 2

# Game loop
def game_loop():
    global mario_x, mario_y, mario_vel_y, on_ground
    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Handle input
        handle_input()

        # Update Mario's position
        mario_x += mario_vel_x
        mario_y += mario_vel_y
        mario_vel_y += gravity

        # Collision with ground
        if mario_y + TILE_SIZE >= HEIGHT:
            mario_y = HEIGHT - TILE_SIZE
            mario_vel_y = 0
            on_ground = True
        elif check_collision(mario_x, mario_y + TILE_SIZE):
            tile_y = int((mario_y + TILE_SIZE) // TILE_SIZE)
            mario_y = tile_y * TILE_SIZE - TILE_SIZE
            mario_vel_y = 0
            on_ground = True
        else:
            on_ground = False

        # Update enemies
        for enemy in enemies:
            enemy.update()

        # Update camera
        update_camera()

        # Draw everything
        screen.fill(BLACK)
        draw_level()
        draw_mario(mario_x, mario_y)
        for enemy in enemies:
            enemy.draw()

        # Scale and display
        scaled_screen = pygame.transform.scale(screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()
