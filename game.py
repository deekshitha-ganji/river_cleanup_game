import pygame
import sys
import random
import time
import numpy as np
from sklearn.cluster import KMeans

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('River Cleanup Game')

# Define regions
SAND_HEIGHT = HEIGHT // 3
WATER_HEIGHT = HEIGHT - SAND_HEIGHT

# Set up colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Item size
ITEM_SIZE = 50
# Load menu and instruction images
menu_img = pygame.transform.scale(pygame.image.load('menu.png'), (WIDTH, HEIGHT))
instruction_img = pygame.transform.scale(pygame.image.load('instructions.png'), (WIDTH, HEIGHT))

# Load images
boat_img = pygame.image.load('img.png')
boat_img = pygame.transform.scale(boat_img, (70, 70))
boat_rect = boat_img.get_rect(center=(WIDTH // 3, HEIGHT // 3))

# Load images for various plastic items
plastic_images = {
    'water_bottle': pygame.transform.scale(pygame.image.load('wb.png'), (ITEM_SIZE, ITEM_SIZE)),
    'soda_can': pygame.transform.scale(pygame.image.load('soda.png'), (ITEM_SIZE, ITEM_SIZE)),
    'chips_packet': pygame.transform.scale(pygame.image.load('chips.png'), (ITEM_SIZE, ITEM_SIZE)),
    'chocolate_wrapper': pygame.transform.scale(pygame.image.load('wrap.png'), (ITEM_SIZE, ITEM_SIZE)),
    'tube': pygame.transform.scale(pygame.image.load('tube.png'), (ITEM_SIZE, ITEM_SIZE)),
    'plastic_bag': pygame.transform.scale(pygame.image.load('bag.png'), (ITEM_SIZE, ITEM_SIZE))
}

wood_img = pygame.transform.scale(pygame.image.load('wood.png'), (ITEM_SIZE, ITEM_SIZE))
stone_img = pygame.transform.scale(pygame.image.load('stone.png'), (ITEM_SIZE, ITEM_SIZE))

background_img = pygame.transform.scale(pygame.image.load('2.png'), (WIDTH, HEIGHT))

# Load end-of-game images
drowned_img = pygame.transform.scale(pygame.image.load('bd.png'), (WIDTH, HEIGHT))
happy_fishes_img = pygame.transform.scale(pygame.image.load('hf.png'), (WIDTH, HEIGHT))
better_luck_img = pygame.transform.scale(pygame.image.load('blnt1.png'), (WIDTH, HEIGHT))

# Boat movement speed
boat_speed = 3

# Item movement speed
item_speed = 2

# Timer settings
time_limit = 75  # seconds

# Font for displaying time
font = pygame.font.Font(None, 36)

# Number of items
num_plastics = 10
num_woods = 4
num_stones = 4
max_items_on_screen = 8
item_generation_interval = 1.5

# Time for last item generation
last_item_generation_time = 0

LIFE_CIRCLE_RADIUS = 10  # Radius of each life circle
LIFE_CIRCLE_SPACING = 30  # Spacing between circles


# Define game states
MENU = 0
INSTRUCTIONS = 1
GAME = 2

current_state = MENU


def kmeans_cluster_items(n_clusters, num_items):
    x_positions = np.random.uniform(WIDTH // 2, WIDTH, size=(n_clusters, 1))
    y_positions = np.random.uniform(SAND_HEIGHT, HEIGHT, size=(n_clusters, 1))
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=1).fit(np.hstack((x_positions, y_positions)))
    
    items_positions = []
    for cluster_center in kmeans.cluster_centers_:
        for _ in range(num_items // n_clusters):
            offset_x = np.random.randint(-ITEM_SIZE, ITEM_SIZE)
            offset_y = np.random.randint(-ITEM_SIZE, ITEM_SIZE)
            items_positions.append((int(cluster_center[0] + offset_x), int(cluster_center[1] + offset_y)))
    
    return items_positions

def create_clustered_items():
    items = []
    
    plastic_types = list(plastic_images.keys())
    
    plastic_positions = kmeans_cluster_items(n_clusters=3, num_items=num_plastics)
    wood_positions = kmeans_cluster_items(n_clusters=2, num_items=num_woods)
    stone_positions = kmeans_cluster_items(n_clusters=2, num_items=num_stones)
    
    for pos in plastic_positions:
        plastic_type = random.choice(plastic_types)
        items.append((pygame.Rect(pos[0], pos[1], ITEM_SIZE, ITEM_SIZE), plastic_type))
    
    for pos in wood_positions:
        items.append((pygame.Rect(pos[0], pos[1], ITEM_SIZE, ITEM_SIZE), 'wood'))
    
    for pos in stone_positions:
        items.append((pygame.Rect(pos[0], pos[1], ITEM_SIZE, ITEM_SIZE), 'stone'))
    
    return items

def generate_item(type_name, x_position):
    y_position = random.randint(SAND_HEIGHT, HEIGHT - ITEM_SIZE)
    return pygame.Rect(x_position, y_position, ITEM_SIZE, ITEM_SIZE), type_name

def regenerate_items(items):
    global last_item_generation_time
    current_time = time.time()
    
    # Regenerate plastic items
    if len([item for item, type_name in items if type_name in plastic_images]) < num_plastics and current_time - last_item_generation_time > item_generation_interval:
        new_type = random.choice(list(plastic_images.keys()) + ['wood', 'stone'])
        new_item, new_type_name = generate_item(new_type, WIDTH)
        items.append((new_item, new_type_name))
        last_item_generation_time = current_time

    # Regenerate wood and stone items
    while len([item for item, type_name in items if type_name == 'wood']) < num_woods:
        new_item, new_type_name = generate_item('wood', WIDTH)
        items.append((new_item, new_type_name))

    while len([item for item, type_name in items if type_name == 'stone']) < num_stones:
        new_item, new_type_name = generate_item('stone', WIDTH)
        items.append((new_item, new_type_name))

    # Remove items that have gone off-screen
    items[:] = [(item, type_name) for item, type_name in items if item.x + item.width >= 0]

def draw_lives(screen, lives, lives_text_width):
    start_x = 10 + lives_text_width + 20  # 10 pixels padding after the text
    for i in range(lives):
        pygame.draw.circle(screen, RED, (start_x + i * LIFE_CIRCLE_SPACING, 105), LIFE_CIRCLE_RADIUS)



def reset_game():
    global score, lives, items, start_time, last_item_generation_time
    score = 0
    lives = 4
    items = create_clustered_items()
    start_time = time.time()
    last_item_generation_time = time.time()

def game_over():
    global game_running
    print(f'Game Over! Final Score: {score}')
    game_running = False

def display_end_screen():
    if lives <= 0:
        screen.blit(drowned_img, (0, 0))
    elif score >= 20:
        screen.blit(happy_fishes_img, (0, 0))
    else:
        screen.blit(better_luck_img, (0, 0))
    
    # Create a surface for text
    text_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    text_surface.fill((0, 0, 0, 0))  # Transparent background
    
    # Render "Game Over" text and score text
    game_over_text = font.render('Game Over', True, RED)
    score_text = font.render(f'Score: {score}', True, RED)
    
    # Position the text at the bottom
    game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT - 100))
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT - 60))
    
    # Blit text onto the text_surface
    text_surface.blit(game_over_text, game_over_rect)
    text_surface.blit(score_text, score_rect)
    
    # Blit the text_surface onto the screen
    screen.blit(text_surface, (0, 0))
    
    pygame.display.flip()
    pygame.time.wait(3000)  # Display the end screen for 3 seconds

#set frame time
clock = pygame.time.Clock()

# Initialize game state
reset_game()
game_running = True

# Main game loop
# Main game loop
while game_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                if current_state == MENU:
                    current_state = INSTRUCTIONS
                elif current_state == INSTRUCTIONS:
                    current_state = GAME
            elif event.key == pygame.K_SPACE and current_state == GAME:
                for plastic, type_name in items[:]:
                    if type_name in plastic_images:
                        stuck = False
                        for item, item_type in items:
                            if item_type in ['wood', 'stone'] and plastic.colliderect(item):
                                stuck = True
                                break
                        if stuck:
                            items.remove((plastic, type_name))
                            score += 1
                            break

    if current_state == MENU:
        screen.blit(menu_img, (0, 0))
    elif current_state == INSTRUCTIONS:
        screen.blit(instruction_img, (0, 0))
    elif current_state == GAME:
        # Insert your main game logic here
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            boat_rect.y -= boat_speed
        if keys[pygame.K_DOWN]:
            boat_rect.y += boat_speed

        boat_rect.y = max(SAND_HEIGHT, min(boat_rect.y, HEIGHT - boat_rect.height))

        for item, type_name in items:
            item.x -= item_speed

        regenerate_items(items)

        for item, type_name in items[:]:
            if boat_rect.colliderect(item):
                if type_name in plastic_images:
                    score += 1
                    items.remove((item, type_name))
                else:
                    score -= 1
                    lives -= 1
                    items.remove((item, type_name))

        elapsed_time = time.time() - start_time
        remaining_time = max(0, int(time_limit - elapsed_time))

        screen.blit(background_img, (0, 0))
        screen.blit(boat_img, boat_rect)

        for item, type_name in items:
            if type_name in plastic_images:
                screen.blit(plastic_images[type_name], item.topleft)
            elif type_name == 'wood':
                screen.blit(wood_img, item.topleft)
            elif type_name == 'stone':
                screen.blit(stone_img, item.topleft)

        timer_text = font.render(f'Time Left: {remaining_time}', True, RED)
        score_text = font.render(f'Score: {score}', True, RED)
        lives_text = font.render(f'Lives: {lives}', True, RED)
        screen.blit(timer_text, (10, 10))
        screen.blit(score_text, (10, 50))
        lives_text = font.render('Lives:', True, RED)
        screen.blit(lives_text, (10, 90))
        lives_text_width = lives_text.get_width()
        draw_lives(screen, lives, lives_text_width)

        if remaining_time <= 0 or lives <= 0:
            game_over()
            display_end_screen()

    pygame.display.flip()
    clock.tick(30)
