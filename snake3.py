import pygame
import random
import imageio
from collections import deque

# Constants
WIDTH, HEIGHT = 400, 400
GRID_SIZE = 20
WHITE, BLACK, BLUE, GREEN, RED, GRAY = (255, 255, 255), (0, 0, 0), (0, 0, 255), (0, 255, 0), (255, 0, 0), (200, 200, 200)
DIRECTIONS = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}

class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("AI Snake Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.running, self.paused, self.started = False, False, False
        self.welcome_screen = True
        self.preview_mode = False
        self.moves = []
        self.snake_color = GREEN
        self.food_color = RED
        self.default_start = (WIDTH // 2, HEIGHT // 2)
        self.snake_start = self.default_start
        self.food_start = (random.randint(0, WIDTH // GRID_SIZE - 1) * GRID_SIZE,
                           random.randint(0, HEIGHT // GRID_SIZE - 1) * GRID_SIZE)
        self.color_input = "(0, 255, 0)"  # Default green
        self.position_input = f"({self.default_start[0]}, {self.default_start[1]})"
        self.error_message = ""
        self.reset()

    def reset(self):
        self.snake = [self.snake_start]
        self.food = self.food_start
        self.direction = 'RIGHT'
        self.moves.clear()
        self.error_message = ""

    def draw_button(self, text, x, y, width, height, color, disabled=False):
        rect = pygame.Rect(x, y, width, height)
        button_color = GRAY if disabled else color
        pygame.draw.rect(self.screen, button_color, rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, rect, 3, border_radius=10)
        text_surf = self.font.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(text_surf, text_rect)
        return rect

    def draw_textbox(self, label, text, x, y, width, height):
        pygame.draw.rect(self.screen, GRAY, (x, y, width, height), border_radius=5)
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2, border_radius=5)
        text_surf = self.font.render(text, True, BLACK)
        label_surf = self.font.render(label, True, WHITE)
        self.screen.blit(label_surf, (x, y - 25))
        self.screen.blit(text_surf, (x + 5, y + 5))
        return pygame.Rect(x, y, width, height)

    def draw_welcome_screen(self):
        # Title
        title = self.font.render("AI Snake Game", True, WHITE)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))
        
        # Input boxes
        color_box = self.draw_textbox("Snake Color (RGB):", self.color_input, 100, 100, 200, 30)
        position_box = self.draw_textbox("Start Position (x,y):", self.position_input, 100, 150, 200, 30)
        
        # Buttons
        preview_button = self.draw_button("Preview", 80, 200, 100, 40, BLUE)
        start_button = self.draw_button("Start Game", 220, 200, 100, 40, GREEN)
        
        # Preview area
        if self.preview_mode:
            pygame.draw.rect(self.screen, BLACK, (50, 250, 300, 120), border_radius=10)
            pygame.draw.rect(self.screen, WHITE, (50, 250, 300, 120), 2, border_radius=10)
            preview_title = self.small_font.render("Preview:", True, WHITE)
            self.screen.blit(preview_title, (60, 260))
            
            # Display a miniature version of the game board
            board_rect = pygame.Rect(100, 280, 200, 80)
            pygame.draw.rect(self.screen, BLACK, board_rect)
            pygame.draw.rect(self.screen, WHITE, board_rect, 1)
            
            # Calculate scaled positions for preview
            scale_x = 200 / WIDTH
            scale_y = 80 / HEIGHT
            
            try:
                snake_pos = eval(self.position_input)
                snake_preview_x = 100 + int(snake_pos[0] * scale_x)
                snake_preview_y = 280 + int(snake_pos[1] * scale_y)
                pygame.draw.rect(self.screen, self.snake_color, 
                                (snake_preview_x, snake_preview_y, 
                                 max(5, int(GRID_SIZE * scale_x)), 
                                 max(5, int(GRID_SIZE * scale_y))))
                
                food_preview_x = 100 + int(self.food_start[0] * scale_x)
                food_preview_y = 280 + int(self.food_start[1] * scale_y)
                pygame.draw.rect(self.screen, self.food_color, 
                                (food_preview_x, food_preview_y, 
                                 max(5, int(GRID_SIZE * scale_x)), 
                                 max(5, int(GRID_SIZE * scale_y))))
            except:
                error_text = self.small_font.render("Invalid position format", True, RED)
                self.screen.blit(error_text, (110, 310))
        
        # Error message
        if self.error_message:
            error_text = self.small_font.render(self.error_message, True, RED)
            self.screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, 370))
        
        return color_box, position_box, preview_button, start_button

    def validate_inputs(self):
        try:
            # Validate color
            color = eval(self.color_input)
            if (not isinstance(color, tuple) or len(color) != 3 or 
                not all(isinstance(c, int) and 0 <= c <= 255 for c in color)):
                self.error_message = "Invalid color format. Use (R,G,B) with values 0-255."
                return False
            
            # Validate position
            pos = eval(self.position_input)
            if (not isinstance(pos, tuple) or len(pos) != 2 or 
                not all(isinstance(p, int) for p in pos) or
                not (0 <= pos[0] < WIDTH and 0 <= pos[1] < HEIGHT)):
                self.error_message = "Invalid position. Must be within game bounds."
                return False
                
            # Align to grid
            aligned_pos = (pos[0] - pos[0] % GRID_SIZE, pos[1] - pos[1] % GRID_SIZE)
            if pos != aligned_pos:
                self.position_input = str(aligned_pos)
                self.error_message = "Position adjusted to align with grid."
            else:
                self.error_message = ""
                
            self.snake_color = color
            self.snake_start = aligned_pos
            return True
        except:
            self.error_message = "Invalid input format. Check your syntax."
            return False

    def move_snake(self):
        if self.snake and self.direction:
            head_x, head_y = self.snake[0]
            move_x, move_y = DIRECTIONS[self.direction]
            new_head = (head_x + move_x * GRID_SIZE, head_y + move_y * GRID_SIZE)
            
            if new_head in self.snake or not (0 <= new_head[0] < WIDTH and 0 <= new_head[1] < HEIGHT):
                self.running = False
                return
            
            self.snake.insert(0, new_head)
            if new_head == self.food:
                self.food = (random.randint(0, WIDTH // GRID_SIZE - 1) * GRID_SIZE,
                             random.randint(0, HEIGHT // GRID_SIZE - 1) * GRID_SIZE)
            else:
                self.snake.pop()
            
            self.moves.append(self.screen.copy())

    def bfs_search(self):
        queue = deque([(self.snake[0], [])])
        visited = set()
        while queue:
            (x, y), path = queue.popleft()
            if (x, y) == self.food:
                return path
            for d in DIRECTIONS:
                nx, ny = x + DIRECTIONS[d][0] * GRID_SIZE, y + DIRECTIONS[d][1] * GRID_SIZE
                if (nx, ny) not in visited and 0 <= nx < WIDTH and 0 <= ny < HEIGHT and (nx, ny) not in self.snake:
                    queue.append(((nx, ny), path + [d]))
                    visited.add((nx, ny))
        return []

    def run(self):
        active_input = None
        while True:
            self.screen.fill(BLACK)
            
            if self.welcome_screen:
                color_box, position_box, preview_button, start_button = self.draw_welcome_screen()
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if color_box.collidepoint(event.pos):
                            active_input = 'color'
                        elif position_box.collidepoint(event.pos):
                            active_input = 'position'
                        elif preview_button.collidepoint(event.pos):
                            if self.validate_inputs():
                                self.preview_mode = True
                        elif start_button.collidepoint(event.pos):
                            if self.validate_inputs():
                                self.welcome_screen = False
                                self.started = True
                                self.running = True
                                self.reset()
                    elif event.type == pygame.KEYDOWN and active_input:
                        if event.key == pygame.K_RETURN:
                            active_input = None
                            self.validate_inputs()
                        elif event.key == pygame.K_BACKSPACE:
                            if active_input == 'color':
                                self.color_input = self.color_input[:-1]
                            elif active_input == 'position':
                                self.position_input = self.position_input[:-1]
                        else:
                            if active_input == 'color':
                                self.color_input += event.unicode
                            elif active_input == 'position':
                                self.position_input += event.unicode
            
            elif self.started:
                # Draw game elements
                pygame.draw.rect(self.screen, self.food_color, (*self.food, GRID_SIZE, GRID_SIZE))
                for segment in self.snake:
                    pygame.draw.rect(self.screen, self.snake_color, (*segment, GRID_SIZE, GRID_SIZE))
                
                # Handle game events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.save_gif()
                        pygame.quit()
                        return
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.paused = not self.paused
                        elif event.key == pygame.K_ESCAPE:
                            self.welcome_screen = True
                            self.started = False
                
                # Update game state
                if self.running and not self.paused:
                    path = self.bfs_search()
                    if path:
                        self.direction = path[0]
                    self.move_snake()
                
                # Draw game status
                if not self.running:
                    game_over = self.font.render("Game Over", True, WHITE)
                    restart = self.small_font.render("Press ESC to return to menu", True, WHITE)
                    self.screen.blit(game_over, (WIDTH // 2 - game_over.get_width() // 2, HEIGHT // 2 - 20))
                    self.screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 20))
                elif self.paused:
                    paused_text = self.font.render("Paused", True, WHITE)
                    self.screen.blit(paused_text, (WIDTH // 2 - paused_text.get_width() // 2, HEIGHT // 2))
            
            pygame.display.flip()
            self.clock.tick(10)

    def save_gif(self):
        if self.moves:
            images = [pygame.surfarray.array3d(surface).swapaxes(0, 1) for surface in self.moves]
            imageio.mimsave("snake_replay.gif", images, duration=0.1)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()