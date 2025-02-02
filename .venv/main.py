import pygame
import sys
from typing import List

# Initialize Pygame
pygame.init()

# Constants
BOARD_SIZE = 17
NUMBER_OF_PIECES = 9
CELL_SIZE = 60  # Made this explicit for clarity
GRID_OFFSET = CELL_SIZE
BOARD_PIXELS = BOARD_SIZE * CELL_SIZE
RESERVE_WIDTH = CELL_SIZE * 4  # Width for the piece reserve area
WINDOW_SIZE = BOARD_PIXELS + (GRID_OFFSET * 2) + RESERVE_WIDTH  # Total window width
PALACE_AREA = 5

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BROWN = (139, 69, 19)
GRID_COLOR = (20, 20,20)
NEW = (50, 50, 50)

PLACE_HIGHLIGHT_PLAYER1 = (0, 255, 0, 128)
PLACE_HIGHLIGHT_PLAYER2 = (255, 180, 255, 128)
MOVE_HIGHLIGHT_PLAYER1 = (0, 127, 0, 128)
MOVE_HIGHLIGHT_PLAYER2 = (127, 90, 127, 128)

RED = (255, 50, 50)
GOLD = (50, 150, 10)
PURPLE = (255,0,255)
PLAYER_1_COLOR = (255,255,255)
PLAYER_2_COLOR = (0,0,0)

# Game constants
EMPTY = 0
PLAYER_1 = 1
PLAYER_2 = 2
PLAYER_1_KING = 3
PLAYER_2_KING = 4
SCOUT_1 = 5
SCOUT_2 = 6

#images



class Piece:
    def __init__(self, name: str, directions: List[str], move_distance: int, owner: int, promoted: False):
        self.name = name
        self.directions = directions
        self.move_distance = move_distance
        self.owner = owner
        self.promoted = False

class Game:
    def __init__(self):
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = PLAYER_1
        self.pieces_in_hand = {PLAYER_1: NUMBER_OF_PIECES, PLAYER_2: NUMBER_OF_PIECES}
        self.selected_piece = None
        self.valid_moves = []
        self.kings_placed = {PLAYER_1: False, PLAYER_2: False}
        self.game_over = False  # Add this
        self.winner = None  # Add this
        self.reserve_selected = False
        self.selected_reserve_piece = None

        self.background_2 = pygame.image.load("background_2.png")
        self.background_2 = pygame.transform.scale(self.background_2, (WINDOW_SIZE, WINDOW_SIZE))
        self.place_sound = pygame.mixer.Sound("place_sound.mp3")  # Replace with actual file path
        self.slide_sound = pygame.mixer.Sound("slide_sound.mp3")
        self.pick_up = pygame.mixer.Sound("pick_up.mp3")

        self.background = pygame.image.load("background.png")
        self.background = pygame.transform.scale(self.background, (BOARD_SIZE * CELL_SIZE, BOARD_SIZE * CELL_SIZE))

        self.player1_reserve = [
            ["Advisor", "Advisor"],  # First row: 2 advisors
            ["Official"] * 7,
            ["Palace"]
        ]
        self.player2_reserve = [
            ["Advisor", "Advisor"],
            ["Official"] * 7,
            ["Palace"]
        ]

    def is_king_placement_phase(self):
        """Check if we're still in the king placement phase"""
        return not (self.kings_placed[PLAYER_1] and self.kings_placed[PLAYER_2])

    def is_enemy_piece(self, piece, player) -> bool:
        if piece.owner != player:
            return True
        else:
            return False

    def demote(self, row, col):
        piece_to_demote = self.board[row][col]
        piece_to_demote.promoted = False

        demotion_settings = {
            "Official": ([(1, 0), (0, 1), (-1, 0), (0, -1)], 1),
            "Advisor": ([(1, 1), (1, -1), (-1, -1), (-1, 1)], 3),
            "Monarch": ([(-1, 0), (1, 0), (0, -1), (0, 1),
                         (-1, -1), (1, 1), (-1, 1), (1, -1)], 2)
        }

        if piece_to_demote.name in demotion_settings:
            piece_to_demote.directions, piece_to_demote.move_distance = demotion_settings[piece_to_demote.name]

    def check_board_promotions(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece != EMPTY:
                    action = self.should_I_promote_piece if self.has_friendly_adjacent_pieces(row, col) else self.demote
                    action(row, col)

    def check_reserve_click(self, mouse_x, mouse_y):
        # Calculate reserve area boundaries
        reserve_start_x = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + CELL_SIZE
        reserve_end_x = WINDOW_SIZE
        piece_spacing = CELL_SIZE * 0.8

        # Reserve area boundaries for both players
        reserve_areas = {
            PLAYER_1: (60, WINDOW_SIZE // 2, self.player1_reserve),
            PLAYER_2: (WINDOW_SIZE // 2 + 40, WINDOW_SIZE, self.player2_reserve)
        }

        # Early return if click is outside reserve area x-coordinates
        if mouse_x < reserve_start_x or mouse_x > reserve_end_x:
            return False

        # Helper function to process reserve click
        def process_reserve_click(start_y, end_y, reserve, player):
            if start_y <= mouse_y <= end_y:
                row = int((mouse_y - start_y) // piece_spacing)
                col = int((mouse_x - reserve_start_x) // piece_spacing)

                if row < len(reserve) and col < len(reserve[row]):
                    self.selected_reserve_piece = {
                        'player': player,
                        'row': row,
                        'col': col,
                        'piece_type': reserve[row][col]
                    }
                    self.pick_up.play()
                    return True
            return False

        # Check the current player's reserve area
        if self.current_player in reserve_areas:
            start_y, end_y, reserve = reserve_areas[self.current_player]
            if process_reserve_click(start_y, end_y, reserve, self.current_player):
                return True

        self.selected_reserve_piece = None
        return False

    def has_friendly_adjacent_pieces(self, row, col):
        piece = self.board[row][col]
        if piece == EMPTY:
            return set()

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
        adjacent_pieces = {
            self.board[new_row][new_col].name
            for dx, dy in directions
            if 0 <= (new_row := row + dx) < BOARD_SIZE and 0 <= (new_col := col + dy) < BOARD_SIZE
               and (adjacent_piece := self.board[new_row][new_col]) != EMPTY
               and adjacent_piece.owner == piece.owner
        }

        return adjacent_pieces

    def get_valid_moves(self, row, col):
        """Get valid moves based on piece type."""
        moves = []
        moving_piece = self.board[row][col]
        player = moving_piece.owner

        for dx, dy in moving_piece.directions:
            for distance in range(1, moving_piece.move_distance + 1):
                new_row, new_col = row + dx * distance, col + dy * distance

                if not (0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE):
                    break  # Stop if we go off the board

                target_square = self.board[new_row][new_col]

                if target_square == EMPTY:
                    moves.append((new_row, new_col))
                elif self.is_enemy_piece(target_square, player):
                    if moving_piece.name != "Advisor" or moving_piece.promoted:
                        moves.append((new_row, new_col))  # Allow attack
                    break  # Stop after hitting any piece
                else:
                    break  # Stop if we hit our own piece

        return moves

    def should_I_promote_piece(self, row, col):
        self.demote(row, col)
        promoting_piece = self.board[row][col]
        adjacent_pieces = self.has_friendly_adjacent_pieces(row, col)

        if not adjacent_pieces:
            return

        def promote(piece, move_distance_increase=0, new_directions=None):
            piece.promoted = True
            piece.move_distance += move_distance_increase
            if new_directions:
                piece.directions += new_directions

        name = promoting_piece.name

        if name == "Monarch":
            if {"Official", "Advisor"}.issubset(adjacent_pieces):
                promote(promoting_piece, move_distance_increase=1)

        elif name == "Official":
            if "Monarch" in adjacent_pieces:
                promote(promoting_piece, new_directions=[(1, 1), (1, -1), (-1, -1), (-1, 1)])
            elif "Advisor" in adjacent_pieces:
                promote(promoting_piece, move_distance_increase=2)
            elif "Official" in adjacent_pieces:
                promote(promoting_piece, move_distance_increase=1)

        elif name == "Advisor":
            if "Monarch" in adjacent_pieces or "Official" in adjacent_pieces:
                promote(promoting_piece)
            elif "Advisor" in adjacent_pieces:
                promoting_piece.directions += [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def move_piece(self, from_pos, to_pos):
        """Handle piece movement and capture logic"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        # Get the moving piece and the target square
        moving_piece = self.board[from_row][from_col]
        target_square = self.board[to_row][to_col]
        current_player = moving_piece.owner

        # Determine enemy player and reserve to update
        enemy_player = PLAYER_2 if current_player == PLAYER_1 else PLAYER_1
        reserve_to_edit = self.player1_reserve if current_player == PLAYER_1 else self.player2_reserve

        # Check if the target square contains an enemy piece
        if target_square != EMPTY and target_square.owner == enemy_player:
            captured_piece_name = target_square.name
            # Handle special cases for capturing important pieces
            if captured_piece_name == "Monarch":
                print(f"{'Black' if current_player == PLAYER_2 else 'White'} wins by capturing the opponent's Monarch!")
                self.game_over = True
                self.winner = current_player
            else:
                # Add captured piece to the current player's reserve
                piece_reserve = reserve_to_edit[0] if captured_piece_name == "Advisor" else reserve_to_edit[1]
                piece_reserve.append(captured_piece_name)
                self.pieces_in_hand[current_player] += 1
                print(
                    f"Captured {captured_piece_name}! Player {current_player} now has {self.pieces_in_hand[current_player]} pieces")

        # Move the piece
        print(f"Player {moving_piece.owner} moved {moving_piece.name} to: {to_row},{to_col}")
        self.board[to_row][to_col] = moving_piece
        self.board[from_row][from_col] = EMPTY

    def get_valid_placement_squares(self):
        valid_squares = set()

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]

                # Skip empty or opponent's pieces
                if piece == EMPTY or piece.owner != self.current_player:
                    continue

                area_size = PALACE_AREA  # You can change this value to any other number

                if piece.name == "Palace":
                    # Mark the area around the Palace (from row - (area_size // 2) to row + (area_size // 2), col - (area_size // 2) to col + (area_size // 2))
                    for i in range(row - (area_size // 2), row + (area_size // 2) + 1):
                        for j in range(col - (area_size // 2), col + (area_size // 2) + 1):
                            # Make sure the indices are within board bounds
                            if 0 <= i < BOARD_SIZE and 0 <= j < BOARD_SIZE:
                                valid_squares.add((i, j))

                else:
                    # Get valid moves for non-Palace pieces
                    valid_squares.update(self.get_valid_moves(row, col))

        return valid_squares

    def handle_click(self, row, col):
        if self.game_over:
            return

        # King placement phase
        if self.is_king_placement_phase():
            if self.board[row][col] == EMPTY:
                king_to_place = Piece("Monarch", [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)],
                                      2, self.current_player, False)
                self.board[row][col] = king_to_place
                self.kings_placed[self.current_player] = True
                self.current_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2

                self.place_sound.play()
            return

        # First priority: If we have a piece selected, handle movement
        if self.selected_piece:
            if (row, col) in self.valid_moves:
                self.move_piece(self.selected_piece, (row, col))
                self.check_board_promotions()
                self.selected_piece = None
                self.valid_moves = []

                if not self.game_over:  # Only switch players if game isn't over
                    self.current_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2

                # Play slide sound when a piece is moved
                self.slide_sound.play()

            elif (row, col) == self.selected_piece:
                self.selected_piece = None
                self.valid_moves = []

        # Second priority: If clicking own piece (regular or king), select it
        elif self.board[row][col] != EMPTY and self.board[row][col].owner == self.current_player:
            self.selected_piece = (row, col)
            self.valid_moves = self.get_valid_moves(row, col)

        # Last priority: If clicking empty space and have pieces, try to place a new piece
        elif self.board[row][col] == EMPTY and self.reserve_selected == True:
            if self.selected_reserve_piece:  # Ensure selected_reserve_piece is not None
                if self.current_player == PLAYER_1:
                    reserve_to_edit = self.player1_reserve
                else:
                    reserve_to_edit = self.player2_reserve

                piece_from_reserve = self.selected_reserve_piece
                if piece_from_reserve['piece_type'] == "Official":
                    piece_to_place = Piece("Official", [(1, 0), (0, 1), (-1, 0), (0, -1)], 1, self.current_player,
                                           False)
                elif piece_from_reserve['piece_type'] == "Advisor":
                    piece_to_place = Piece("Advisor", [(1, 1), (1, -1), (-1, -1), (-1, 1)], 3, self.current_player,
                                           False)
                elif piece_from_reserve['piece_type'] == "Palace":
                    piece_to_place = Piece("Palace", [], 0, self.current_player, False)

                valid_placements = self.get_valid_placement_squares()

                if (row, col) in valid_placements:
                    self.reserve_selected = False
                    self.board[row][col] = piece_to_place
                    self.check_board_promotions()

                    self.pieces_in_hand[self.current_player] -= 1
                    self.selected_piece = None
                    self.valid_moves = []
                    self.current_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2

                    # Update reserves based on the piece placed
                    if piece_from_reserve['piece_type'] == "Advisor":
                        reserve_to_edit[0].pop()  # Removes and returns the last advisor
                    if piece_from_reserve['piece_type'] == "Official":
                        reserve_to_edit[1].pop()  # Removes and returns the last official
                    if piece_from_reserve['piece_type'] == "Palace":
                        reserve_to_edit[2].pop()

                    print(f"Player {self.board[row][col].owner} placed {self.board[row][col].name} at: {row},{col}")

                    # Play place sound when a piece is placed
                    self.place_sound.play()

                else:
                    print("Invalid placement: Must place next to existing pieces")

    def draw(self, screen):


        screen.blit(self.background_2, (0, 0))  # This covers the whole screen



        # Draw the background (wood pattern) behind the grid (just the board area)
        screen.blit(self.background, (GRID_OFFSET, GRID_OFFSET))

        # Draw the grid on top of the wood pattern
        for i in range(BOARD_SIZE + 1):
            pygame.draw.line(screen, GRID_COLOR,
                             (GRID_OFFSET + i * CELL_SIZE, GRID_OFFSET),
                             (GRID_OFFSET + i * CELL_SIZE, GRID_OFFSET + BOARD_SIZE * CELL_SIZE))
            pygame.draw.line(screen, GRID_COLOR,
                             (GRID_OFFSET, GRID_OFFSET + i * CELL_SIZE),
                             (GRID_OFFSET + BOARD_SIZE * CELL_SIZE, GRID_OFFSET + i * CELL_SIZE))

        # Show valid placement squares for piece placement phase
        if not self.selected_piece and not self.is_king_placement_phase() and len(
                self.player1_reserve[0] + self.player1_reserve[1]) > 0 and self.reserve_selected:
            valid_placements = self.get_valid_placement_squares()
            for row, col in valid_placements:
                if self.board[row][col] == EMPTY:  # Only highlight empty squares
                    color = PLACE_HIGHLIGHT_PLAYER1 if self.current_player == PLAYER_1 else PLACE_HIGHLIGHT_PLAYER2
                    pygame.draw.rect(screen, color,
                                     (GRID_OFFSET + col * CELL_SIZE,
                                      GRID_OFFSET + row * CELL_SIZE,
                                      CELL_SIZE, CELL_SIZE))

        # Draw valid moves for selected piece
        self.draw_valid_moves(screen)

        # Draw the selected piece highlight
        if self.selected_piece:
            row, col = self.selected_piece
            pygame.draw.rect(screen, RED,
                             (GRID_OFFSET + col * CELL_SIZE,
                              GRID_OFFSET + row * CELL_SIZE,
                              CELL_SIZE, CELL_SIZE))

        # Draw the pieces on the board
        self.draw_pieces_on_board(screen)

        # Draw piece reserve area on the right side
        self.draw_piece_reserve(screen)

        # Draw phase and current player info at the top
        self.draw_game_info(screen)

        # Draw selected reserve piece highlight
        if self.selected_reserve_piece:
            self.draw_selected_reserve_piece(screen)

    def draw_valid_moves(self, screen):
        """Draw valid moves for selected piece."""
        for row, col in self.valid_moves:
            color = MOVE_HIGHLIGHT_PLAYER1 if self.current_player == PLAYER_1 else MOVE_HIGHLIGHT_PLAYER2
            pygame.draw.rect(screen, color,
                             (GRID_OFFSET + col * CELL_SIZE,
                              GRID_OFFSET + row * CELL_SIZE,
                              CELL_SIZE, CELL_SIZE))

    def draw_pieces_on_board(self, screen):
        """Draw all the pieces on the board."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board[row][col] != EMPTY:
                    piece = self.board[row][col]
                    main_color = WHITE if piece.owner == PLAYER_1 else BLACK
                    contrast_color = BLACK if piece.owner == PLAYER_1 else WHITE

                    # Calculate center position
                    center = (GRID_OFFSET + col * CELL_SIZE + CELL_SIZE // 2,
                              GRID_OFFSET + row * CELL_SIZE + CELL_SIZE // 2)

                    # Draw promotion indicator if piece is promoted
                    if piece.promoted:
                        pygame.draw.circle(screen, RED, center, CELL_SIZE // 2 - 2)

                    # Draw the main piece circle
                    pygame.draw.circle(screen, main_color, center, CELL_SIZE // 2 - 5)

                    # Draw special indicators for different piece types
                    self.draw_piece_type_indicators(screen, piece, center)

    def draw_piece_type_indicators(self, screen, piece, center):
        """Draw special indicators for different piece types."""
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
            # 5x5 area alignment around the Palace
            area_size = PALACE_AREA  # 5x5 area around the Palace
            # Calculate the top-left corner of the 5x5 area
            top_left_x = (center[0] // CELL_SIZE) * CELL_SIZE - (area_size // 2) * CELL_SIZE
            top_left_y = (center[1] // CELL_SIZE) * CELL_SIZE - (area_size // 2) * CELL_SIZE

            # Set the outline color based on the player's color
            outline_color = PLAYER_1_COLOR if piece.owner == PLAYER_1 else PLAYER_2_COLOR

            # Draw the outline of the 5x5 area
            outline_rect = pygame.Rect(top_left_x, top_left_y, area_size * CELL_SIZE, area_size * CELL_SIZE)
            pygame.draw.rect(screen, outline_color, outline_rect, 4)  # Draw just the outline (border)

            # Draw the actual Palace piece in the center of the grid cell
            palace_top_left = (center[0] - CELL_SIZE // 4, center[1] - CELL_SIZE // 4)
            pygame.draw.rect(screen, PURPLE, (palace_top_left[0], palace_top_left[1], CELL_SIZE // 2, CELL_SIZE // 2))

    def draw_piece_reserve(self, screen):
        """Draw the piece reserve area on the right side."""
        reserve_start_x = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + CELL_SIZE
        piece_spacing = CELL_SIZE * 0.8  # Slightly smaller than board pieces

        # Draw headers for piece reserves
        font = pygame.font.Font(None, 36)
        text_white = font.render("White Pieces", True, WHITE)
        text_black = font.render("Black Pieces", True, BLACK)
        screen.blit(text_white, (reserve_start_x, 20))
        screen.blit(text_black, (reserve_start_x, WINDOW_SIZE // 2))

        # Draw White's pieces from reserve array
        self.draw_reserve_pieces(screen, self.player1_reserve, reserve_start_x, 60, WHITE, BLACK)

        # Draw Black's pieces from reserve array
        self.draw_reserve_pieces(screen, self.player2_reserve, reserve_start_x, WINDOW_SIZE // 2 + 40, BLACK, WHITE)

    def draw_reserve_pieces(self, screen, reserve, reserve_start_x, y_offset, piece_color, contrast_color):
        """Draw pieces from the reserve."""
        piece_spacing = CELL_SIZE * 0.8
        for row_idx, row in enumerate(reserve):
            for col_idx, piece_type in enumerate(row):
                # Calculate x and y positions for each piece
                x = reserve_start_x + (col_idx * piece_spacing)
                y = y_offset + (row_idx * piece_spacing)

                # Check if the piece is within the screen width and height
                if x + piece_spacing > WINDOW_SIZE:  # If the piece goes off the screen to the right
                    continue  # Skip drawing this piece
                if y + piece_spacing > WINDOW_SIZE:  # If the piece goes off the screen downward
                    continue  # Skip drawing this piece

                # Draw the piece
                pygame.draw.circle(screen, piece_color,
                                   (int(x + piece_spacing / 2), int(y + piece_spacing / 2)),
                                   int(piece_spacing / 2 - 5))

                # Draw specific piece type (Advisor or Palace)
                if piece_type == "Advisor":
                    pygame.draw.circle(screen, contrast_color,
                                       (int(x + piece_spacing / 2), int(y + piece_spacing / 2)),
                                       int(piece_spacing / 4))
                elif piece_type == "Palace":
                    pygame.draw.rect(screen, PURPLE,
                                     (int(x + piece_spacing / 2 - piece_spacing / 4),
                                      int(y + piece_spacing / 2 - piece_spacing / 4),
                                      piece_spacing / 2, piece_spacing / 2))

    def draw_game_info(self, screen):
        """Draw phase and current player info."""

        display_name = "White" if self.current_player == PLAYER_1 else "Black"

        font = pygame.font.Font(None, 36)
        text3 = font.render(f"Player to move: {display_name}", True, WHITE)
        screen.blit(text3, (10, 10))

        # Draw game over message if applicable
        if self.game_over:
            winner_text = "White Wins!" if self.winner == PLAYER_1 else "Black Wins!"
            text5 = font.render(winner_text, True, GOLD)
            screen.blit(text5, (WINDOW_SIZE // 2 - 100, 10))

    def draw_selected_reserve_piece(self, screen):
        """Draw selected reserve piece highlight."""
        reserve_start_x = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + CELL_SIZE
        piece_spacing = CELL_SIZE * 0.8
        y_offset = 60 if self.selected_reserve_piece['player'] == PLAYER_1 else WINDOW_SIZE // 2 + 40

        x = reserve_start_x + (self.selected_reserve_piece['col'] * piece_spacing)
        y = y_offset + (self.selected_reserve_piece['row'] * piece_spacing)

        pygame.draw.rect(screen, RED, (x, y, piece_spacing, piece_spacing), 2)


def main():
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Board Game Prototype")

    game = Game()
    clock = pygame.time.Clock()

    # Pre-load and pre-scale textures (only done once)


    while True:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Check if a reserve piece is clicked
                reserve_clicked = game.check_reserve_click(mouse_x, mouse_y)

                if reserve_clicked:
                    game.reserve_selected = True
                    # You can add more logic for selecting a reserve piece if needed.

                # Handle the board click if within bounds
                col = (mouse_x - GRID_OFFSET) // CELL_SIZE
                row = (mouse_y - GRID_OFFSET) // CELL_SIZE
                if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                    game.handle_click(row, col)

        game.draw(screen)
        pygame.display.flip()
        clock.tick(15)


if __name__ == "__main__":
    main()
