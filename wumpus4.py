import pygame
import random
import math
import os
import json
from collections import deque
import imageio  # For GIF export
from datetime import datetime

# Constants for the game grid
GRID_SIZE = 10  # 10x10 grid
TILE_SIZE = 80  # Tile size
WIDTH, HEIGHT = GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
BUTTON_HEIGHT = 50
TEXT_INPUT_HEIGHT = 40
UI_PADDING = 20
SIDEBAR_WIDTH = 300
GAME_SCREEN_WIDTH = WIDTH + SIDEBAR_WIDTH

# Game states
MAIN_MENU = 0
GAME_SETUP = 1
GAME_RUNNING = 2
MAP_EDITOR = 3
SETTINGS = 4
STATS_SCREEN = 5
LEVEL_SELECT = 6

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 150, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
LIGHT_BLUE = (173, 216, 230)
YELLOW = (255, 255, 0)
LIGHT_GREEN = (144, 238, 144)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)
TRANSPARENT_YELLOW = (255, 255, 0, 128)

# Entities
AGENT = "A"
WUMPUS = "W"
GOLD = "G"
PIT = "P"
EMPTY = "_"
TRAIL = "T"
OBSTACLE = "O"
TRAP = "X"  # New trap entity
TELEPORT = "TP"  # New teleport entity

# Difficulty settings
DIFFICULTY_SETTINGS = {
    "Easy": {"wumpus": 1, "pits": 5, "obstacles": 1, "traps": 0, "teleports": 0},
    "Medium": {"wumpus": 2, "pits": 8, "obstacles": 3, "traps": 1, "teleports": 0},
    "Hard": {"wumpus": 3, "pits": 10, "obstacles": 5, "traps": 2, "teleports": 1},
    "Expert": {"wumpus": 4, "pits": 12, "obstacles": 7, "traps": 3, "teleports": 2}
}

# Initialize Pygame
pygame.init()
pygame.font.init()
font = pygame.font.SysFont('Arial', 24)
title_font = pygame.font.SysFont('Arial', 36, bold=True)
small_font = pygame.font.SysFont('Arial', 18)
tiny_font = pygame.font.SysFont('Arial', 14)

# Load or generate stats data
def load_stats():
    try:
        if os.path.exists('wumpus_stats.json'):
            with open('wumpus_stats.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading stats: {e}")
    # Default stats
    return {
        "games_played": 0,
        "gold_collected": 0,
        "total_steps": 0,
        "deaths": 0,
        "best_path_length": float('inf'),
        "best_score": 0,
        "levels_completed": {},
        "history": []
    }

stats_data = load_stats()

def save_stats():
    try:
        with open('wumpus_stats.json', 'w') as f:
            json.dump(stats_data, f)
    except Exception as e:
        print(f"Error saving stats: {e}")

class Button:
    def __init__(self, x, y, width, height, text, color, action=None, disabled=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = (min(color[0] + 30, 255), min(color[1] + 30, 255), min(color[2] + 30, 255))
        self.active_color = color
        self.disabled_color = (150, 150, 150)
        self.action = action
        self.disabled = disabled
        
    def draw(self, surface):
        if self.disabled:
            pygame.draw.rect(surface, self.disabled_color, self.rect)
        else:
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
        if self.disabled:
            return False
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

class Dropdown:
    def __init__(self, x, y, width, height, options, label="", default_index=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.label = label
        self.selected_index = default_index
        self.expanded = False
        self.option_height = height
        self.label_surface = font.render(label, True, BLACK)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
            elif self.expanded:
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(
                        self.rect.x, 
                        self.rect.y + (i + 1) * self.option_height, 
                        self.rect.width, 
                        self.option_height
                    )
                    if option_rect.collidepoint(event.pos):
                        self.selected_index = i
                        self.expanded = False
                        break
                # Click outside the dropdown closes it
                self.expanded = False
    
    def draw(self, surface):
        # Draw label
        if self.label:
            label_rect = self.label_surface.get_rect(bottomleft=(self.rect.x, self.rect.y - 5))
            surface.blit(self.label_surface, label_rect)
        
        # Draw selected option
        pygame.draw.rect(surface, WHITE, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        text = self.options[self.selected_index]
        text_surface = font.render(text, True, BLACK)
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 10, self.rect.y + self.rect.height//2))
        surface.blit(text_surface, text_rect)
        
        # Draw dropdown arrow
        arrow_size = 10
        arrow_pos = (self.rect.right - 20, self.rect.centery)
        pygame.draw.polygon(surface, BLACK, [
            (arrow_pos[0] - arrow_size, arrow_pos[1] - arrow_size//2),
            (arrow_pos[0] + arrow_size, arrow_pos[1] - arrow_size//2),
            (arrow_pos[0], arrow_pos[1] + arrow_size//2)
        ])
        
        # Draw expanded options
        if self.expanded:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(
                    self.rect.x, 
                    self.rect.y + (i + 1) * self.option_height, 
                    self.rect.width, 
                    self.option_height
                )
                pygame.draw.rect(surface, WHITE, option_rect)
                pygame.draw.rect(surface, BLACK, option_rect, 1)
                
                option_text = font.render(option, True, BLACK)
                text_rect = option_text.get_rect(midleft=(option_rect.x + 10, option_rect.y + option_rect.height//2))
                surface.blit(option_text, text_rect)
                
    def get_selected(self):
        return self.options[self.selected_index]

class Animation:
    def __init__(self, start_pos, end_pos, duration=300, entity_type=AGENT):
        self.start_pos = start_pos  # Grid position (row, col)
        self.end_pos = end_pos      # Grid position (row, col)
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.entity_type = entity_type
        self.completed = False
        
        # Convert grid positions to pixel positions
        self.start_pixel = (start_pos[1] * TILE_SIZE + TILE_SIZE // 2, 
                            start_pos[0] * TILE_SIZE + TILE_SIZE // 2)
        self.end_pixel = (end_pos[1] * TILE_SIZE + TILE_SIZE // 2, 
                         end_pos[0] * TILE_SIZE + TILE_SIZE // 2)
        
        # Special effects
        self.rotation = 0
        self.scale = 1.0
        self.alpha = 255
        self.particles = []
        
        # Special animation for gold collection
        if entity_type == GOLD:
            self.create_particles()
    
    def create_particles(self, count=20):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5)
            size = random.uniform(2, 8)
            lifetime = random.uniform(500, 1500)
            self.particles.append({
                'pos': list(self.start_pixel),
                'vel': [math.cos(angle) * speed, math.sin(angle) * speed],
                'size': size,
                'color': YELLOW,
                'lifetime': lifetime,
                'start_time': pygame.time.get_ticks()
            })
    
    def update(self):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        if elapsed >= self.duration:
            self.completed = True
            return True
        
        # Update particle effects
        for particle in self.particles:
            particle_elapsed = current_time - particle['start_time']
            if particle_elapsed > particle['lifetime']:
                self.particles.remove(particle)
                continue
                
            # Update particle position
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            
            # Fade out over time
            particle['color'] = list(particle['color'])
            fade_factor = 1 - (particle_elapsed / particle['lifetime'])
            particle['color'][3] = int(255 * fade_factor) if len(particle['color']) > 3 else 255
            
        return False
        
    def draw(self, surface):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # Calculate current position with easing
        eased_progress = self.ease_out_quad(progress)
        current_x = self.start_pixel[0] + (self.end_pixel[0] - self.start_pixel[0]) * eased_progress
        current_y = self.start_pixel[1] + (self.end_pixel[1] - self.start_pixel[1]) * eased_progress
        
        # Draw based on entity type
        if self.entity_type == AGENT:
            # Agent animation - blue circle with smooth movement
            pygame.draw.circle(surface, BLUE, (int(current_x), int(current_y)), int(TILE_SIZE // 3 * (1 + 0.2 * math.sin(progress * math.pi))))
            # Draw a direction indicator
            dir_x = self.end_pixel[0] - self.start_pixel[0]
            dir_y = self.end_pixel[1] - self.start_pixel[1]
            if dir_x != 0 or dir_y != 0:
                norm = math.sqrt(dir_x**2 + dir_y**2)
                dir_x, dir_y = dir_x/norm, dir_y/norm
                pygame.draw.line(surface, BLACK, 
                                (int(current_x), int(current_y)),
                                (int(current_x + dir_x * TILE_SIZE//4), int(current_y + dir_y * TILE_SIZE//4)),
                                3)
        
        elif self.entity_type == GOLD:
            # Gold collection animation - particles and a shrinking gold circle
            # Draw particles
            for particle in self.particles:
                pygame.draw.circle(surface, particle['color'], 
                                  (int(particle['pos'][0]), int(particle['pos'][1])), 
                                  int(particle['size']))
            
            # Draw shrinking gold
            if progress < 0.7:  # Only show during first part of animation
                size_factor = 1 - progress/0.7
                pygame.draw.circle(surface, GREEN, 
                                  (int(current_x), int(current_y)), 
                                  int(TILE_SIZE // 3 * size_factor))
                
        elif self.entity_type == TRAP:
            # Trap animation - red flash
            flash_intensity = math.sin(progress * math.pi * 8)  # Quick flashing
            flash_color = (255, max(0, int(255 * (1-flash_intensity))), max(0, int(255 * (1-flash_intensity))))
            pygame.draw.rect(surface, flash_color, 
                           (int(current_x - TILE_SIZE//3), int(current_y - TILE_SIZE//3),
                            TILE_SIZE//1.5, TILE_SIZE//1.5))
            
        elif self.entity_type == TELEPORT:
            # Teleport animation - circular ripple effect
            for i in range(3):
                ripple_progress = (progress + i/3) % 1.0
                radius = TILE_SIZE//2 * ripple_progress
                width = max(1, int(TILE_SIZE//10 * (1 - ripple_progress)))
                pygame.draw.circle(surface, PURPLE, 
                                 (int(current_x), int(current_y)), 
                                 int(radius), width)
    
    def ease_out_quad(self, x):
        return 1 - (1 - x) * (1 - x)

class Level:
    def __init__(self, name, difficulty, size=GRID_SIZE, custom_config=None):
        self.name = name
        self.difficulty = difficulty
        self.size = size
        
        # Default settings based on difficulty
        self.settings = DIFFICULTY_SETTINGS[difficulty].copy() if difficulty in DIFFICULTY_SETTINGS else DIFFICULTY_SETTINGS["Medium"].copy()
        
        # Custom configuration overrides defaults
        if custom_config:
            self.settings.update(custom_config)
        
        # Default starting positions
        self.agent_pos = (0, 0)
        self.gold_pos = (size-1, size-1)
        
    def generate_grid(self):
        """Generate a grid based on level settings"""
        grid = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
        
        # Place agent and gold
        grid[self.agent_pos[0]][self.agent_pos[1]] = AGENT
        grid[self.gold_pos[0]][self.gold_pos[1]] = GOLD
        
        # Place wumpuses
        wumpus_positions = []
        for _ in range(self.settings["wumpus"]):
            pos = self.find_empty_position(grid, [self.agent_pos, self.gold_pos] + wumpus_positions)
            if pos:
                wumpus_positions.append(pos)
                grid[pos[0]][pos[1]] = WUMPUS
        
        # Place pits
        pit_positions = []
        for _ in range(self.settings["pits"]):
            pos = self.find_empty_position(grid, [self.agent_pos, self.gold_pos] + wumpus_positions + pit_positions)
            if pos:
                pit_positions.append(pos)
                grid[pos[0]][pos[1]] = PIT
        
        # Place obstacles
        obstacle_positions = []
        for _ in range(self.settings["obstacles"]):
            pos = self.find_empty_position(grid, [self.agent_pos, self.gold_pos] + wumpus_positions + pit_positions + obstacle_positions)
            if pos:
                obstacle_positions.append(pos)
                grid[pos[0]][pos[1]] = OBSTACLE
        
        # Place traps
        trap_positions = []
        for _ in range(self.settings["traps"]):
            pos = self.find_empty_position(grid, [self.agent_pos, self.gold_pos] + wumpus_positions + pit_positions + obstacle_positions + trap_positions)
            if pos:
                trap_positions.append(pos)
                grid[pos[0]][pos[1]] = TRAP
        
        # Place teleports
        teleport_positions = []
        for _ in range(self.settings["teleports"]):
            pos = self.find_empty_position(grid, [self.agent_pos, self.gold_pos] + wumpus_positions + pit_positions + obstacle_positions + trap_positions + teleport_positions)
            if pos:
                teleport_positions.append(pos)
                grid[pos[0]][pos[1]] = TELEPORT
                
        return grid, self.agent_pos, self.gold_pos, wumpus_positions
    
    def find_empty_position(self, grid, exclude_positions):
        """Find a random empty position that's not in the excluded list"""
        attempts = 0
        while attempts < 100:  # Prevent infinite loop
            row = random.randint(0, self.size-1)
            col = random.randint(0, self.size-1)
            
            if grid[row][col] == EMPTY and (row, col) not in exclude_positions:
                # Also check that the position isn't adjacent to the agent start
                if abs(row - self.agent_pos[0]) > 1 or abs(col - self.agent_pos[1]) > 1:
                    return (row, col)
            
            attempts += 1
        
        # If we couldn't find a position after many attempts, just find any empty space
        for row in range(self.size):
            for col in range(self.size):
                if grid[row][col] == EMPTY and (row, col) not in exclude_positions:
                    return (row, col)
        
        return None  # Grid is full (shouldn't happen)

class GameManager:
    def __init__(self):
        self.game_state = MAIN_MENU
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Wumpus AI Game")
        
        # Game variables
        self.grid = None
        self.agent_pos = None
        self.gold_pos = None
        self.wumpus_positions = []
        self.path = []
        self.record_gif = False
        self.animation = None
        self.animations = []
        self.teleport_destinations = {}  # Maps teleport positions to destination positions
        self.current_level = None
        self.levels = self.generate_default_levels()
        self.current_level_index = 0
        self.difficulty = "Medium"
        self.animation_speed = 300  # ms per step
        self.paused = False
        self.map_editor_selected_tile = EMPTY
        self.score = 0
        self.steps_taken = 0
        self.gold_collected = 0
        self.game_over = False
        self.game_won = False
        self.show_path_preview = True
        self.game_start_time = 0
        self.game_time_elapsed = 0
        self.gif_frames = []
        
        # UI elements
        self.setup_ui()
        
        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()
        
        # Challenge mode
        self.challenge_mode = False
        self.challenge_timer = 0
        self.challenge_interval = 10000  # 10 seconds between changes
        self.challenge_next_change = 0
    
    def generate_default_levels(self):
        """Generate default game levels"""
        levels = []
        
        # Tutorial level
        tutorial = Level("Tutorial", "Easy", GRID_SIZE, 
                        {"wumpus": 0, "pits": 3, "obstacles": 2, "traps": 0, "teleports": 0})
        levels.append(tutorial)
        
        # Default levels with increasing difficulty
        for i, diff in enumerate(["Easy", "Medium", "Hard", "Expert"]):
            level = Level(f"Level {i+1}", diff, GRID_SIZE)
            levels.append(level)
        
        # Special challenge level
        challenge = Level("Challenge Mode", "Expert", GRID_SIZE, 
                         {"wumpus": 3, "pits": 8, "obstacles": 4, "traps": 2, "teleports": 2})
        levels.append(challenge)
        
        return levels
    
    def setup_ui(self):
        """Initialize all UI elements"""
        # Main menu buttons
        menu_width = 300
        menu_height = 50
        menu_x = WIDTH // 2 - menu_width // 2
        self.main_menu_buttons = [
            Button(menu_x, 200, menu_width, menu_height, "Play Game", GREEN, GAME_SETUP),
            Button(menu_x, 270, menu_width, menu_height, "Map Editor", BLUE, MAP_EDITOR),
            Button(menu_x, 340, menu_width, menu_height, "Statistics", GRAY, STATS_SCREEN),
            Button(menu_x, 410, menu_width, menu_height, "Settings", GRAY, SETTINGS),
            Button(menu_x, 480, menu_width, menu_height, "Quit", RED, "quit")
        ]
        
        # Difficulty selector
        self.difficulty_dropdown = Dropdown(
            WIDTH // 2 - 150, 150, 300, 40,
            ["Easy", "Medium", "Hard", "Expert"],
            "Difficulty:", 1  # Default to Medium
        )
        
        # Game setup UI
        self.agent_input = TextInput(WIDTH//2 - 150, HEIGHT - 200, 300, TEXT_INPUT_HEIGHT, 
                                    "Agent Position (row,col):", "0,0")
        self.gold_input = TextInput(WIDTH//2 - 150, HEIGHT - 140, 300, TEXT_INPUT_HEIGHT,
                                   "Gold Position (row,col):", f"{GRID_SIZE-1},{GRID_SIZE-1}")
        
        self.preview_button = Button(WIDTH//2 - 310, HEIGHT - 80, 
                                   200, BUTTON_HEIGHT, "Preview", GRAY)
        self.start_button = Button(WIDTH//2 - 100, HEIGHT - 80, 
                                  200, BUTTON_HEIGHT, "Start Game", GREEN)
        self.gif_button = Button(WIDTH//2 + 110, HEIGHT - 80, 
                               200, BUTTON_HEIGHT, "Start & Save GIF", BLUE)
        
        # Level select buttons
        self.level_buttons = []
        level_btn_width = 200
        level_btn_x = WIDTH // 2 - level_btn_width // 2
        for i, level in enumerate(self.levels):
            btn = Button(level_btn_x, 150 + i*70, level_btn_width, 60, 
                       f"{level.name} ({level.difficulty})", GREEN)
            self.level_buttons.append(btn)
        
        # Settings UI
        self.settings_speed_slider = None  # TODO: Implement slider for animation speed
        
        # Map editor UI elements
        self.map_editor_palette = [
            Button(20, HEIGHT - 200, 80, 40, "Agent", BLUE, AGENT),
            Button(110, HEIGHT - 200, 80, 40, "Gold", GREEN, GOLD),
            Button(200, HEIGHT - 200, 80, 40, "Wumpus", RED, WUMPUS),
            Button(290, HEIGHT - 200, 80, 40, "Pit", BLACK, PIT),
            Button(380, HEIGHT - 200, 80, 40, "Empty", WHITE, EMPTY),
            Button(470, HEIGHT - 200, 80, 40, "Obstacle", BROWN, OBSTACLE),
            Button(560, HEIGHT - 200, 80, 40, "Trap", ORANGE, TRAP),
            Button(650, HEIGHT - 200, 80, 40, "Teleport", PURPLE, TELEPORT)
        ]
        
        self.map_editor_buttons = [
            Button(20, HEIGHT - 140, 180, 40, "Clear Map", GRAY),
            Button(210, HEIGHT - 140, 180, 40, "Save Map", GREEN),
            Button(400, HEIGHT - 140, 180, 40, "Load Map", BLUE),
            Button(590, HEIGHT - 140, 180, 40, "Test Path", YELLOW),
            Button(WIDTH//2 - 200, HEIGHT - 80, 400, 50, "Back to Main Menu", RED, MAIN_MENU)
        ]
        
        # Game UI
        self.game_ui_buttons = [
            Button(WIDTH + 20, 20, SIDEBAR_WIDTH - 40, 40, "Pause/Resume", GRAY),
            Button(WIDTH + 20, 70, SIDEBAR_WIDTH - 40, 40, "Restart Level", YELLOW),
            Button(WIDTH + 20, 120, SIDEBAR_WIDTH - 40, 40, "Main Menu", RED, MAIN_MENU)
        ]
        
        # Stats screen UI
        self.stats_back_button = Button(WIDTH//2 - 100, HEIGHT - 80, 200, 50, "Back", RED, MAIN_MENU)
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                self.handle_event(event)
            
            self.update()
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
    
    def handle_event(self, event):
        """Handle various pygame events based on game state"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse_click(event.pos)
            
        # Handle keyboard input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.game_state in [GAME_SETUP, MAP_EDITOR, SETTINGS, STATS_SCREEN, LEVEL_SELECT]:
                    self.game_state = MAIN_MENU
                elif self.game_state == GAME_RUNNING:
                    self.paused = not self.paused
            
            # Handle spacebar for pause/resume during animation
            if event.key == pygame.K_SPACE and self.game_state == GAME_RUNNING:
                self.paused = not self.paused
        
        # Handle text inputs
        if self.game_state == GAME_SETUP:
            self.agent_input.handle_event(event)
            self.gold_input.handle_event(event)
            self.difficulty_dropdown.handle_event(event)
        
        # Handle map editor clicks
        if self.game_state == MAP_EDITOR and event.type == pygame.MOUSEBUTTONDOWN:
            if event.pos[0] < WIDTH and event.pos[1] < HEIGHT:
                # Calculate grid position from mouse click
                col = event.pos[0] // TILE_SIZE
                row = event.pos[1] // TILE_SIZE
                
                if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                    if self.grid is None:
                        self.grid = [[EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    
                    # Place the selected tile type
                    old_value = self.grid[row][col]
                    self.grid[row][col] = self.map_editor_selected_tile
                    
                    # Handle special cases
                    if self.map_editor_selected_tile == AGENT:
                        # Remove any existing agent
                        for r in range(GRID_SIZE):
                            for c in range(GRID_SIZE):
                                if (r, c) != (row, col) and self.grid[r][c] == AGENT:
                                    self.grid[r][c] = EMPTY
                        self.agent_pos = (row, col)
                    
                    elif self.map_editor_selected_tile == GOLD:
                        # Remove any existing gold
                        for r in range(GRID_SIZE):
                            for c in range(GRID_SIZE):
                                if (r, c) != (row, col) and self.grid[r][c] == GOLD:
                                    self.grid[r][c] = EMPTY
                        self.gold_pos = (row, col)
                    
                    # Handle teleport pairing
                    if self.map_editor_selected_tile == TELEPORT and old_value != TELEPORT:
                        # Find any existing unpaired teleport
                        unpaired = None
                        for r in range(GRID_SIZE):
                            for c in range(GRID_SIZE):
                                if (r, c) != (row, col) and self.grid[r][c] == TELEPORT:
                                    if (r, c) not in self.teleport_destinations:
                                        unpaired = (r, c)
                                        break
                        
                        if unpaired:
                            # Create bidirectional teleport link
                            self.teleport_destinations[unpaired] = (row, col)
                            self.teleport_destinations[(row, col)] = unpaired
    
    def handle_mouse_click(self, pos):
        """Handle mouse clicks based on current game state"""
        if self.game_state == MAIN_MENU:
            for button in self.main_menu_buttons:
                if button.is_clicked(pos):
                    if button.action == "quit":
                        pygame.quit()
                        exit()
                    else:
                        self.game_state = button.action
                        if button.action == GAME_SETUP:
                            self.game_state = LEVEL_SELECT
                        elif button.action == MAP_EDITOR:
                            self.initialize_map_editor()
        
        elif self.game_state == LEVEL_SELECT:
            for i, button in enumerate(self.level_buttons):
                if button.is_clicked(pos):
                    self.current_level_index = i
                    self.current_level = self.levels[i]
                    self.initialize_game()
                    self.game_state = GAME_RUNNING
        
        elif self.game_state == GAME_SETUP:
            if self.preview_button.is_clicked(pos):
                self.initialize_game(True)  # Just preview
            elif self.start_button.is_clicked(pos):
                self.initialize_game()
                self.game_state = GAME_RUNNING
            elif self.gif_button.is_clicked(pos):
                self.record_gif = True
                self.initialize_game()
                self.game_state = GAME_RUNNING
        
        elif self.game_state == GAME_RUNNING:
            for i, button in enumerate(self.game_ui_buttons):
                if button.is_clicked(pos):
                    if i == 0:  # Pause/Resume button
                        self.paused = not self.paused
                    elif i == 1:  # Restart Level button
                        self.initialize_game()
                    elif i == 2:  # Main Menu button
                        self.game_state = MAIN_MENU
        
        elif self.game_state == MAP_EDITOR:
            # Handle map editor palette clicks
            for button in self.map_editor_palette:
                if button.is_clicked(pos):
                    self.map_editor_selected_tile = button.action
            
            # Handle map editor action buttons
            for i, button in enumerate(self.map_editor_buttons):
                if button.is_clicked(pos):
                    if i == 0:  # Clear Map
                        self.grid = [[EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                        self.agent_pos = (0, 0)
                        self.grid[0][0] = AGENT
                        self.gold_pos = (GRID_SIZE-1, GRID_SIZE-1)
                        self.grid[GRID_SIZE-1][GRID_SIZE-1] = GOLD
                        self.teleport_destinations = {}
                    elif i == 1:  # Save Map
                        self.save_custom_map()
                    elif i == 2:  # Load Map
                        self.load_custom_map()
                    elif i == 3:  # Test Path
                        self.calculate_path()
                    elif i == 4:  # Back to Main Menu
                        self.game_state = MAIN_MENU
        
        elif self.game_state == STATS_SCREEN:
            if self.stats_back_button.is_clicked(pos):
                self.game_state = MAIN_MENU
        
        elif self.game_state == SETTINGS:
            # Handle settings UI clicks (to be implemented)
            pass

    def save_custom_map(self):
        """Save the current map to a file"""
        try:
            custom_map = {
                "grid": self.grid,
                "agent_pos": self.agent_pos,
                "gold_pos": self.gold_pos,
                "teleport_destinations": self.teleport_destinations
            }
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"custom_map_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(custom_map, f)
            print(f"Map saved as {filename}")
        except Exception as e:
            print(f"Error saving map: {e}")
    
    def load_custom_map(self):
        """Load a map from available custom maps"""
        # In a real implementation, you'd show a file picker
        # For simplicity, we'll just load the latest map if available
        try:
            import glob
            map_files = glob.glob("custom_map_*.json")
            if map_files:
                latest_map = max(map_files)
                with open(latest_map, 'r') as f:
                    custom_map = json.load(f)
                self.grid = custom_map["grid"] 
                self.agent_pos = tuple(custom_map["agent_pos"])
                self.gold_pos = tuple(custom_map["gold_pos"])
                
                # Convert string keys back to tuples for teleport_destinations
                teleport_dict = {}
                for k, v in custom_map["teleport_destinations"].items():
                    teleport_dict[eval(k) if isinstance(k, str) else tuple(k)] = tuple(v)
                self.teleport_destinations = teleport_dict
                
                print(f"Loaded map from {latest_map}")
            else:
                print("No custom maps found")
        except Exception as e:
            print(f"Error loading map: {e}")
    
    def initialize_map_editor(self):
        """Initialize the map editor with a blank grid"""
        self.grid = [[EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.agent_pos = (0, 0)
        self.grid[0][0] = AGENT
        self.gold_pos = (GRID_SIZE-1, GRID_SIZE-1)
        self.grid[GRID_SIZE-1][GRID_SIZE-1] = GOLD
        self.teleport_destinations = {}
        self.map_editor_selected_tile = EMPTY
    
    def initialize_game(self, preview_only=False):
        """Initialize a new game based on current settings"""
        # Reset game variables
        self.path = []
        self.animations = []
        self.animation = None
        self.game_over = False
        self.game_won = False
        self.steps_taken = 0
        self.score = 0
        self.gold_collected = 0
        self.game_time_elapsed = 0
        self.gif_frames = []
        
        # Get positions from input fields or generate a new level
        if self.game_state == GAME_SETUP:
            try:
                agent_row, agent_col = map(int, self.agent_input.text.split(','))
                gold_row, gold_col = map(int, self.gold_input.text.split(','))
                
                if (0 <= agent_row < GRID_SIZE and 0 <= agent_col < GRID_SIZE and
                    0 <= gold_row < GRID_SIZE and 0 <= gold_col < GRID_SIZE):
                    self.agent_pos = (agent_row, agent_col)
                    self.gold_pos = (gold_row, gold_col)
                else:
                    self.agent_pos = (0, 0)
                    self.gold_pos = (GRID_SIZE-1, GRID_SIZE-1)
            except:
                self.agent_pos = (0, 0)
                self.gold_pos = (GRID_SIZE-1, GRID_SIZE-1)
            
            # Generate grid based on difficulty
            self.difficulty = self.difficulty_dropdown.get_selected()
            level = Level("Custom", self.difficulty, GRID_SIZE)
            self.grid, _, _, self.wumpus_positions = level.generate_grid()
            
            # Override the agent and gold positions
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if self.grid[r][c] in [AGENT, GOLD]:
                        self.grid[r][c] = EMPTY
            
            self.grid[self.agent_pos[0]][self.agent_pos[1]] = AGENT
            self.grid[self.gold_pos[0]][self.gold_pos[1]] = GOLD
            
        elif self.current_level:
            # Use the selected level
            self.grid, self.agent_pos, self.gold_pos, self.wumpus_positions = self.current_level.generate_grid()
            
            # Set up challenge mode if applicable
            if self.current_level.name == "Challenge Mode":
                self.challenge_mode = True
                self.challenge_next_change = pygame.time.get_ticks() + self.challenge_interval
            else:
                self.challenge_mode = False
        
        # Initialize teleport destinations
        self.initialize_teleports()
        
        # Calculate path
        self.calculate_path()
        
        # Start game timer
        self.game_start_time = pygame.time.get_ticks()
        
        if not preview_only and not self.game_state == MAP_EDITOR:
            # Record game start for statistics
            stats_data["games_played"] += 1
            save_stats()
    
    def initialize_teleports(self):
        """Create random teleport destination pairs"""
        self.teleport_destinations = {}
        teleport_positions = []
        
        # Find all teleport positions
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] == TELEPORT:
                    teleport_positions.append((r, c))
        
        # Create random pairs
        random.shuffle(teleport_positions)
        for i in range(0, len(teleport_positions), 2):
            if i + 1 < len(teleport_positions):
                self.teleport_destinations[teleport_positions[i]] = teleport_positions[i+1]
                self.teleport_destinations[teleport_positions[i+1]] = teleport_positions[i]
    
    def calculate_path(self):
        """Calculate best path from agent to gold using A*"""
        if not self.agent_pos or not self.gold_pos or not self.grid:
            return []
        
        # A* algorithm implementation
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Manhattan distance
        
        def get_neighbors(pos):
            row, col = pos
            neighbors = []
            
            # Check four directions
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                r, c = row + dr, col + dc
                
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    # Check if it's a valid move
                    if self.grid[r][c] not in [OBSTACLE, WUMPUS]:
                        neighbors.append((r, c))
            
            return neighbors
        
        # Initialize A* variables
        open_set = [(0, self.agent_pos)]  # Priority queue (f_score, pos)
        came_from = {}
        g_score = {self.agent_pos: 0}
        f_score = {self.agent_pos: heuristic(self.agent_pos, self.gold_pos)}
        
        while open_set:
            _, current = min(open_set, key=lambda x: x[0])
            open_set = [x for x in open_set if x[1] != current]
            
            if current == self.gold_pos:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(self.agent_pos)
                path.reverse()
                self.path = path
                return path
            
            for neighbor in get_neighbors(current):
                # Special case for teleport - adjust g_score
                teleport_penalty = 0
                if self.grid[neighbor[0]][neighbor[1]] == TELEPORT:
                    # Add a small penalty for teleports to avoid teleport loops
                    teleport_penalty = 1
                
                tentative_g = g_score[current] + 1 + teleport_penalty
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, self.gold_pos)
                    if not any(neighbor == x[1] for x in open_set):
                        open_set.append((f_score[neighbor], neighbor))
        
        # No path found
        self.path = []
        return []
    
    def update(self):
        """Update game state"""
        if self.game_state == GAME_RUNNING and not self.paused:
            current_time = pygame.time.get_ticks()
            
            # Update game time
            if self.game_start_time > 0:
                self.game_time_elapsed = current_time - self.game_start_time
            
            # Challenge mode updates
            if self.challenge_mode and current_time > self.challenge_next_change:
                self.challenge_next_change = current_time + self.challenge_interval
                self.apply_challenge_update()
            
            # Process animations
            if self.animations:
                # Check if current animation is completed
                if not self.animation:
                    self.animation = self.animations.pop(0)
                
                if self.animation.update():
                    # Animation completed
                    if self.animation.entity_type == AGENT:
                        # Update agent position
                        new_pos = self.animation.end_pos
                        self.grid[self.agent_pos[0]][self.agent_pos[1]] = TRAIL
                        self.agent_pos = new_pos
                        
                        # Check what's at the new position
                        entity_at_pos = self.grid[new_pos[0]][new_pos[1]]
                        
                        if entity_at_pos == GOLD:
                            # Collected gold
                            self.gold_collected += 1
                            stats_data["gold_collected"] += 1
                            save_stats()
                            
                            # Add gold collection animation
                            self.animations.insert(0, Animation(new_pos, new_pos, 500, GOLD))
                            
                            # Update score
                            self.score += 1000 - self.steps_taken * 10
                            if self.score > stats_data["best_score"]:
                                stats_data["best_score"] = self.score
                                save_stats()
                                
                            # Set game win state
                            self.game_won = True
                        
                        elif entity_at_pos == WUMPUS or entity_at_pos == PIT:
                            # Game over - died
                            stats_data["deaths"] += 1
                            save_stats()
                            self.game_over = True
                        
                        elif entity_at_pos == TRAP:
                            # Trap effect - lose points
                            self.score -= 100
                            # Add trap animation
                            self.animations.insert(0, Animation(new_pos, new_pos, 500, TRAP))
                        
                        elif entity_at_pos == TELEPORT:
                            # Teleport to paired location
                            if new_pos in self.teleport_destinations:
                                dest_pos = self.teleport_destinations[new_pos]
                                # Add teleport animation
                                self.animations.insert(0, Animation(new_pos, new_pos, 500, TELEPORT))
                                # Add movement animation to destination
                                self.animations.insert(1, Animation(new_pos, dest_pos, self.animation_speed, AGENT))
                        
                        # Place agent at new position
                        self.grid[new_pos[0]][new_pos[1]] = AGENT
                        
                        # Update stats
                        self.steps_taken += 1
                        stats_data["total_steps"] += 1
                        save_stats()
                    
                    # Clear the completed animation
                    self.animation = None
                    
                    # Check for end of game
                    if self.game_over or self.game_won:
                        # Record level completion
                        if self.game_won and self.current_level:
                            level_key = self.current_level.name
                            if level_key not in stats_data["levels_completed"]:
                                stats_data["levels_completed"][level_key] = 0
                            stats_data["levels_completed"][level_key] += 1
                            
                            # Record best path
                            if self.steps_taken < stats_data["best_path_length"]:
                                stats_data["best_path_length"] = self.steps_taken
                            
                            # Add to history
                            stats_data["history"].append({
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "level": self.current_level.name,
                                "difficulty": self.current_level.difficulty,
                                "steps": self.steps_taken,
                                "score": self.score,
                                "time": self.game_time_elapsed // 1000,  # seconds
                                "result": "won" if self.game_won else "lost"
                            })
                            save_stats()
                        
                        # Save GIF if recording
                        if self.record_gif and self.gif_frames:
                            self.save_gif()
            
            # Start next animation if path exists and no current animation
            elif self.path and not self.game_over and not self.game_won:
                if len(self.path) > 1:
                    current_pos = self.path.pop(0)
                    next_pos = self.path[0]
                    self.animations.append(Animation(current_pos, next_pos, self.animation_speed, AGENT))
            
            # Capture frame for GIF if recording
            if self.record_gif:
                surface_copy = self.screen.copy()
                pygame_surface_to_pil = pygame.surfarray.array3d(surface_copy).swapaxes(0, 1)
                self.gif_frames.append(pygame_surface_to_pil)
    
    def apply_challenge_update(self):
        """Apply random changes for challenge mode"""
        change_type = random.choice(["move_wumpus", "add_pit", "add_trap"])
        
        if change_type == "move_wumpus" and self.wumpus_positions:
            # Move a random wumpus
            wumpus_pos = random.choice(self.wumpus_positions)
            self.grid[wumpus_pos[0]][wumpus_pos[1]] = EMPTY
            
            # Find a new empty position
            new_pos = self.find_empty_position()
            if new_pos:
                self.grid[new_pos[0]][new_pos[1]] = WUMPUS
                self.wumpus_positions.remove(wumpus_pos)
                self.wumpus_positions.append(new_pos)
        
        elif change_type == "add_pit":
            # Add a new pit
            new_pos = self.find_empty_position()
            if new_pos:
                self.grid[new_pos[0]][new_pos[1]] = PIT
        
        elif change_type == "add_trap":
            # Add a new trap
            new_pos = self.find_empty_position()
            if new_pos:
                self.grid[new_pos[0]][new_pos[1]] = TRAP
        
        # Recalculate path after changes
        self.calculate_path()
    
    def find_empty_position(self):
        """Find a random empty position that's not near the agent or gold"""
        safe_distance = 2  # Minimum distance from agent
        attempts = 0
        
        while attempts < 100:  # Prevent infinite loop
            row = random.randint(0, GRID_SIZE-1)
            col = random.randint(0, GRID_SIZE-1)
            
            # Check if position is empty and far enough from agent
            if (self.grid[row][col] == EMPTY and
                abs(row - self.agent_pos[0]) > safe_distance and
                abs(col - self.agent_pos[1]) > safe_distance):
                return (row, col)
            
            attempts += 1
        
        return None
    
    def save_gif(self):
        """Save recorded game as a GIF"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wumpus_game_{timestamp}.gif"
            
            if self.gif_frames:
                # Convert pygame surfaces to PIL images
                pil_frames = [pygame.surfarray.array3d(frame).swapaxes(0, 1) for frame in self.gif_frames]
                
                # Save as GIF
                imageio.mimsave(filename, pil_frames, fps=10)
                print(f"GIF saved as {filename}")
        except Exception as e:
            print(f"Error saving GIF: {e}")
        
        # Reset recording
        self.record_gif = False
        self.gif_frames = []
    
    def draw(self):
        """Draw the game based on current state"""
        self.screen = pygame.display.set_mode((GAME_SCREEN_WIDTH, HEIGHT)) if self.game_state == GAME_RUNNING else pygame.display.set_mode((WIDTH, HEIGHT))
        self.screen.fill(WHITE)
        
        if self.game_state == MAIN_MENU:
            self.draw_main_menu()
        elif self.game_state == LEVEL_SELECT:
            self.draw_level_select()
        elif self.game_state == GAME_SETUP:
            self.draw_game_setup()
        elif self.game_state == GAME_RUNNING:
            self.draw_game()
        elif self.game_state == MAP_EDITOR:
            self.draw_map_editor()
        elif self.game_state == SETTINGS:
            self.draw_settings()
        elif self.game_state == STATS_SCREEN:
            self.draw_stats()
    
    def draw_main_menu(self):
        """Draw the main menu screen"""
        # Draw title
        title_text = title_font.render("Wumpus World AI Game", True, BLACK)
        title_rect = title_text.get_rect(center=(WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw menu buttons
        for button in self.main_menu_buttons:
            button.draw(self.screen)
        
        # Draw footer
        version_text = small_font.render("v1.0 - AI Pathfinding Demo", True, BLACK)
        version_rect = version_text.get_rect(midbottom=(WIDTH//2, HEIGHT - 20))
        self.screen.blit(version_text, version_rect)
    
    def draw_level_select(self):
        """Draw the level selection screen"""
        # Draw title
        title_text = title_font.render("Select Level", True, BLACK)
        title_rect = title_text.get_rect(center=(WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Draw level buttons
        for button in self.level_buttons:
            button.draw(self.screen)
        
        # Back button
        back_button = Button(WIDTH//2 - 100, HEIGHT - 80, 200, 50, "Back", RED, MAIN_MENU)
        back_button.draw(self.screen)
        if back_button.is_clicked(pygame.mouse.get_pos()):
            self.game_state = MAIN_MENU
    
    def draw_game_setup(self):
        """Draw the game setup screen"""
        # Draw title
        title_text = title_font.render("Game Setup", True, BLACK)
        title_rect = title_text.get_rect(center=(WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Draw difficulty selector
        difficulty_label = font.render("Select Difficulty:", True, BLACK)
        self.screen.blit(difficulty_label, (WIDTH//2 - 150, 120))
        self.difficulty_dropdown.draw(self.screen)
        
        # Draw input fields
        self.agent_input.draw(self.screen)
        self.gold_input.draw(self.screen)
        
        # Draw buttons
        self.preview_button.draw(self.screen)
        self.start_button.draw(self.screen)
        self.gif_button.draw(self.screen)
        
        # Draw back button
        back_button = Button(WIDTH//2 - 100, HEIGHT - 30, 200, 30, "Back", RED, MAIN_MENU)
        back_button.draw(self.screen)
        
        # Draw preview grid if available
        if self.grid:
            # Scale down and center the grid for preview
            preview_size = min(WIDTH, HEIGHT) - 300
            tile_size = preview_size // GRID_SIZE
            offset_x = (WIDTH - GRID_SIZE * tile_size) // 2
            offset_y = 220
            
            self.draw_grid(offset_x, offset_y, tile_size)
            
            # Draw path if preview requested
            if self.show_path_preview and self.path:
                for i, pos in enumerate(self.path):
                    if i < len(self.path) - 1:
                        next_pos = self.path[i+1]
                        start_x = offset_x + pos[1] * tile_size + tile_size // 2
                        start_y = offset_y + pos[0] * tile_size + tile_size // 2
                        end_x = offset_x + next_pos[1] * tile_size + tile_size // 2
                        end_y = offset_y + next_pos[0] * tile_size + tile_size // 2
                        
                        pygame.draw.line(self.screen, BLUE, (start_x, start_y), (end_x, end_y), 3)
    
    def draw_game(self):
        """Draw the game screen with grid and UI"""
        # Draw grid
        self.draw_grid(0, 0, TILE_SIZE)
        
        # Draw sidebar background
        sidebar_rect = pygame.Rect(WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
        pygame.draw.rect(self.screen, LIGHT_BLUE, sidebar_rect)
        
        # Draw UI buttons
        for button in self.game_ui_buttons:
            button.draw(self.screen)
        
        # Draw game info
        info_y = 180
        info_texts = [
            f"Level: {self.current_level.name if self.current_level else 'Custom'}",
            f"Difficulty: {self.current_level.difficulty if self.current_level else self.difficulty}",
            f"Steps: {self.steps_taken}",
            f"Score: {self.score}",
            f"Time: {self.game_time_elapsed // 1000}s"
        ]
        
        for text in info_texts:
            text_surface = font.render(text, True, BLACK)
            self.screen.blit(text_surface, (WIDTH + 20, info_y))
            info_y += 40
        
        # Draw legend
        legend_y = info_y + 40
        legend_title = font.render("Legend:", True, BLACK)
        self.screen.blit(legend_title, (WIDTH + 20, legend_y))
        legend_y += 30
        
        legend_items = [
            (AGENT, BLUE, "Agent"),
            (GOLD, GREEN, "Gold"),
            (WUMPUS, RED, "Wumpus"),
            (PIT, BLACK, "Pit"),
            (OBSTACLE, BROWN, "Obstacle"),
            (TRAP, ORANGE, "Trap"),
            (TELEPORT, PURPLE, "Teleport")
        ]
        
        for entity, color, label in legend_items:
            pygame.draw.rect(self.screen, color, (WIDTH + 20, legend_y, 30, 30))
            pygame.draw.rect(self.screen, BLACK, (WIDTH + 20, legend_y, 30, 30), 1)
            text_surface = small_font.render(label, True, BLACK)
            self.screen.blit(text_surface, (WIDTH + 60, legend_y + 8))
            legend_y += 40
        
        # Draw path if showing preview
        if self.show_path_preview and self.path and not self.animation:
            for i, pos in enumerate(self.path):
                if i < len(self.path) - 1:
                    next_pos = self.path[i+1]
                    start_x = pos[1] * TILE_SIZE + TILE_SIZE // 2
                    start_y = pos[0] * TILE_SIZE + TILE_SIZE // 2
                    end_x = next_pos[1] * TILE_SIZE + TILE_SIZE // 2
                    end_y = next_pos[0] * TILE_SIZE + TILE_SIZE // 2
                    
                    pygame.draw.line(self.screen, BLUE, (start_x, start_y), (end_x, end_y), 3)
        
        # Draw current animation
        if self.animation:
            self.animation.draw(self.screen)
        
        # Draw game over / won message
        if self.game_over or self.game_won:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            if self.game_won:
                message = "You Won!"
                color = GREEN
            else:
                message = "Game Over"
                color = RED
                
            text = title_font.render(message, True, color)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
            self.screen.blit(text, text_rect)
            
            score_text = font.render(f"Score: {self.score}   Steps: {self.steps_taken}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(score_text, score_rect)
            
            # Draw next level button if won
            if self.game_won and self.current_level:
                    next_level_index = min(self.current_level_index + 1, len(self.levels) - 1)
                    next_button = Button(WIDTH//2 - 150, HEIGHT//2 + 50, 300, 50, 
                                      f"Next Level: {self.levels[next_level_index].name}", GREEN)
                    next_button.draw(self.screen)
                    
                    if pygame.mouse.get_pressed()[0] and next_button.is_clicked(pygame.mouse.get_pos()):
                        self.current_level_index = next_level_index
                        self.current_level = self.levels[next_level_index]
                        self.initialize_game()
    
    def draw_map_editor(self):
        """Draw the map editor screen"""
        # Draw title
        title_text = title_font.render("Map Editor", True, BLACK)
        title_rect = title_text.get_rect(center=(WIDTH//2, 30))
        self.screen.blit(title_text, title_rect)
        
        # Draw grid
        self.draw_grid(0, 0, TILE_SIZE)
        
        # Draw palette
        palette_text = font.render("Tile Palette:", True, BLACK)
        self.screen.blit(palette_text, (20, HEIGHT - 230))
        
        for button in self.map_editor_palette:
            button.draw(self.screen)
            
            # Highlight selected tile
            if button.action == self.map_editor_selected_tile:
                pygame.draw.rect(self.screen, BLUE, button.rect, 3)
        
        # Draw action buttons
        for button in self.map_editor_buttons:
            button.draw(self.screen)
        
        # Draw instructions
        info_text = small_font.render("Click on the grid to place selected tile type", True, BLACK)
        self.screen.blit(info_text, (20, HEIGHT - 170))
        
        # Draw teleport connections if any
        for pos, dest in self.teleport_destinations.items():
            start_x = pos[1] * TILE_SIZE + TILE_SIZE // 2
            start_y = pos[0] * TILE_SIZE + TILE_SIZE // 2
            end_x = dest[1] * TILE_SIZE + TILE_SIZE // 2
            end_y = dest[0] * TILE_SIZE + TILE_SIZE // 2
            
            pygame.draw.line(self.screen, PURPLE, (start_x, start_y), (end_x, end_y), 2)
    
    def draw_settings(self):
        """Draw the settings screen"""
        # Draw title
        title_text = title_font.render("Game Settings", True, BLACK)
        title_rect = title_text.get_rect(center=(WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Draw settings options
        option_y = 180
        
        # Animation speed setting
        speed_text = font.render(f"Animation Speed: {self.animation_speed}ms", True, BLACK)
        self.screen.blit(speed_text, (WIDTH//4, option_y))
        
        speed_faster = Button(WIDTH//2, option_y, 100, 40, "Faster", GREEN)
        speed_slower = Button(WIDTH//2 + 110, option_y, 100, 40, "Slower", RED)
        
        speed_faster.draw(self.screen)
        speed_slower.draw(self.screen)
        
        if pygame.mouse.get_pressed()[0]:
            pos = pygame.mouse.get_pos()
            if speed_faster.is_clicked(pos):
                self.animation_speed = max(100, self.animation_speed - 50)
            elif speed_slower.is_clicked(pos):
                self.animation_speed = min(1000, self.animation_speed + 50)
        
        option_y += 80
        
        # Path preview toggle
        preview_text = font.render("Show Path Preview:", True, BLACK)
        self.screen.blit(preview_text, (WIDTH//4, option_y))
        
        preview_on = Button(WIDTH//2, option_y, 100, 40, "On", GREEN if self.show_path_preview else GRAY)
        preview_off = Button(WIDTH//2 + 110, option_y, 100, 40, "Off", RED if not self.show_path_preview else GRAY)
        
        preview_on.draw(self.screen)
        preview_off.draw(self.screen)
        
        if pygame.mouse.get_pressed()[0]:
            pos = pygame.mouse.get_pos()
            if preview_on.is_clicked(pos):
                self.show_path_preview = True
            elif preview_off.is_clicked(pos):
                self.show_path_preview = False
        
        option_y += 80
        
        # Challenge mode difficulty
        challenge_text = font.render("Challenge Interval:", True, BLACK)
        self.screen.blit(challenge_text, (WIDTH//4, option_y))
        
        interval_easy = Button(WIDTH//2 - 120, option_y, 100, 40, "Easy", GREEN if self.challenge_interval == 20000 else GRAY)
        interval_medium = Button(WIDTH//2, option_y, 100, 40, "Medium", GREEN if self.challenge_interval == 10000 else GRAY)
        interval_hard = Button(WIDTH//2 + 120, option_y, 100, 40, "Hard", GREEN if self.challenge_interval == 5000 else GRAY)
        
        interval_easy.draw(self.screen)
        interval_medium.draw(self.screen)
        interval_hard.draw(self.screen)
        
        if pygame.mouse.get_pressed()[0]:
            pos = pygame.mouse.get_pos()
            if interval_easy.is_clicked(pos):
                self.challenge_interval = 20000  # 20 seconds
            elif interval_medium.is_clicked(pos):
                self.challenge_interval = 10000  # 10 seconds
            elif interval_hard.is_clicked(pos):
                self.challenge_interval = 5000   # 5 seconds
        
        # Back button
        back_button = Button(WIDTH//2 - 100, HEIGHT - 80, 200, 50, "Back", RED, MAIN_MENU)
        back_button.draw(self.screen)
        
        if pygame.mouse.get_pressed()[0] and back_button.is_clicked(pygame.mouse.get_pos()):
            self.game_state = MAIN_MENU
    
    def draw_stats(self):
        """Draw the statistics screen"""
        # Draw title
        title_text = title_font.render("Game Statistics", True, BLACK)
        title_rect = title_text.get_rect(center=(WIDTH//2, 50))
        self.screen.blit(title_text, title_rect)
        
        stats_y = 120
        
        # Draw global stats
        global_stats = [
            f"Games Played: {stats_data['games_played']}",
            f"Gold Collected: {stats_data['gold_collected']}",
            f"Total Steps: {stats_data['total_steps']}",
            f"Deaths: {stats_data['deaths']}",
            f"Best Path Length: {stats_data['best_path_length'] if stats_data['best_path_length'] != float('inf') else 'N/A'}",
            f"Best Score: {stats_data['best_score']}"
        ]
        
        # Draw left column - global stats
        for stat in global_stats:
            text = font.render(stat, True, BLACK)
            self.screen.blit(text, (50, stats_y))
            stats_y += 40
        
        # Draw right column - level completions
        level_stats_x = WIDTH // 2 + 50
        level_stats_y = 120
        
        level_title = font.render("Level Completions:", True, BLACK)
        self.screen.blit(level_title, (level_stats_x, level_stats_y))
        level_stats_y += 40
        
        if stats_data["levels_completed"]:
            for level, count in stats_data["levels_completed"].items():
                text = small_font.render(f"{level}: {count}", True, BLACK)
                self.screen.blit(text, (level_stats_x, level_stats_y))
                level_stats_y += 30
        else:
            text = small_font.render("No levels completed yet", True, BLACK)
            self.screen.blit(text, (level_stats_x, level_stats_y))
        
        # Draw recent history
        history_y = 350
        history_title = font.render("Recent Games:", True, BLACK)
        self.screen.blit(history_title, (50, history_y))
        history_y += 40
        
        column_headers = ["Date", "Level", "Difficulty", "Steps", "Score", "Time", "Result"]
        column_widths = [150, 100, 80, 60, 70, 50, 70]
        column_x = 50
        
        # Draw headers
        for header, width in zip(column_headers, column_widths):
            text = small_font.render(header, True, BLACK)
            self.screen.blit(text, (column_x, history_y))
            column_x += width
        
        history_y += 30
        
        # Draw recent games (last 5)
        recent_games = stats_data["history"][-5:] if stats_data["history"] else []
        for game in recent_games:
            column_x = 50
            for i, key in enumerate(["date", "level", "difficulty", "steps", "score", "time", "result"]):
                value = str(game.get(key, ""))
                text = tiny_font.render(value, True, BLACK)
                self.screen.blit(text, (column_x, history_y))
                column_x += column_widths[i]
            history_y += 25
        
        # Draw back button
        self.stats_back_button.draw(self.screen)
        
        if pygame.mouse.get_pressed()[0] and self.stats_back_button.is_clicked(pygame.mouse.get_pos()):
            self.game_state = MAIN_MENU
    
    def draw_grid(self, offset_x, offset_y, tile_size):
        """Draw the game grid with all entities"""
        if not self.grid:
            return
        
        for row in range(len(self.grid)):
            for col in range(len(self.grid[row])):
                # Calculate tile position
                x = offset_x + col * tile_size
                y = offset_y + row * tile_size
                
                # Draw tile background
                pygame.draw.rect(self.screen, WHITE, (x, y, tile_size, tile_size))
                pygame.draw.rect(self.screen, BLACK, (x, y, tile_size, tile_size), 1)
                
                # Draw entity based on grid value
                entity = self.grid[row][col]
                
                if entity == AGENT:
                    pygame.draw.circle(self.screen, BLUE, (x + tile_size//2, y + tile_size//2), tile_size//3)
                
                elif entity == GOLD:
                    pygame.draw.circle(self.screen, GREEN, (x + tile_size//2, y + tile_size//2), tile_size//3)
                    
                    # Draw dollar sign
                    dollar_text = font.render("$", True, BLACK)
                    dollar_rect = dollar_text.get_rect(center=(x + tile_size//2, y + tile_size//2))
                    self.screen.blit(dollar_text, dollar_rect)
                
                elif entity == WUMPUS:
                    # Draw wumpus as a red triangle
                    pygame.draw.polygon(self.screen, RED, [
                        (x + tile_size//2, y + tile_size//5),
                        (x + tile_size//5, y + tile_size*4//5),
                        (x + tile_size*4//5, y + tile_size*4//5)
                    ])
                
                elif entity == PIT:
                    # Draw pit as a black circle
                    pygame.draw.circle(self.screen, BLACK, (x + tile_size//2, y + tile_size//2), tile_size//3)
                
                elif entity == OBSTACLE:
                    # Draw obstacle as a brown rectangle
                    pygame.draw.rect(self.screen, BROWN, (x + tile_size//5, y + tile_size//5, 
                                                       tile_size*3//5, tile_size*3//5))
                
                elif entity == TRAP:
                    # Draw trap as an orange X
                    pygame.draw.line(self.screen, ORANGE, (x + tile_size//5, y + tile_size//5), 
                                   (x + tile_size*4//5, y + tile_size*4//5), tile_size//10)
                    pygame.draw.line(self.screen, ORANGE, (x + tile_size*4//5, y + tile_size//5), 
                                   (x + tile_size//5, y + tile_size*4//5), tile_size//10)
                
                elif entity == TELEPORT:
                    # Draw teleport as a purple circle
                    pygame.draw.circle(self.screen, PURPLE, (x + tile_size//2, y + tile_size//2), tile_size//3, 5)
                    
                    # Draw inner circle
                    pygame.draw.circle(self.screen, PURPLE, (x + tile_size//2, y + tile_size//2), tile_size//6)
                
                elif entity == TRAIL:
                    # Draw trail as a light blue dot
                    pygame.draw.circle(self.screen, LIGHT_BLUE, (x + tile_size//2, y + tile_size//2), tile_size//6)

# Run the game
if __name__ == "__main__":
    game_manager = GameManager()
    game_manager.run()
                        