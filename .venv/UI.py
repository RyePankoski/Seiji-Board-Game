import pygame
from constants import *
from draw_utils import DrawUtils
class MenuScreen:
    def __init__(self):
        self.show_ip_dialog = False
        self.DrawUtils = DrawUtils

        try:
            self.font = pygame.font.Font('Fonts/general_text.ttf', 60)  # Changed size to match
            self.title_font = pygame.font.Font('Fonts/general_text.ttf', 90)  # Updated font while keeping size
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

    def fade_transition(self, screen, fade_in=True, speed=5, delay=10):
        """
        Creates a fade transition effect.

        Args:
            screen: Pygame surface to fade
            fade_in: If True, fades to black. If False, fades from black
            speed: How quickly to fade (lower is slower)
            delay: Delay between fade steps in milliseconds
        """
        fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        fade_surface.fill((0, 0, 0))  # Black fade

        alpha_range = range(0, 255, speed) if fade_in else range(255, 0, -speed)

        for alpha in alpha_range:
            fade_surface.set_alpha(alpha)
            screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            pygame.time.delay(delay)

    def draw(self, screen):
        """Draw the menu using DrawUtils"""
        DrawUtils.draw_menu(screen, self)


class PostGameScreen:
    def __init__(self):
        self.buttons = []
        self.button_borders = []

        button_width = 200
        button_height = 50
        button_spacing = 75
        border_width = 3

        # Calculate positions
        total_height = (2 * button_height) + button_spacing
        start_y = (WINDOW_HEIGHT // 2)

        # Create buttons
        button_positions = [
            ("Rematch", start_y),
            ("Menu", start_y + button_height + button_spacing)
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
        """Handle post-game button clicks"""
        for button_rect, text in self.buttons:
            if button_rect.collidepoint(mouse_x, mouse_y):
                return text
        return None

    def draw(self, screen, winner_text):
        """Draw the post-game screen"""
        # Draw black background
        screen.fill((0, 0, 0))

        # Draw the winner text
        font = pygame.font.Font('Fonts/general_text.ttf', 90)
        text_surface = font.render(winner_text, True, (255, 215, 0))  # Gold color
        text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))

        # Create outline effect
        outline_offset = 3
        outline_positions = [
            (-outline_offset, -outline_offset),
            (outline_offset, -outline_offset),
            (-outline_offset, outline_offset),
            (outline_offset, outline_offset)
        ]

        for offset_x, offset_y in outline_positions:
            offset_rect = text_rect.copy()
            offset_rect.x += offset_x
            offset_rect.y += offset_y
            outline_surface = font.render(winner_text, True, (0, 0, 0))
            screen.blit(outline_surface, offset_rect)

        screen.blit(text_surface, text_rect)

        # Draw buttons
        button_font = pygame.font.Font('Fonts/general_text.ttf', 32)
        for border_rect, (button_rect, text) in zip(self.button_borders, self.buttons):
            pygame.draw.rect(screen, (255, 0, 0), border_rect)  # Red border
            pygame.draw.rect(screen, (0, 0, 0), button_rect)  # Black button

            text_surface = button_font.render(text, True, (255, 0, 0))  # Red text
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)