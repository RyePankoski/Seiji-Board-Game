import pygame
from constants import *


class DrawUtils:
    @staticmethod
    def draw(game, screen):
        """Main draw method that handles all drawing operations"""
        screen.blit(game.background_2, (0, 0))

        # Draw board border first (3D effect)
        border_width = 8
        # Outer dark border (shadow)
        pygame.draw.rect(screen, (40, 40, 40),
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

        # Draw main board background
        screen.blit(game.background, (GRID_OFFSET, GRID_OFFSET))

        # Draw center X
        DrawUtils._draw_center_x(screen)

        # Draw grid
        DrawUtils._draw_grid(screen)

        # Show valid placement squares for piece placement phase
        if not game.selected_piece and not game.is_king_placement_phase() and game.reserve_selected:
            DrawUtils._draw_valid_placements(game, screen)

        # Draw valid moves for selected piece
        DrawUtils._draw_valid_moves(game, screen)

        # Draw the mute button
        DrawUtils._draw_mute_button(game, screen)

        # Draw the selected piece highlight
        if game.selected_piece:
            DrawUtils._draw_selected_piece_highlight(game, screen)

        # Draw the pieces on the board
        DrawUtils._draw_pieces_on_board(game, screen)

        # Draw piece reserve area on the right side
        DrawUtils._draw_piece_reserve(game, screen)

        # Draw phase and current player info at the top
        DrawUtils._draw_game_info(game, screen)

        # Draw selected reserve piece highlight
        if game.selected_reserve_piece:
            DrawUtils._draw_selected_reserve_piece(game, screen)

        game.draw_message_log(screen)

        # Draw row and column numbers
        font = pygame.font.SysFont(None, 24)
        text_color = (255, 255, 255)  # Black for visibility

        # Draw numbers along the left side (rows)
        for row in range(1, BOARD_SIZE + 1):
            text = font.render(str(row), True, text_color)
            text_rect = text.get_rect()
            text_rect.right = GRID_OFFSET - 10  # 10 pixels padding from the grid
            text_rect.centery = GRID_OFFSET + (BOARD_SIZE - row + 0.5) * CELL_SIZE  # Adjust for bottom-up numbering
            screen.blit(text, text_rect)

        # Draw numbers along the bottom (columns)
        for col in range(1, BOARD_SIZE + 1):
            text = font.render(str(col), True, text_color)
            text_rect = text.get_rect()
            text_rect.centerx = GRID_OFFSET + (col - 0.5) * CELL_SIZE
            text_rect.top = GRID_OFFSET + BOARD_SIZE * CELL_SIZE + 10  # Adjust to position above the grid
            screen.blit(text, text_rect)

    def draw_menu(screen, menu):
        """Draw the menu screen with all its components"""
        # Draw background
        screen.fill((50, 50, 50))

        # Draw each button with its texture and border
        for border_rect, (button_rect, text) in zip(menu.button_borders, menu.buttons):
            # Draw border
            pygame.draw.rect(screen, (200, 200, 200), border_rect)

            # Draw button background
            pygame.draw.rect(screen, (100, 100, 100), button_rect)

            # Draw texture if available
            if menu.texture:
                # Create a subsurface of the texture sized to the button
                texture_rect = menu.texture.get_rect()
                scale_factor = max(button_rect.width / texture_rect.width,
                                 button_rect.height / texture_rect.height)

                scaled_width = int(texture_rect.width * scale_factor)
                scaled_height = int(texture_rect.height * scale_factor)

                scaled_texture = pygame.transform.scale(menu.texture,
                                                     (scaled_width, scaled_height))

                # Center the texture on the button
                texture_x = button_rect.x + (button_rect.width - scaled_width) // 2
                texture_y = button_rect.y + (button_rect.height - scaled_height) // 2

                # Create a mask to keep the texture within the button bounds
                button_surface = pygame.Surface((button_rect.width, button_rect.height))
                button_surface.fill((100, 100, 100))
                screen.blit(scaled_texture, (texture_x, texture_y),
                           special_flags=pygame.BLEND_RGBA_MULT)

            # Draw text
            DrawUtils._draw_menu_text(screen, text, button_rect, menu.font)

    @staticmethod
    def _draw_menu_text(screen, text, button, font):
        """Helper method to draw text on menu buttons"""
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=button.center)
        screen.blit(text_surface, text_rect)

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

        pygame.draw.rect(screen, (200, 200,200, 100), button_bg_rect)
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

        font = pygame.font.Font(None, 30)
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
            top_left_x = (center[0] // CELL_SIZE) * CELL_SIZE - (area_size // 2) * CELL_SIZE
            top_left_y = (center[1] // CELL_SIZE) * CELL_SIZE - (area_size // 2) * CELL_SIZE

            outline_color = PLAYER_1_COLOR if piece.owner == PLAYER_1 else PLAYER_2_COLOR
            outline_rect = pygame.Rect(top_left_x, top_left_y, area_size * CELL_SIZE, area_size * CELL_SIZE)
            pygame.draw.rect(screen, outline_color, outline_rect, 4)

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
        """Draw game information including current player and game over message"""
        display_name = "White" if game.current_player == PLAYER_1 else "Black"

        font = pygame.font.Font(None, 36)
        text3 = font.render(f"Player to move: {display_name}", True, WHITE)
        screen.blit(text3, (10, 10))

        if game.game_over:
            winner_text = "WHITE WINS" if game.winner == PLAYER_1 else "BLACK WINS"

            # Use a much larger font for the end game message
            end_game_font = pygame.font.Font(None, 250)
            text5 = end_game_font.render(winner_text, True, YELLOW)

            # Get the width and height of the text to center it
            text_rect = text5.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

            # Create a black outline effect
            outline_offset = 5
            # List of all 8 directions for the outline
            outline_positions = [
                (-outline_offset, -outline_offset),  # Top-left
                (0, -outline_offset),  # Top
                (outline_offset, -outline_offset),  # Top-right
                (-outline_offset, 0),  # Left
                (outline_offset, 0),  # Right
                (-outline_offset, outline_offset),  # Bottom-left
                (0, outline_offset),  # Bottom
                (outline_offset, outline_offset)  # Bottom-right
            ]

            # Draw the outline
            for x_offset, y_offset in outline_positions:
                outline_rect = text_rect.copy()
                outline_rect.x += x_offset
                outline_rect.y += y_offset
                screen.blit(end_game_font.render(winner_text, True, BLACK), outline_rect)

            # Draw the main text in the center of the screen
            screen.blit(text5, text_rect)

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