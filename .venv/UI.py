import pygame
from constants import *
from draw_utils import DrawUtils
class MenuScreen:
    def __init__(self):
        self.show_ip_dialog = False
        self.DrawUtils = DrawUtils

        try:
            self.font = pygame.font.Font('Fonts/font.otf', 60)
            self.title_font = pygame.font.Font('Fonts/font.otf', 90)
        except pygame.error:
            print("Custom font not found, using default")
            self.font = pygame.font.Font(None, 42)

        # Load and scale the texture
        try:
            self.texture = pygame.image.load('Textures/tables.png').convert_alpha()
        except pygame.error:
            print("Texture not found")
            self.texture = None

        button_width = 200
        button_height = 50
        button_spacing = 75
        border_width = 3

        # Calculate positions
        total_height = (3 * button_height) + (2 * button_spacing)
        start_y = (WINDOW_HEIGHT // 2) - (total_height // 2)

        # Store both outer (with border) and inner rectangles
        self.button_borders = []
        self.buttons = []

        # Create buttons with their borders
        button_positions = [
            ("Alone", start_y),
            ("Amidst", start_y + button_height + button_spacing),
            ("Abandon", start_y + 2 * (button_height + button_spacing))
        ]

        for text, y_pos in button_positions:
            # Outer rectangle (border)
            border_rect = pygame.Rect(
                WINDOW_WIDTH // 2 - (button_width + border_width * 2) // 2,
                y_pos - border_width,
                button_width + border_width * 2,
                button_height + border_width * 2
            )

            # Inner rectangle (button)
            button_rect = pygame.Rect(
                WINDOW_WIDTH // 2 - button_width // 2,
                y_pos,
                button_width,
                button_height
            )

            self.button_borders.append(border_rect)
            self.buttons.append((button_rect, text))

    def handle_click(self, mouse_x, mouse_y):
        """Handle menu button clicks"""
        for button_rect, text in self.buttons:
            if button_rect.collidepoint(mouse_x, mouse_y):
                return text  # Return the exact text without modification
        return None

    def draw(self, screen):
        """Draw the menu using DrawUtils"""
        DrawUtils.draw_menu(screen, self)