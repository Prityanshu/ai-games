import pygame
import random
from collections import deque

# Constants for the game grid
GRID_SIZE = 10  # 12x12 grid
TILE_SIZE = 80  # Tile size
WIDTH, HEIGHT = GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
BUTTON_HEIGHT = 50
TEXT_INPUT_HEIGHT = 40
WELCOME_HEIGHT = HEIGHT - 20  + 3 * BUTTON_HEIGHT + 2 * TEXT_INPUT_HEIGHT 

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
LIGHT_BLUE = (173, 216, 230)

# Entities
AGENT = "A"
WUMPUS = "W"
GOLD = "G"
PIT = "P"
EMPTY = "_"

# Initialize Pygame
pygame.init()
pygame.font.init()
font = pygame.font.SysFont('Arial', 24)
small_font = pygame.font.SysFont('Arial', 18)

# Game states
WELCOME_SCREEN = 0
GAME_RUNNING = 1

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = (min(color[0] + 30, 255), min(color[1] + 30, 255), min(color[2] + 30, 255))
        self.active_color = color
        
    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(surface, self.hover_color, self.rect)
        else:
            pygame.draw.rect(surface, self.active_color, self.rect)
        
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class TextInput:
    def __init__(self, x, y, width, height, label="", default_text=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = default_text
        self.label = label
        self.active = False
        self.label_surface = font.render(label, True, BLACK)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            else:
                # Only allow numbers and commas
                if event.unicode.isdigit() or event.unicode == ',':
                    self.text += event.unicode
    
    def draw(self, surface):
        # Draw label
        label_rect = self.label_surface.get_rect(bottomleft=(self.rect.x, self.rect.y - 5))
        surface.blit(self.label_surface, label_rect)
        
        # Draw text box
        color = LIGHT_BLUE if self.active else WHITE
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        # Draw text
        text_surface = font.render(self.text, True, BLACK)
        surface.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

def generate_custom_grid(agent_pos_str, gold_pos_str, num_wumpus=1, num_pits=9):
    try:
        agent_pos = tuple(map(int, agent_pos_str.split(',')))
        gold_pos = tuple(map(int, gold_pos_str.split(',')))
        
        # Validate positions
        if not (0 <= agent_pos[0] < GRID_SIZE and 0 <= agent_pos[1] < GRID_SIZE):
            agent_pos = (0, 0)
        if not (0 <= gold_pos[0] < GRID_SIZE and 0 <= gold_pos[1] < GRID_SIZE):
            gold_pos = (GRID_SIZE-1, GRID_SIZE-1)
            
        grid = [[EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Place wumpuses
        wumpus_positions = []
        for _ in range(num_wumpus):
            while True:
                wumpus_pos = (random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1))
                if wumpus_pos != agent_pos and wumpus_pos != gold_pos and wumpus_pos not in wumpus_positions:
                    wumpus_positions.append(wumpus_pos)
                    break
        
        # Place pits
        pit_positions = []
        for _ in range(num_pits):
            attempts = 0
            while attempts < 100:  # Prevent infinite loop
                pit_pos = (random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1))
                if (pit_pos != agent_pos and pit_pos != gold_pos and 
                    pit_pos not in wumpus_positions and pit_pos not in pit_positions):
                    pit_positions.append(pit_pos)
                    break
                attempts += 1
            
        # Populate grid
        grid[agent_pos[0]][agent_pos[1]] = AGENT
        grid[gold_pos[0]][gold_pos[1]] = GOLD
        
        for pos in wumpus_positions:
            grid[pos[0]][pos[1]] = WUMPUS
            
        for pos in pit_positions:
            grid[pos[0]][pos[1]] = PIT
            
        return grid, agent_pos, gold_pos, wumpus_positions[0] if wumpus_positions else None
        
    except (ValueError, IndexError):
        # Fallback to random generation if parsing fails
        return generate_random_grid()

def generate_random_grid():
    grid = [[EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    # Place agent in the top-left corner
    agent_pos = (0, 0)
    
    # Place gold in the bottom-right corner
    gold_pos = (GRID_SIZE-1, GRID_SIZE-1)
    
    # Place wumpus randomly, but not on agent or gold
    while True:
        wumpus_pos = (random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1))
        if wumpus_pos != agent_pos and wumpus_pos != gold_pos:
            break
    
    # Place pits randomly
    pits = set()
    while len(pits) < 9:
        pit_pos = (random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1))
        if pit_pos != agent_pos and pit_pos != gold_pos and pit_pos != wumpus_pos:
            pits.add(pit_pos)
   
    grid[agent_pos[0]][agent_pos[1]] = AGENT
    grid[gold_pos[0]][gold_pos[1]] = GOLD
    grid[wumpus_pos[0]][wumpus_pos[1]] = WUMPUS
    
    for pit in pits:
        grid[pit[0]][pit[1]] = PIT
    
    return grid, agent_pos, gold_pos, wumpus_pos

def draw_grid(surface, grid):
    surface.fill(WHITE)
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x, y = col * TILE_SIZE, row * TILE_SIZE
            pygame.draw.rect(surface, BLACK, (x, y, TILE_SIZE, TILE_SIZE), 1)
            
            cell_value = grid[row][col]
            if cell_value == AGENT:
                pygame.draw.circle(surface, BLUE, (x + TILE_SIZE // 2, y + TILE_SIZE // 2), TILE_SIZE // 3)
            elif cell_value == WUMPUS:
                pygame.draw.circle(surface, RED, (x + TILE_SIZE // 2, y + TILE_SIZE // 2), TILE_SIZE // 3)
            elif cell_value == GOLD:
                pygame.draw.circle(surface, GREEN, (x + TILE_SIZE // 2, y + TILE_SIZE // 2), TILE_SIZE // 3)
            elif cell_value == PIT:
                pygame.draw.rect(surface, BLACK, (x + 10, y + 10, TILE_SIZE - 20, TILE_SIZE - 20))
                
    # Add legend
    legend_y = 10
    legend_x = 10
    
    legend_items = [
        (BLUE, "Agent"),
        (GREEN, "Gold"),
        (RED, "Wumpus"),
        (BLACK, "Pit")
    ]
    
    for color, text in legend_items:
        pygame.draw.circle(surface, color, (legend_x + 10, legend_y + 10), 10)
        text_surface = small_font.render(text, True, BLACK)
        surface.blit(text_surface, (legend_x + 30, legend_y))
        legend_y += 30

def bfs_search(grid, start, goal):
    queue = deque([(start, [])])
    visited = set()
    
    while queue:
        (x, y), path = queue.popleft()
        
        if (x, y) == goal:
            return path + [(x, y)]
            
        if (x, y) in visited:
            continue
            
        visited.add((x, y))
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and 
                grid[nx][ny] != PIT and grid[nx][ny] != WUMPUS):
                queue.append(((nx, ny), path + [(x, y)]))
                
    return []

def move_agent(grid, path, screen):
    temp_grid = [row[:] for row in grid]  # Create a copy of the grid
    
    for i, pos in enumerate(path):
        # Reset the previous position to EMPTY
        if i > 0:
            prev_pos = path[i-1]
            temp_grid[prev_pos[0]][prev_pos[1]] = EMPTY
        
        # Set current position to AGENT
        temp_grid[pos[0]][pos[1]] = AGENT
        
        # Draw and delay
        draw_grid(screen, temp_grid)
        pygame.display.flip()
        pygame.time.delay(300)
        
        # Process events to keep the window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

def main():
    # Create a screen for the welcome screen
    welcome_screen = pygame.display.set_mode((WIDTH, WELCOME_HEIGHT))
    game_screen = None
    pygame.display.set_caption("Wumpus AI Game")
    
    # Create UI elements
    agent_input = TextInput(WIDTH//2 - 150, HEIGHT + 30, 300, TEXT_INPUT_HEIGHT, 
                           "Agent Position (row,col):", "0,0")
    gold_input = TextInput(WIDTH//2 - 150, HEIGHT + 30 + TEXT_INPUT_HEIGHT + 20, 300, TEXT_INPUT_HEIGHT,
                          "Gold Position (row,col):", "11,11")
    
    preview_button = Button(WIDTH//2 - 310, HEIGHT + 30 + 2*TEXT_INPUT_HEIGHT + 40, 
                          200, BUTTON_HEIGHT, "Preview", GRAY)
    start_button = Button(WIDTH//2 + 110, HEIGHT + 30 + 2*TEXT_INPUT_HEIGHT + 40, 
                         200, BUTTON_HEIGHT, "Start Game", GREEN)
    
    # Game variables
    game_state = WELCOME_SCREEN
    grid = None
    agent_pos = None
    gold_pos = None
    wumpus_pos = None
    path = None
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if game_state == WELCOME_SCREEN:
                agent_input.handle_event(event)
                gold_input.handle_event(event)
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if preview_button.is_clicked(event.pos):
                        # Generate and display preview
                        grid, agent_pos, gold_pos, wumpus_pos = generate_custom_grid(
                            agent_input.text, gold_input.text)
                        welcome_screen.fill(WHITE)
                        
                        # Draw smaller preview grid
                        preview_surface = pygame.Surface((WIDTH, HEIGHT))
                        draw_grid(preview_surface, grid)
                        
                        # Scale down the preview
                        preview_scale = 0.5
                        scaled_preview = pygame.transform.scale(
                            preview_surface, 
                            (int(WIDTH * preview_scale), int(HEIGHT * preview_scale))
                        )
                        
                        # Display scaled preview at the top
                        welcome_screen.blit(scaled_preview, (WIDTH//2 - scaled_preview.get_width()//2, 20))
                    
                    elif start_button.is_clicked(event.pos):
                        # Start the game
                        game_screen = pygame.display.set_mode((WIDTH, HEIGHT))
                        grid, agent_pos, gold_pos, wumpus_pos = generate_custom_grid(
                            agent_input.text, gold_input.text)
                        game_state = GAME_RUNNING
                        
                        # Find path using BFS
                        path = bfs_search(grid, agent_pos, gold_pos)
        
        # Rendering
        if game_state == WELCOME_SCREEN:
            welcome_screen.fill(WHITE)
            
            # Draw title
            title = font.render("Wumpus AI Game - Setup", True, BLACK)
            welcome_screen.blit(title, (WIDTH//2 - title.get_width()//2, 10))
            
            # Draw instructions
            instructions = small_font.render(
                "Set the starting positions for the agent and gold. Format: row,col (0-11)", 
                True, BLACK
            )
            welcome_screen.blit(instructions, (WIDTH//2 - instructions.get_width()//2, 50))
            
            # Draw UI elements
            agent_input.draw(welcome_screen)
            gold_input.draw(welcome_screen)
            preview_button.draw(welcome_screen)
            start_button.draw(welcome_screen)
            
            # If grid exists, draw preview
            if grid:
                preview_surface = pygame.Surface((WIDTH, HEIGHT))
                draw_grid(preview_surface, grid)
                
                # Scale down the preview
                preview_scale = 0.4
                scaled_preview = pygame.transform.scale(
                    preview_surface, 
                    (int(WIDTH * preview_scale), int(HEIGHT * preview_scale))
                )
                
                # Display scaled preview
                welcome_screen.blit(scaled_preview, (WIDTH//2 - scaled_preview.get_width()//2, 100))
                
                # Draw path info
                test_path = bfs_search(grid, agent_pos, gold_pos)
                if test_path:
                    path_text = small_font.render(
                        f"Path found! Length: {len(test_path)} steps", True, GREEN)
                else:
                    path_text = small_font.render(
                        "No path found! Agent cannot reach the gold.", True, RED)
                welcome_screen.blit(path_text, (WIDTH//2 - path_text.get_width()//2, 
                                             100 + scaled_preview.get_height() + 20))
                
        elif game_state == GAME_RUNNING:
            draw_grid(game_screen, grid)
            
            if path:
                # Display message about the path
                message = font.render(f"Path length: {len(path)} steps", True, BLACK)
                game_screen.blit(message, (WIDTH//2 - message.get_width()//2, 10))
                
                # Move agent along the path
                move_agent(grid, path, game_screen)
                
                # Wait a bit after reaching the gold
                pygame.time.delay(2000)
                
                # Return to welcome screen
                game_screen = None
                game_state = WELCOME_SCREEN
                welcome_screen = pygame.display.set_mode((WIDTH, WELCOME_HEIGHT))
            else:
                # Display message that no path was found
                message = font.render("No path found! Agent cannot reach the gold.", True, RED)
                game_screen.blit(message, (WIDTH//2 - message.get_width()//2, HEIGHT//2))
                pygame.display.flip()
                
                # Wait and return to welcome screen
                pygame.time.delay(3000)
                game_screen = None
                game_state = WELCOME_SCREEN
                welcome_screen = pygame.display.set_mode((WIDTH, WELCOME_HEIGHT))
        
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()

if __name__ == "__main__":
    main()