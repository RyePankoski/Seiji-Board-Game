import pygame
import random
import math
from constants import *

class StarPoint:
    def __init__(self, center_x, center_y,star_color):
        offset_x = random.uniform(-5, 5)
        offset_y = random.uniform(-5, 5)
        self.position = [center_x + offset_x, center_y + offset_y]
        self.center = (center_x, center_y)  # Store center for distance calculation
        self.size = 0.5
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)

        min_speed = .1

        # Ensure min speed
        if x > 0:
            x = max(min_speed, x)
        else:
            x = min(-min_speed, x)

        if y > 0:
            y = max(min_speed, y)
        else:
            y = min(-min_speed, y)

        self.vector = (x, y)
        self.color = star_color
    def update(self, speed):
        # Update position based on vector
        self.position[0] += self.vector[0] * speed
        self.position[1] += self.vector[1] * speed

        # Calculate distance from center
        dx = self.position[0] - self.center[0]
        dy = self.position[1] - self.center[1]
        distance = (dx * dx + dy * dy) ** 0.5

        # Gradually increase size based on distance
        # Starting from 0.5, growing to max 2.5
        self.size = 0.5 + (distance / 150)  # Adjust 400 to control growth rate
        self.size = min(10, self.size)  # Cap maximum size

    def is_off_screen(self, width, height):
        return (self.position[0] < 0 or self.position[0] > width or
                self.position[1] < 0 or self.position[1] > height)

class MenuStarfield:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.stars = []
        self.center = (width // 2, height // 2)
        self.frame_counter = 0
        self.spawn_interval = 2
        self.max_stars = 200
        self.speed = 5

    def update(self):
        self.frame_counter += 1

        star_chance = random.uniform(0,100)

        if star_chance > 98:
            star_color = (random.uniform(0,255),random.uniform(0,255),random.uniform(0,255))
        else:
            star_color = (255, 255, 255)

        # Spawn new star every few frames if under max
        if self.frame_counter % self.spawn_interval == 0 and len(self.stars) < self.max_stars:
            self.stars.append(StarPoint(self.center[0], self.center[1], star_color))

        # Update existing stars and remove ones that are off screen
        self.stars = [star for star in self.stars if not star.is_off_screen(self.width, self.height)]
        for star in self.stars:
            star.update(self.speed)

    def draw(self, screen):
        for star in self.stars:
            pygame.draw.circle(screen, star.color,
                               (int(star.position[0]), int(star.position[1])),
                               star.size)  # Use dynamic size
class DrawUtils:
    @staticmethod
    def draw(game, screen):
        """Main draw method that handles all drawing operations"""
        screen.blit(game.background_2, (0, 0))

        # Draw board border first (3D effect)
        border_width = 8
        # Outer dark border (shadow)
        pygame.draw.rect(screen, (40, 40, 40,),
                         (GRID_OFFSET - border_width,
                          GRID_OFFSET - border_width,
                          BOARD_SIZE * CELL_SIZE + border_width * 2,
                          BOARD_SIZE * CELL_SIZE + border_width * 2))
        # Inner light border (highlight)
        pygame.draw.rect(screen, (200, 200, 200),
                         (GRID_OFFSET - border_width // 2,
                          GRID_OFFSET - border_width // 2,
                          BOARD_SIZE * CELL_SIZE + border_width,
                          BOARD_SIZE * CELL_SIZE + border_width))

        board_size = BOARD_SIZE * CELL_SIZE
        board_background = pygame.transform.scale(game.background, (board_size, board_size))
        screen.blit(board_background, (GRID_OFFSET, GRID_OFFSET))

        # Draw the grid
        DrawUtils._draw_grid(screen)
        DrawUtils._draw_coordinates(screen)  # Add this line

        if game.is_king_placement_phase():
            DrawUtils.draw_red_center(screen)
        else:
            DrawUtils._draw_center_x(screen)

        # Draw the center X
        DrawUtils._draw_center_x(screen)

        # Draw valid placements if in placement phase
        if game.selected_reserve_piece:
            DrawUtils._draw_valid_placements(game, screen)

        # Draw valid moves if a piece is selected
        if game.selected_piece:
            DrawUtils._draw_valid_moves(game, screen)

        # Draw selected piece highlight
        if game.selected_piece:
            DrawUtils._draw_selected_piece_highlight(game, screen)

        # Draw all pieces
        DrawUtils._draw_pieces_on_board(game, screen)

        # Draw piece reserve
        DrawUtils._draw_piece_reserve(game, screen)

        # Draw selected reserve piece highlight
        if game.selected_reserve_piece:
            DrawUtils._draw_selected_reserve_piece(game, screen)

        # Draw mute button and game info
        DrawUtils._draw_resign_button(game, screen)
        DrawUtils._draw_mute_button(game, screen)
        DrawUtils._draw_game_info(game, screen)

    @staticmethod
    def _draw_resign_button(game, screen):
        """Draw the resign button in the top right corner"""
        button_color = (200, 50, 50) if game.resign_hover else (150, 30, 30)
        pygame.draw.rect(screen, button_color, game.resign_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), game.resign_button_rect, 2)  # White border

        # Draw button text
        font = pygame.font.Font('Fonts/general_text.ttf', 30)  # Use the custom font instead of None
        text = font.render("Resign", True, (255, 255, 255))
        text_rect = text.get_rect(center=game.resign_button_rect.center)
        screen.blit(text, text_rect)
    @staticmethod
    def _draw_coordinates(screen, color=(255, 255, 255)):  # Added color parameter with white as default
        """Draw coordinate numbers on the left and bottom edges of the board"""
        # Set up the font
        font = pygame.font.Font(None, int(CELL_SIZE * 0.5))  # Font size relative to cell size

        # Calculate padding for number placement
        padding = CELL_SIZE * 0.3

        for i in range(BOARD_SIZE):
            # Bottom numbers count left to right (1 to n)
            bottom_number = str(i + 1)
            text = font.render(bottom_number, True, color)  # Using custom color
            x = GRID_OFFSET + (i * CELL_SIZE) + (CELL_SIZE - text.get_width()) // 2
            y = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + padding
            screen.blit(text, (x, y))

            # Left numbers count top to bottom (1 to n)
            left_number = str(BOARD_SIZE - i)
            text = font.render(left_number, True, color)  # Using custom color
            x = GRID_OFFSET - padding - text.get_width()
            y = GRID_OFFSET + (i * CELL_SIZE) + (CELL_SIZE - text.get_height()) // 2
            screen.blit(text, (x, y))
    @staticmethod
    def draw_menu(screen, menu):
        """Draw the menu screen with starfield effect and all its components"""
        # Initialize starfield if not already created
        if not hasattr(menu, 'starfield'):
            menu.starfield = MenuStarfield(screen.get_width(), screen.get_height())

        # Draw black background
        screen.fill((0, 0, 0))

        # Update and draw starfield
        menu.starfield.update()
        menu.starfield.draw(screen)

        # Draw title "Deceit" at the top
        title_font = pygame.font.Font("Fonts/general_text.ttf", 100)  # Using your custom font
        title_text = title_font.render("Seiji ", True, (255, 255, 255))
        title_rect = title_text.get_rect(centerx=screen.get_width() // 2, top=50)
        screen.blit(title_text, title_rect)

        # Draw each button bigger and without table texture
        button_height = 80  # Increased button height
        for border_rect, (button_rect, text) in zip(menu.button_borders, menu.buttons):
            # Increase button size
            button_rect.height = button_height
            border_rect.height = button_height + 4

            # Draw text with larger font
            DrawUtils._draw_menu_text(screen, text, button_rect, menu.font, size=40)

        if menu.show_ip_dialog:
            # Draw semi-transparent black overlay
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            screen.blit(overlay, (0, 0))

            # Draw IP dialog
            dialog_width = 400
            dialog_height = 200
            dialog_x = (WINDOW_WIDTH - dialog_width) // 2
            dialog_y = (WINDOW_HEIGHT - dialog_height) // 2

            # Draw dialog box
            pygame.draw.rect(screen, (0, 0, 0), (dialog_x, dialog_y, dialog_width, dialog_height))
            pygame.draw.rect(screen, (255, 255, 255), (dialog_x, dialog_y, dialog_width, dialog_height), 2)

            # Draw text
            font = pygame.font.Font(None, 32)
            title = font.render("Enter Server IP", True, (255, 255, 255))
            screen.blit(title, (dialog_x + 20, dialog_y + 20))

            # Draw input box
            input_box = pygame.Rect(dialog_x + 20, dialog_y + 70, dialog_width - 40, 40)
            pygame.draw.rect(screen, (50, 50, 50), input_box)
            pygame.draw.rect(screen, (255, 255, 255), input_box, 2)

            # Draw input text
            if hasattr(menu, 'ip_input'):
                text = font.render(menu.ip_input, True, (255, 255, 255))
                screen.blit(text, (input_box.x + 5, input_box.y + 10))

    def draw_message_log(self, screen):
        """Draw the message log in the bottom right corner with scrolling"""
        # Draw semi-transparent background
        log_surface = pygame.Surface((self.log_rect.width, self.log_rect.height))
        log_surface.fill((30, 30, 30))
        log_surface.set_alpha(200)
        screen.blit(log_surface, self.log_rect)

        # Draw border
        pygame.draw.rect(screen, (100, 100, 100), self.log_rect, 2)

        # Get the most recent messages (reverse the list)
        messages_to_display = list(reversed(self.message_log))

        # Draw messages from bottom up
        current_y = self.log_rect.bottom - 30  # Start from bottom, with padding

        for message in messages_to_display:
            text_surface = self.log_font.render(message, True, (255, 255, 255))

            # If we've moved above the top of the box, stop drawing
            if current_y < self.log_rect.top:
                break

            if text_surface.get_width() > self.log_rect.width - 10:
                # Handle word wrapping
                words = message.split()
                lines = []
                current_line = words[0]

                for word in words[1:]:
                    test_line = current_line + " " + word
                    test_surface = self.log_font.render(test_line, True, (255, 255, 255))
                    if test_surface.get_width() <= self.log_rect.width - 10:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                lines.append(current_line)

                # Draw wrapped lines from bottom up
                for line in reversed(lines):
                    text_surface = self.log_font.render(line, True, (255, 255, 255))
                    screen.blit(text_surface, (self.log_rect.x + 5, current_y))
                    current_y -= 25
            else:
                screen.blit(text_surface, (self.log_rect.x + 5, current_y))
                current_y -= 25

    @staticmethod
    def _draw_menu_text(screen, text, button, font, size=50):  # Increased size from 40 to 50
        """Helper method to draw text on menu buttons with specified size"""
        letter_spacing = 10  # Adjust this value to increase/decrease spacing

        # Calculate total width with spacing to center properly
        total_width = 0
        letter_surfaces = []
        for char in text:
            letter_surface = font.render(char, True, (255, 0, 0))  # Changed to red (255, 0, 0)
            letter_surfaces.append(letter_surface)
            total_width += letter_surface.get_width() + letter_spacing
        total_width -= letter_spacing  # Remove extra spacing after last letter

        # Calculate starting x position to center the text
        start_x = button.centerx - (total_width // 2)
        y = button.centery - letter_surfaces[0].get_height() // 2

        # Draw each letter with spacing
        current_x = start_x
        for letter_surface in letter_surfaces:
            screen.blit(letter_surface, (current_x, y))
            current_x += letter_surface.get_width() + letter_spacing

    @staticmethod
    def _draw_center_x(screen):
        """Draw the X in the center of the board"""
        center_x = GRID_OFFSET + (BOARD_SIZE // 2) * CELL_SIZE
        center_y = GRID_OFFSET + (BOARD_SIZE // 2) * CELL_SIZE
        pygame.draw.line(screen, GRID_COLOR,
                         (center_x, center_y),
                         (center_x + CELL_SIZE, center_y + CELL_SIZE),
                         width=2)
        pygame.draw.line(screen, GRID_COLOR,
                         (center_x + CELL_SIZE, center_y),
                         (center_x, center_y + CELL_SIZE),
                         width=2)

    # Add this static method to the DrawUtils class:
    @staticmethod
    def draw_red_center(screen):
        """Draw a transparent red highlight in the center of the board with an X"""
        center_x = GRID_OFFSET + (BOARD_SIZE // 2) * CELL_SIZE
        center_y = GRID_OFFSET + (BOARD_SIZE // 2) * CELL_SIZE

        # Create a surface for the transparent red square
        red_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(red_surface, (255, 0, 0, 128), (0, 0, CELL_SIZE, CELL_SIZE))  # 128 is half transparency
        screen.blit(red_surface, (center_x, center_y))

        # Draw the X lines in white for contrast
        pygame.draw.line(screen, (255, 255, 255),
                         (center_x, center_y),
                         (center_x + CELL_SIZE, center_y + CELL_SIZE),
                         width=3)
        pygame.draw.line(screen, (255, 255, 255),
                         (center_x + CELL_SIZE, center_y),
                         (center_x, center_y + CELL_SIZE),
                         width=3)

    @staticmethod
    def _draw_grid(screen):
        """Draw the game board grid"""
        for i in range(BOARD_SIZE + 1):
            pygame.draw.line(screen, GRID_COLOR,
                             (GRID_OFFSET + i * CELL_SIZE, GRID_OFFSET),
                             (GRID_OFFSET + i * CELL_SIZE, GRID_OFFSET + BOARD_SIZE * CELL_SIZE),
                             width=1)
            pygame.draw.line(screen, GRID_COLOR,
                             (GRID_OFFSET, GRID_OFFSET + i * CELL_SIZE),
                             (GRID_OFFSET + BOARD_SIZE * CELL_SIZE, GRID_OFFSET + i * CELL_SIZE),
                             width=1)

    @staticmethod
    def _draw_valid_placements(game, screen):
        """Draw valid placement squares for piece placement phase"""
        valid_placements = game.get_valid_placement_squares()
        for row, col in valid_placements:
            if game.board[row][col] == EMPTY:  # Only highlight empty squares
                color = PLACE_HIGHLIGHT_PLAYER1 if game.current_player == PLAYER_1 else PLACE_HIGHLIGHT_PLAYER2
                x = GRID_OFFSET + col * CELL_SIZE
                y = GRID_OFFSET + row * CELL_SIZE

                pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.line(screen, GRID_COLOR, (x, y), (x, y + CELL_SIZE))
                pygame.draw.line(screen, GRID_COLOR, (x, y), (x + CELL_SIZE, y))

    @staticmethod
    def _draw_valid_moves(game, screen):
        """Draw valid moves for selected piece"""
        for row, col in game.valid_moves:
            color = MOVE_HIGHLIGHT_PLAYER1 if game.current_player == PLAYER_1 else MOVE_HIGHLIGHT_PLAYER2
            x = GRID_OFFSET + col * CELL_SIZE
            y = GRID_OFFSET + row * CELL_SIZE

            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.line(screen, GRID_COLOR, (x, y), (x, y + CELL_SIZE))
            pygame.draw.line(screen, GRID_COLOR, (x, y), (x + CELL_SIZE, y))

    @staticmethod
    def _draw_mute_button(game, screen):
        """Draw the mute button with speaker icon and volume message"""
        # Draw button background with gray box
        button_bg_rect = pygame.Rect(game.mute_button_rect)
        button_bg_rect.inflate_ip(700, 10)

        pygame.draw.rect(screen, (200, 200, 200, 100), button_bg_rect)
        pygame.draw.rect(screen, (180, 20, 20), button_bg_rect, width=2)
        pygame.draw.rect(screen, (30, 30, 30), game.mute_button_rect, border_radius=10)

        x, y = game.mute_button_rect.topleft
        pygame.draw.polygon(screen, WHITE, [
            (x + 15, y + 25),
            (x + 25, y + 25),
            (x + 35, y + 15),
            (x + 35, y + 45),
            (x + 25, y + 35),
            (x + 15, y + 35),
        ])

        if not game.is_muted:
            pygame.draw.arc(screen, WHITE, (x + 35, y + 20, 10, 20), -0.5, 0.5, 2)
            pygame.draw.arc(screen, WHITE, (x + 40, y + 15, 15, 30), -0.5, 0.5, 2)
        else:
            pygame.draw.line(screen, RED, (x + 40, y + 15), (x + 55, y + 45), 3)
            pygame.draw.line(screen, RED, (x + 55, y + 15), (x + 40, y + 45), 3)

        font = pygame.font.Font('Fonts/general_text.ttf', 25)
        text = font.render("Use arrows keys to adjust volume", True, BLACK)
        screen.blit(text, (x + 70, y + 20))

    @staticmethod
    def _draw_selected_piece_highlight(game, screen):
        """Draw highlight for selected piece"""
        row, col = game.selected_piece
        pygame.draw.rect(screen, RED,
                         (GRID_OFFSET + col * CELL_SIZE,
                          GRID_OFFSET + row * CELL_SIZE,
                          CELL_SIZE, CELL_SIZE))

    @staticmethod
    def _draw_pieces_on_board(game, screen):
        """Draw all pieces on the board"""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if game.board[row][col] != EMPTY:
                    piece = game.board[row][col]
                    main_color = WHITE if piece.owner == PLAYER_1 else BLACK
                    contrast_color = BLACK if piece.owner == PLAYER_1 else WHITE

                    center = (GRID_OFFSET + col * CELL_SIZE + CELL_SIZE // 2,
                              GRID_OFFSET + row * CELL_SIZE + CELL_SIZE // 2)

                    if piece.promoted:
                        pygame.draw.circle(screen, RED, center, CELL_SIZE // 2 - 2)

                    pygame.draw.circle(screen, main_color, center, CELL_SIZE // 2 - 5)

                    DrawUtils._draw_piece_type_indicators(screen, piece, center)

    @staticmethod
    def _draw_piece_type_indicators(screen, piece, center):
        """Draw special indicators for different piece types"""
        contrast_color = BLACK if piece.owner == PLAYER_1 else WHITE

        if piece.name == "Monarch":
            points = [
                (center[0], center[1] - CELL_SIZE // 4),
                (center[0] - CELL_SIZE // 4, center[1] + CELL_SIZE // 4),
                (center[0] + CELL_SIZE // 4, center[1] + CELL_SIZE // 4)
            ]
            pygame.draw.polygon(screen, GOLD, points)
        elif piece.name == "Advisor":
            pygame.draw.circle(screen, contrast_color, center, CELL_SIZE // 4)
        elif piece.name == "Palace":
            area_size = PALACE_AREA
            # Calculate original intended position without bounds checking
            top_left_x = (center[0] // CELL_SIZE) * CELL_SIZE - (area_size // 2) * CELL_SIZE
            top_left_y = (center[1] // CELL_SIZE) * CELL_SIZE - (area_size // 2) * CELL_SIZE

            outline_color = PLAYER_1_COLOR if piece.owner == PLAYER_1 else PLAYER_2_COLOR

            # Create a clip rect that represents the board boundaries
            board_rect = pygame.Rect(GRID_OFFSET, GRID_OFFSET, BOARD_SIZE * CELL_SIZE, BOARD_SIZE * CELL_SIZE)
            original_clip = screen.get_clip()
            screen.set_clip(board_rect)

            # Draw the rectangle - it will only appear within the clipped board area
            outline_rect = pygame.Rect(top_left_x, top_left_y, area_size * CELL_SIZE, area_size * CELL_SIZE)
            pygame.draw.rect(screen, outline_color, outline_rect, 4)

            # Reset the clip
            screen.set_clip(original_clip)

            # Draw the center purple square - calculate its position relative to the outline
            palace_top_left = (center[0] - CELL_SIZE // 4, center[1] - CELL_SIZE // 4)
            pygame.draw.rect(screen, PURPLE, (palace_top_left[0], palace_top_left[1], CELL_SIZE // 2, CELL_SIZE // 2))

    @staticmethod
    def _draw_piece_reserve(game, screen):
        """Draw the piece reserve area on the right side with 3D borders"""
        reserve_start_x = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + CELL_SIZE

        piece_spacing = CELL_SIZE * 0.8
        max_pieces_per_row = 4
        padding = piece_spacing * 0.5
        max_possible_rows = 5

        table_size = max(
            (max_pieces_per_row * piece_spacing) + (padding * 3),
            (max_possible_rows * piece_spacing) + (padding * 4)
        )

        # Draw tables with 3D borders
        for y_offset in [60, WINDOW_HEIGHT // 2 - 60]:
            # Draw outer shadow border
            border_width = 8
            pygame.draw.rect(screen, (40, 40, 40),
                             (reserve_start_x - border_width,
                              y_offset - border_width,
                              table_size + border_width * 2,
                              table_size + border_width * 2))

            # Draw inner highlight border
            pygame.draw.rect(screen, (200, 200, 200),
                             (reserve_start_x - border_width // 2,
                              y_offset - border_width // 2,
                              table_size + border_width,
                              table_size + border_width))

            # Draw table background
            table_texture = pygame.transform.scale(game.table_texture,
                                                   (int(table_size), int(table_size)))
            screen.blit(table_texture, (reserve_start_x, y_offset))

        # Draw the pieces
        DrawUtils._draw_reserve_pieces(game, screen, game.player1_reserve,
                                       reserve_start_x, 60, WHITE, BLACK)
        DrawUtils._draw_reserve_pieces(game, screen, game.player2_reserve,
                                       reserve_start_x, WINDOW_HEIGHT // 2 - 60,
                                       BLACK, WHITE)

    @staticmethod
    def _draw_reserve_pieces(game, screen, reserve, reserve_start_x, y_offset, piece_color, contrast_color):
        """Draw pieces in the reserve area"""
        piece_spacing = CELL_SIZE * 0.8
        max_pieces_per_row = 4
        padding = piece_spacing * 0.5

        current_y = y_offset + padding
        for section in reserve:
            num_pieces = len(section)
            rows_needed = (num_pieces + max_pieces_per_row - 1) // max_pieces_per_row

            for piece_idx, piece_type in enumerate(section):
                row = piece_idx // max_pieces_per_row
                col = piece_idx % max_pieces_per_row

                x = reserve_start_x + (col * piece_spacing) + padding
                y = current_y + (row * piece_spacing)

                pygame.draw.circle(screen, piece_color,
                                   (int(x + piece_spacing / 2), int(y + piece_spacing / 2)),
                                   int(piece_spacing / 2 - 5))

                if piece_type == "Advisor":
                    pygame.draw.circle(screen, contrast_color,
                                       (int(x + piece_spacing / 2), int(y + piece_spacing / 2)),
                                       int(piece_spacing / 4))
                elif piece_type == "Palace":
                    pygame.draw.rect(screen, PURPLE,
                                     (int(x + piece_spacing / 2 - piece_spacing / 4),
                                      int(y + piece_spacing / 2 - piece_spacing / 4),
                                      piece_spacing / 2, piece_spacing / 2))

            current_y += rows_needed * piece_spacing + padding

    @staticmethod
    def _draw_game_info(game, screen):
        """Draw game information including current player"""
        display_name = "White" if game.current_player == PLAYER_1 else "Black"

        font = pygame.font.Font('Fonts/general_text.ttf', 36)
        text = font.render(f"Player to move: {display_name}", True, WHITE)
        screen.blit(text, (10, 10))

    @staticmethod
    def _draw_selected_reserve_piece(game, screen):
        """Draw highlight for selected reserve piece"""
        reserve_start_x = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + CELL_SIZE
        piece_spacing = CELL_SIZE * 0.8
        padding = piece_spacing * 0.5
        max_pieces_per_row = 4

        y_offset = 60 if game.selected_reserve_piece['player'] == PLAYER_1 else WINDOW_HEIGHT // 2 - 60

        # Find the correct y position by calculating cumulative height
        current_y = y_offset + padding
        reserve = game.player1_reserve if game.selected_reserve_piece['player'] == PLAYER_1 else game.player2_reserve

        for section_idx in range(game.selected_reserve_piece['section']):
            num_pieces = len(reserve[section_idx])
            rows_needed = (num_pieces + max_pieces_per_row - 1) // max_pieces_per_row
            current_y += rows_needed * piece_spacing + padding

        # Use stored row and col values directly
        row = game.selected_reserve_piece['row']
        col = game.selected_reserve_piece['col']

        x = reserve_start_x + (col * piece_spacing) + padding
        y = current_y + (row * piece_spacing)

        pygame.draw.rect(screen, RED, (x, y, piece_spacing, piece_spacing), 2)