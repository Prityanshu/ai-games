import sys
import random
import math
import os
import json
from collections import deque
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                           QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLineEdit, QComboBox, QStackedWidget, QFrame)
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath, QPolygon
from PyQt6.QtCore import Qt, QRect, QPoint, QTimer, pyqtSignal, QSize

# Constants for the game grid
GRID_SIZE = 10  # 10x10 grid
TILE_SIZE = 80  # Tile size
WIDTH, HEIGHT = GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
SIDEBAR_WIDTH = 300
GAME_SCREEN_WIDTH = WIDTH + SIDEBAR_WIDTH

# Game states - using integers for the StackedWidget indices
# Screen indexes
MAIN_MENU = 0
LEVEL_SELECT = 1
GAME_RUNNING = 2
MAP_EDITOR = 3
SETTINGS = 4
STATS = 5
LEVEL_SELECT = 6

# Entities
AGENT = "A"
WUMPUS = "W"
GOLD = "G"
PIT = "P"
EMPTY = "_"
TRAIL = "T"
OBSTACLE = "O"
TRAP = "X"
TELEPORT = "TP"

# Colors - Convert pygame colors to QColor
WHITE = QColor(255, 255, 255)
BLACK = QColor(0, 0, 0)
GREEN = QColor(0, 255, 0)
DARK_GREEN = QColor(0, 150, 0)
RED = QColor(255, 0, 0)
BLUE = QColor(0, 0, 255)
GRAY = QColor(200, 200, 200)
LIGHT_BLUE = QColor(173, 216, 230)
YELLOW = QColor(255, 255, 0)
LIGHT_GREEN = QColor(144, 238, 144)
PURPLE = QColor(128, 0, 128)
ORANGE = QColor(255, 165, 0)
BROWN = QColor(139, 69, 19)

# Difficulty settings
DIFFICULTY_SETTINGS = {
    "Easy": {"wumpus": 1, "pits": 5, "obstacles": 1, "traps": 0, "teleports": 0},
    "Medium": {"wumpus": 2, "pits": 8, "obstacles": 3, "traps": 1, "teleports": 0},
    "Hard": {"wumpus": 3, "pits": 10, "obstacles": 5, "traps": 2, "teleports": 1},
    "Expert": {"wumpus": 4, "pits": 12, "obstacles": 7, "traps": 3, "teleports": 2}
}

# Custom button class with hover effect
class StyledButton(QPushButton):
    def __init__(self, text, color, action=None, parent=None):
        super().__init__(text, parent)
        self.base_color = QColor(color)
        self.hover_color = QColor(
            min(color.red() + 30, 255),
            min(color.green() + 30, 255),
            min(color.blue() + 30, 255)
        )
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({color.red()}, {color.green()}, {color.blue()});
                border: 2px solid black;
                border-radius: 5px;
                padding: 5px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: rgb({self.hover_color.red()}, {self.hover_color.green()}, {self.hover_color.blue()});
            }}
            QPushButton:pressed {{
                background-color: rgb({color.red()-20 if color.red()>20 else 0}, 
                                      {color.green()-20 if color.green()>20 else 0}, 
                                      {color.blue()-20 if color.blue()>20 else 0});
            }}
            QPushButton:disabled {{
                background-color: rgb(150, 150, 150);
            }}
        """)
        self.setMinimumHeight(40)
        self.action = action
        
class Animation:
    def __init__(self, start_pos, end_pos, duration=300, entity_type=AGENT):
        self.start_pos = start_pos  # Grid position (row, col)
        self.end_pos = end_pos      # Grid position (row, col)
        self.duration = duration
        self.start_time = QTimer()
        self.start_time.start(duration)
        self.elapsed = 0
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
                'elapsed': 0
            })
    
    def update(self, delta_time):
        # Update elapsed time
        self.elapsed += delta_time
        
        if self.elapsed >= self.duration:
            self.completed = True
            return True
        
        # Update particle effects
        for particle in self.particles:
            particle['elapsed'] += delta_time
            if particle['elapsed'] > particle['lifetime']:
                self.particles.remove(particle)
                continue
                
            # Update particle position
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            
        return False
        
    def draw(self, painter):
        progress = min(self.elapsed / self.duration, 1.0)
        
        # Calculate current position with easing
        eased_progress = self.ease_out_quad(progress)
        current_x = self.start_pixel[0] + (self.end_pixel[0] - self.start_pixel[0]) * eased_progress
        current_y = self.start_pixel[1] + (self.end_pixel[1] - self.start_pixel[1]) * eased_progress
        
        # Draw based on entity type
        if self.entity_type == AGENT:
            # Agent animation - blue circle with smooth movement
            painter.setBrush(QBrush(BLUE))
            size = TILE_SIZE // 3 * (1 + 0.2 * math.sin(progress * math.pi))
            painter.drawEllipse(int(current_x - size/2), int(current_y - size/2), int(size), int(size))
            
            # Draw a direction indicator
            dir_x = self.end_pixel[0] - self.start_pixel[0]
            dir_y = self.end_pixel[1] - self.start_pixel[1]
            if dir_x != 0 or dir_y != 0:
                norm = math.sqrt(dir_x**2 + dir_y**2)
                dir_x, dir_y = dir_x/norm, dir_y/norm
                painter.setPen(QPen(BLACK, 3))
                painter.drawLine(
                    QPoint(int(current_x), int(current_y)),
                    QPoint(int(current_x + dir_x * TILE_SIZE//4), int(current_y + dir_y * TILE_SIZE//4))
                )
        
        elif self.entity_type == GOLD:
            # Gold collection animation - particles and a shrinking gold circle
            # Draw particles
            for particle in self.particles:
                painter.setBrush(QBrush(particle['color']))
                painter.setPen(Qt.PenStyle.NoPen)
                fade_factor = 1 - (particle['elapsed'] / particle['lifetime'])
                color = QColor(particle['color'])
                color.setAlpha(int(255 * fade_factor))
                painter.setBrush(QBrush(color))
                size = int(particle['size'])
                painter.drawEllipse(
                    int(particle['pos'][0] - size/2),
                    int(particle['pos'][1] - size/2),
                    size, size
                )
            
            # Draw shrinking gold
            if progress < 0.7:  # Only show during first part of animation
                size_factor = 1 - progress/0.7
                painter.setBrush(QBrush(GREEN))
                painter.setPen(Qt.PenStyle.NoPen)
                size = int(TILE_SIZE // 3 * size_factor)
                painter.drawEllipse(
                    int(current_x - size/2),
                    int(current_y - size/2),
                    size, size
                )
                
        elif self.entity_type == TRAP:
            # Trap animation - red flash
            flash_intensity = math.sin(progress * math.pi * 8)  # Quick flashing
            flash_color = QColor(
                255, 
                max(0, int(255 * (1-flash_intensity))), 
                max(0, int(255 * (1-flash_intensity)))
            )
            painter.setBrush(QBrush(flash_color))
            painter.setPen(Qt.PenStyle.NoPen)
            rect_size = TILE_SIZE // 1.5
            painter.drawRect(
                int(current_x - rect_size/2),
                int(current_y - rect_size/2),
                int(rect_size),
                int(rect_size)
            )
            
        elif self.entity_type == TELEPORT:
            # Teleport animation - circular ripple effect
            painter.setPen(QPen(PURPLE))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for i in range(3):
                ripple_progress = (progress + i/3) % 1.0
                radius = TILE_SIZE//2 * ripple_progress
                width = max(1, int(TILE_SIZE//10 * (1 - ripple_progress)))
                painter.setPen(QPen(PURPLE, width))
                painter.drawEllipse(
                    int(current_x - radius),
                    int(current_y - radius),
                    int(radius * 2),
                    int(radius * 2)
                )
    
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

# Game grid widget for rendering
class GameGridWidget(QWidget):
    tileClicked = pyqtSignal(int, int)  # Signal for when a tile is clicked (row, col)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = None
        self.agent_pos = None
        self.gold_pos = None
        self.path = []
        self.animations = []
        self.teleport_destinations = {}
        self.show_path_preview = True
        
        self.setFixedSize(WIDTH, HEIGHT)
    
    def set_grid(self, grid, agent_pos, gold_pos):
        self.grid = grid
        self.agent_pos = agent_pos
        self.gold_pos = gold_pos
        self.update()
    
    def set_path(self, path):
        self.path = path
        self.update()
    
    def add_animation(self, animation):
        self.animations.append(animation)
    
    def clear_animations(self):
        self.animations = []
    
    def update_animations(self, delta_time):
        # Update all animations
        completed = []
        for anim in self.animations:
            if anim.update(delta_time):
                completed.append(anim)
        
        # Remove completed animations
        for anim in completed:
            self.animations.remove(anim)
        
        # Request repaint if any animations are active
        if self.animations:
            self.update()
            
        return len(completed) > 0
    
    def mousePressEvent(self, event):
        if self.grid is None:
            return
            
        # Calculate grid position from mouse click
        col = event.position().x() // TILE_SIZE
        row = event.position().y() // TILE_SIZE
        
        if 0 <= row < len(self.grid) and 0 <= col < len(self.grid[0]):
            self.tileClicked.emit(int(row), int(col))
    
    def paintEvent(self, event):
        if self.grid is None:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw grid
        for row in range(len(self.grid)):
            for col in range(len(self.grid[0])):
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                
                # Draw tile background
                tile_type = self.grid[row][col]
                
                if tile_type == EMPTY:
                    painter.setBrush(QBrush(WHITE))
                elif tile_type == AGENT:
                    painter.setBrush(QBrush(BLUE))
                elif tile_type == WUMPUS:
                    painter.setBrush(QBrush(RED))
                elif tile_type == GOLD:
                    painter.setBrush(QBrush(GREEN))
                elif tile_type == PIT:
                    painter.setBrush(QBrush(BLACK))
                elif tile_type == OBSTACLE:
                    painter.setBrush(QBrush(BROWN))
                elif tile_type == TRAP:
                    painter.setBrush(QBrush(ORANGE))
                elif tile_type == TELEPORT:
                    painter.setBrush(QBrush(PURPLE))
                elif tile_type == TRAIL:
                    painter.setBrush(QBrush(LIGHT_BLUE))
                
                painter.setPen(QPen(BLACK, 1))
                painter.drawRect(x, y, TILE_SIZE, TILE_SIZE)
                
                # Draw entity symbols
                if tile_type != EMPTY:
                    painter.setPen(QPen(BLACK, 2))
                    text_rect = QRect(x, y, TILE_SIZE, TILE_SIZE)
                    
                    if tile_type == AGENT:
                        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "A")
                    elif tile_type == WUMPUS:
                        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "W")
                    elif tile_type == GOLD:
                        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "G")
                    elif tile_type == PIT:
                        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "P")
                    elif tile_type == OBSTACLE:
                        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "O")
                    elif tile_type == TRAP:
                        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "X")
                    elif tile_type == TELEPORT:
                        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "TP")
        
        # Draw path preview if enabled
        if self.show_path_preview and self.path:
            path_color = QColor(255, 255, 0, 128)  # Semi-transparent yellow
            painter.setPen(QPen(path_color, 3))
            
            for i in range(len(self.path) - 1):
                start_row, start_col = self.path[i]
                end_row, end_col = self.path[i + 1]
                
                start_x = start_col * TILE_SIZE + TILE_SIZE // 2
                start_y = start_row * TILE_SIZE + TILE_SIZE // 2
                end_x = end_col * TILE_SIZE + TILE_SIZE // 2
                end_y = end_row * TILE_SIZE + TILE_SIZE // 2
                
                painter.drawLine(start_x, start_y, end_x, end_y)
                
                # Draw a small circle at each path point
                painter.setBrush(QBrush(path_color))
                painter.drawEllipse(start_x - 5, start_y - 5, 10, 10)
            
            # Draw last point
            if self.path:
                last_row, last_col = self.path[-1]
                last_x = last_col * TILE_SIZE + TILE_SIZE // 2
                last_y = last_row * TILE_SIZE + TILE_SIZE // 2
                painter.drawEllipse(last_x - 5, last_y - 5, 10, 10)
        
        # Draw animations on top
        for animation in self.animations:
            animation.draw(painter)

# Main menu screen
# Main Menu Screen
class MainMenuScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title = QLabel("Wumpus AI Game")
        title.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(30)
        
        # Buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.playButton = StyledButton("Play Game", GREEN, LEVEL_SELECT)
        self.mapEditorButton = StyledButton("Map Editor", BLUE, MAP_EDITOR)
        self.statsButton = StyledButton("Statistics", YELLOW, STATS)
        self.settingsButton = StyledButton("Settings", GRAY, SETTINGS)
        self.quitButton = StyledButton("Quit", RED)
        
        for button in [self.playButton, self.mapEditorButton, self.statsButton, self.settingsButton, self.quitButton]:
            buttons_layout.addWidget(button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

# Level selection screen
class LevelSelectScreen(QWidget):
    def __init__(self, levels, parent=None):
        super().__init__(parent)
        self.levels = levels
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title = QLabel("Select Level")
        title.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(30)
        
        # Level buttons
        self.level_buttons = []
        button_width = 300
        
        for level in self.levels:
            btn = StyledButton(f"{level.name} ({level.difficulty})", GREEN)
            btn.setFixedWidth(button_width)
            layout.addWidget(btn)
            layout.addSpacing(10)
            self.level_buttons.append(btn)
        
        layout.addSpacing(20)
        
        # Back button
        self.backButton = StyledButton("Back to Main Menu", RED, MAIN_MENU)
        self.backButton.setFixedWidth(button_width)
        layout.addWidget(self.backButton)
        
        self.setLayout(layout)

# Game screen with sidebar
class GameScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Game grid widget
        self.gridWidget = GameGridWidget()
        layout.addWidget(self.gridWidget)
        
        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout()
        
        # Game info labels
        self.levelLabel = QLabel("Level: Tutorial")
        self.scoreLabel = QLabel("Score: 0")
        self.stepsLabel = QLabel("Steps: 0")
        self.timeLabel = QLabel("Time: 00:00")
        
        for label in [self.levelLabel, self.scoreLabel, self.stepsLabel, self.timeLabel]:
            label.setFont(QFont("Arial", 14))
            sidebar_layout.addWidget(label)
        
        sidebar_layout.addSpacing(20)
        
        # Game control buttons
        self.pauseButton = StyledButton("Pause/Resume", GRAY)
        self.restartButton = StyledButton("Restart Level", YELLOW)
        self.menuButton = StyledButton("Main Menu", RED, MAIN_MENU)
        
        for button in [self.pauseButton, self.restartButton, self.menuButton]:
            sidebar_layout.addWidget(button)
            sidebar_layout.addSpacing(10)
        
        sidebar_layout.addStretch()
        
        # Game message box
        self.messageBox = QLabel("Find the gold while avoiding dangers!")
        self.messageBox.setWordWrap(True)
        self.messageBox.setFont(QFont("Arial", 12))
        self.messageBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.messageBox.setFrameShape(QFrame.Shape.Box)
        self.messageBox.setFrameShadow(QFrame.Shadow.Sunken)
        self.messageBox.setLineWidth(2)
        self.messageBox.setMinimumHeight(100)
        sidebar_layout.addWidget(self.messageBox)
        
        self.sidebar.setLayout(sidebar_layout)
        layout.addWidget(self.sidebar)
        
        self.setLayout(layout)
        
        # Animation timer
        self.animationTimer = QTimer()
        self.animationTimer.setInterval(16)  # ~60 fps
        self.animationTimer.timeout.connect(self.update_animations)
        self.last_update_time = datetime.now()
        
    def start_animation_timer(self):
        self.last_update_time = datetime.now()
        self.animationTimer.start()
    
    def stop_animation_timer(self):
        self.animationTimer.stop()
    
    def update_animations(self):
        current_time = datetime.now()
        delta_time = (current_time - self.last_update_time).total_seconds() * 1000  # Convert to ms
        self.last_update_time = current_time
        
        # Update animations in the grid widget
        self.gridWidget.update_animations(delta_time)

# Map editor screen
class MapEditorScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title and message box
        title_layout = QVBoxLayout()
        
        title = QLabel("Map Editor")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title)
        
        self.message_box = QLabel("Create your own Wumpus World!")
        self.message_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_box.setFont(QFont("Arial", 14))
        title_layout.addWidget(self.message_box)
        
        layout.addLayout(title_layout)
        
        # Grid layout
        grid_layout = QHBoxLayout()
        
        # Game grid widget
        self.gridWidget = GameGridWidget()
        self.gridWidget.tileClicked.connect(self.handle_tile_click)
        grid_layout.addWidget(self.gridWidget)
        
        # Tool palette
        palette_layout = QVBoxLayout()
        palette_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        palette_title = QLabel("Tile Types")
        palette_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        palette_layout.addWidget(palette_title)
        
        # Create palette buttons
        self.palette_buttons = []
        self.selected_tile = EMPTY
        
        palette_items = [
            ("Agent", BLUE, AGENT),
            ("Gold", GREEN, GOLD),
            ("Wumpus", RED, WUMPUS),
            ("Pit", BLACK, PIT),
            ("Empty", WHITE, EMPTY),
            ("Obstacle", BROWN, OBSTACLE),
            ("Trap", ORANGE, TRAP),
            ("Teleport", PURPLE, TELEPORT)
        ]
        
        for name, color, tile_type in palette_items:
            btn = StyledButton(name, color)
            btn.setProperty("tile_type", tile_type)
            btn.clicked.connect(self.set_selected_tile)
            palette_layout.addWidget(btn)
            self.palette_buttons.append(btn)
        
        palette_layout.addStretch()
        
        # Action buttons
        action_layout = QVBoxLayout()
        
        self.clearButton = StyledButton("Clear Map", GRAY)
        self.saveButton = StyledButton("Save Map", GREEN)
        self.loadButton = StyledButton("Load Map", BLUE)
        self.testPathButton = StyledButton("Test Path", YELLOW)
        self.backButton = StyledButton("Back to Main Menu", RED, MAIN_MENU)
        
        for button in [self.clearButton, self.saveButton, self.loadButton, self.testPathButton]:
            action_layout.addWidget(button)
        
        action_layout.addStretch()
        action_layout.addWidget(self.backButton)
        
        palette_layout.addLayout(action_layout)
        grid_layout.addLayout(palette_layout)
        
        layout.addLayout(grid_layout)
        self.setLayout(layout)
        
        # Initialize map
        self.initialize_map()
    
    def initialize_map(self):
        self.grid = [[EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.agent_pos = (0, 0)
        self.gold_pos = (GRID_SIZE-1, GRID_SIZE-1)
        self.grid[0][0] = AGENT
        self.grid[GRID_SIZE-1][GRID_SIZE-1] = GOLD
        self.teleport_destinations = {}
        self.gridWidget.set_grid(self.grid, self.agent_pos, self.gold_pos)
    
    def set_selected_tile(self):
        sender = self.sender()
        self.selected_tile = sender.property("tile_type")
        
        # Update UI to show which button is selected
        for btn in self.palette_buttons:
            btn.setStyleSheet("")
        sender.setStyleSheet("background-color: #5cb85c; color: white;")
        
        # Update message
        tile_names = {
            EMPTY: "Empty", 
            OBSTACLE: "Obstacle", 
            WUMPUS: "Wumpus", 
            PIT: "Pit",
            AGENT: "Agent", 
            GOLD: "Gold", 
            TELEPORT: "Teleport", 
            TRAP: "Trap"
        }
        self.message_box.setText(f"Selected tile: {tile_names.get(self.selected_tile, 'Unknown')}")

    def handle_tile_click(self, row, col):
        # Don't allow placing teleports without destinations
        if self.selected_tile == TELEPORT and not any(self.grid[r][c] == TELEPORT for r in range(len(self.grid)) for c in range(len(self.grid[0]))):
            self.teleport_destinations[(row, col)] = None  # Mark as needing a destination

        # Special case for teleports - link them in pairs
        elif self.selected_tile == TELEPORT and any(self.grid[r][c] == TELEPORT for r in range(len(self.grid)) for c in range(len(self.grid[0]))):
            # If this is the second teleport, link it with the first one
            first_teleport = None
            for r in range(len(self.grid)):
                for c in range(len(self.grid[0])):
                    if self.grid[r][c] == TELEPORT:
                        first_teleport = (r, c)
                        break
                if first_teleport:
                    break
                    
            if first_teleport and first_teleport != (row, col):
                self.teleport_destinations[first_teleport] = (row, col)
                self.teleport_destinations[(row, col)] = first_teleport
        
        # Handle agent and gold placement (only one of each allowed)
        if self.selected_tile == AGENT:
            # Remove existing agent
            for r in range(len(self.grid)):
                for c in range(len(self.grid[0])):
                    if self.grid[r][c] == AGENT:
                        self.grid[r][c] = EMPTY
            self.agent_pos = (row, col)
            
        elif self.selected_tile == GOLD:
            # Remove existing gold
            for r in range(len(self.grid)):
                for c in range(len(self.grid[0])):
                    if self.grid[r][c] == GOLD:
                        self.grid[r][c] = EMPTY
            self.gold_pos = (row, col)
            
        # Set the tile
        self.grid[row][col] = self.selected_tile
        self.gridWidget.set_grid(self.grid, self.agent_pos, self.gold_pos)

# Settings screen
class SettingsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(30)
        
        # Settings options
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # Animation speed
        anim_layout = QHBoxLayout()
        anim_label = QLabel("Animation Speed:")
        anim_label.setFont(QFont("Arial", 14))
        self.animationSpeedCombo = QComboBox()
        self.animationSpeedCombo.addItems(["Slow", "Medium", "Fast", "Instant"])
        self.animationSpeedCombo.setCurrentText("Medium")
        anim_layout.addWidget(anim_label)
        anim_layout.addWidget(self.animationSpeedCombo)
        form_layout.addLayout(anim_layout)
        
        # Sound effects
        sound_layout = QHBoxLayout()
        sound_label = QLabel("Sound Effects:")
        sound_label.setFont(QFont("Arial", 14))
        self.soundCheckBox = QPushButton("Enabled")
        self.soundCheckBox.setCheckable(True)
        self.soundCheckBox.setChecked(True)
        self.soundCheckBox.clicked.connect(self.toggle_sound)
        sound_layout.addWidget(sound_label)
        sound_layout.addWidget(self.soundCheckBox)
        form_layout.addLayout(sound_layout)
        
        # Path preview
        path_layout = QHBoxLayout()
        path_label = QLabel("Show Path Preview:")
        path_label.setFont(QFont("Arial", 14))
        self.pathPreviewCheckBox = QPushButton("Enabled")
        self.pathPreviewCheckBox.setCheckable(True)
        self.pathPreviewCheckBox.setChecked(True)
        self.pathPreviewCheckBox.clicked.connect(self.toggle_path_preview)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.pathPreviewCheckBox)
        form_layout.addLayout(path_layout)
        
        layout.addLayout(form_layout)
        layout.addSpacing(40)
        
        # Save and back buttons
        buttons_layout = QHBoxLayout()
        self.saveButton = StyledButton("Save Settings", GREEN)
        self.backButton = StyledButton("Back", RED, MAIN_MENU)
        buttons_layout.addWidget(self.saveButton)
        buttons_layout.addWidget(self.backButton)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def toggle_sound(self):
        if self.soundCheckBox.isChecked():
            self.soundCheckBox.setText("Enabled")
        else:
            self.soundCheckBox.setText("Disabled")
    
    def toggle_path_preview(self):
        if self.pathPreviewCheckBox.isChecked():
            self.pathPreviewCheckBox.setText("Enabled")
        else:
            self.pathPreviewCheckBox.setText("Disabled")

# Statistics screen
class StatsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title = QLabel("Game Statistics")
        title.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(30)
        
        # Stats data - would normally load from a file
        self.stats = {
            "Games Played": 15,
            "Games Won": 10,
            "Win Rate": "66.7%",
            "Average Score": 842,
            "Highest Score": 1245,
            "Total Steps": 347,
            "Total Time Played": "3:45:22",
            "Wumpuses Avoided": 27,
            "Pits Avoided": 42,
            "Gold Collected": 10
        }
        
        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        row = 0
        for key, value in self.stats.items():
            label = QLabel(f"{key}:")
            label.setFont(QFont("Arial", 14))
            
            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            
            stats_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight)
            stats_layout.addWidget(value_label, row, 1, Qt.AlignmentFlag.AlignLeft)
            row += 1
        
        stats_widget = QWidget()
        stats_widget.setLayout(stats_layout)
        layout.addWidget(stats_widget)
        layout.addSpacing(40)
        
        # Reset and back buttons
        buttons_layout = QHBoxLayout()
        self.resetButton = StyledButton("Reset Statistics", YELLOW)
        self.backButton = StyledButton("Back to Main Menu", RED, MAIN_MENU)
        buttons_layout.addWidget(self.resetButton)
        buttons_layout.addWidget(self.backButton)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)


    
class WumpusGameApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wumpus AI Game")
        self.setFixedSize(GAME_SCREEN_WIDTH, HEIGHT)
        
        # Stack widget to switch between screens
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Create screens
        self.create_levels()
        self.create_screens()
        
        # Set up connections
        self.setup_connections()
        
        # Start with main menu
        self.stack.setCurrentIndex(MAIN_MENU)
        
        # Current game instance
        self.current_game = None
    
    def create_levels(self):
        """Create predefined levels"""
        self.levels = [
            Level("Tutorial", "Easy"),
            Level("Forest", "Easy"),
            Level("Cave", "Medium"),
            Level("Dungeon", "Medium"),
            Level("Abyss", "Hard"),
            Level("Labyrinth", "Hard", custom_config={"obstacles": 10}),
            Level("The Void", "Expert")
        ]
    
    def create_screens(self):
        """Create all the screens"""
        # Main menu
        self.main_menu = MainMenuScreen()
        self.stack.addWidget(self.main_menu)
        
        # Level select
        self.level_select = LevelSelectScreen(self.levels)
        self.stack.addWidget(self.level_select)
        
        # Game screen
        self.game_screen = GameScreen()
        self.stack.addWidget(self.game_screen)
        
        # Map editor
        self.map_editor = MapEditorScreen()
        self.stack.addWidget(self.map_editor)
        
        # Settings
        self.settings_screen = SettingsScreen()
        self.stack.addWidget(self.settings_screen)
        
        # Statistics
        self.stats_screen = StatsScreen()
        self.stack.addWidget(self.stats_screen)
    
    def setup_connections(self):
        """Connect signals and slots"""
        # Main menu buttons
        self.main_menu.playButton.clicked.connect(lambda: self.stack.setCurrentIndex(LEVEL_SELECT))
        self.main_menu.mapEditorButton.clicked.connect(lambda: self.stack.setCurrentIndex(MAP_EDITOR))
        self.main_menu.statsButton.clicked.connect(lambda: self.stack.setCurrentIndex(STATS))
        self.main_menu.settingsButton.clicked.connect(lambda: self.stack.setCurrentIndex(SETTINGS))
        self.main_menu.quitButton.clicked.connect(self.close)
        
        # Level select buttons
        for i, button in enumerate(self.level_select.level_buttons):
            button.clicked.connect(lambda checked, level_idx=i: self.start_game_with_level(level_idx))
        self.level_select.backButton.clicked.connect(lambda: self.stack.setCurrentIndex(MAIN_MENU))
        
        # Game screen buttons
        self.game_screen.pauseButton.clicked.connect(self.toggle_pause_game)
        self.game_screen.restartButton.clicked.connect(self.restart_game)
        self.game_screen.menuButton.clicked.connect(lambda: self.stack.setCurrentIndex(MAIN_MENU))
        self.game_screen.gridWidget.tileClicked.connect(self.handle_game_tile_click)
        
        # Map editor buttons
        self.map_editor.clearButton.clicked.connect(self.map_editor.initialize_map)
        self.map_editor.saveButton.clicked.connect(self.save_map)
        self.map_editor.loadButton.clicked.connect(self.load_map)
        self.map_editor.testPathButton.clicked.connect(self.test_path)
        self.map_editor.backButton.clicked.connect(lambda: self.stack.setCurrentIndex(MAIN_MENU))
        
        # Settings screen
        self.settings_screen.saveButton.clicked.connect(self.save_settings)
        self.settings_screen.backButton.clicked.connect(lambda: self.stack.setCurrentIndex(MAIN_MENU))
        
        # Stats screen
        self.stats_screen.resetButton.clicked.connect(self.reset_stats)
        self.stats_screen.backButton.clicked.connect(lambda: self.stack.setCurrentIndex(MAIN_MENU))
    
    def start_game_with_level(self, level_idx):
        """Start a new game with the selected level"""
        level = self.levels[level_idx]
        self.current_game = WumpusGame(self.game_screen, level=level)
        self.current_game.start_game()
        self.stack.setCurrentIndex(GAME_RUNNING)
    
    def toggle_pause_game(self):
        """Pause or resume the current game"""
        if self.current_game:
            self.current_game.pause_game()
    
    def restart_game(self):
        """Restart the current game"""
        if self.current_game and hasattr(self.current_game, 'level'):
            self.start_game_with_level(self.levels.index(self.current_game.level))
    
    def handle_game_tile_click(self, row, col):
        """Handle a click on the game grid"""
        if self.current_game:
            # Show path preview
            if self.settings_screen.pathPreviewCheckBox.isChecked():
                path = self.current_game.show_path(row, col)
                if path and len(path) > 1:  # If valid path with at least one move
                    target_row, target_col = path[1]  # First step in path
                    self.current_game.move_agent(target_row, target_col)
            else:
                # Direct movement without path
                self.current_game.move_agent(row, col)
    
    def save_map(self):
        """Save the current map to a file"""
        # In a real app, this would use QFileDialog and actually save the file
        self.map_editor.message_box.setText("Map saved!")
    
    def load_map(self):
        """Load a map from a file"""
        # In a real app, this would use QFileDialog and actually load a file
        pass
    
    def test_path(self):
        """Test pathfinding on the current map"""
        # Create a game instance to test the path
        game = WumpusGame(self.game_screen, grid=self.map_editor.grid)
        path = game.calculate_path(self.map_editor.gold_pos[0], self.map_editor.gold_pos[1])
        self.map_editor.gridWidget.set_path(path)
    
    def save_settings(self):
        """Save the current settings"""
        # Animation speed
        speed = self.settings_screen.animationSpeedCombo.currentText()
        
        # Sound effects
        sound_enabled = self.settings_screen.soundCheckBox.isChecked()
        
        # Path preview
        path_preview = self.settings_screen.pathPreviewCheckBox.isChecked()
        
        # Apply settings to game
        if self.current_game:
            self.game_screen.gridWidget.show_path_preview = path_preview
        
        self.stack.setCurrentIndex(MAIN_MENU)
    
    def reset_stats(self):
        """Reset all statistics"""
        # In a real app, this would clear the stats file/database
        self.stats_screen.stats = {
            "Games Played": 0,
            "Games Won": 0,
            "Win Rate": "0%",
            "Average Score": 0,
            "Highest Score": 0,
            "Total Steps": 0,
            "Total Time Played": "0:00:00",
            "Wumpuses Avoided": 0,
            "Pits Avoided": 0,
            "Gold Collected": 0
        }
        # Recreate the stats screen
        self.stack.removeWidget(self.stats_screen)
        self.stats_screen = StatsScreen()
        self.stack.addWidget(self.stats_screen)
        self.stats_screen.backButton.clicked.connect(lambda: self.stack.setCurrentIndex(MAIN_MENU))
        self.stats_screen.resetButton.clicked.connect(self.reset_stats)

# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WumpusGameApp()
    window.show()
    sys.exit(app.exec())