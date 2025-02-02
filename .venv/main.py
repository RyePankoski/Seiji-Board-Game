import pygame
import sys
from typing import List

# Initialize Pygame
pygame.init()

# Constants
BOARD_SIZE = 13
NUMBER_OF_PIECES = 9
CELL_SIZE = 60  # Made this explicit for clarity
GRID_OFFSET = CELL_SIZE
BOARD_PIXELS = BOARD_SIZE * CELL_SIZE
RESERVE_WIDTH = CELL_SIZE * 4  # Width for the piece reserve area
WINDOW_SIZE = BOARD_PIXELS + (GRID_OFFSET * 2) + RESERVE_WIDTH  # Total window width

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BROWN = (139, 69, 19)
GRID_COLOR = (50, 50, 50)
NEW = (50, 50, 50)

PLACE_HIGHLIGHT_PLAYER1 = (0, 255, 0, 128)
PLACE_HIGHLIGHT_PLAYER2 = (255, 180, 255, 128)
MOVE_HIGHLIGHT_PLAYER1 = (0, 127, 0, 128)
MOVE_HIGHLIGHT_PLAYER2 = (127, 90, 127, 128)

RED = (255, 50, 50)
GOLD = (50, 150, 10)

# Game constants
EMPTY = 0
PLAYER_1 = 1
PLAYER_2 = 2
PLAYER_1_KING = 3
PLAYER_2_KING = 4
SCOUT_1 = 5
SCOUT_2 = 6


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

        self.player1_reserve = [
            ["Advisor", "Advisor"],  # First row: 2 advisors
            ["Official"] * 7  # Second row: 7 officials
        ]
        self.player2_reserve = [
            ["Advisor", "Advisor"],
            ["Official"] * 7
        ]

    def is_king_placement_phase(self):
        """Check if we're still in the king placement phase"""
        return not (self.kings_placed[PLAYER_1] and self.kings_placed[PLAYER_2])

    def is_enemy_piece(self, piece, player) -> bool:
        if piece.owner != player:
            return True
        else:
            return False

    def demote(self,row,col):
        piece_to_demote = self.board[row][col]
        piece_to_demote.promoted = False
        if piece_to_demote.name == "Official":
            piece_to_demote.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
            piece_to_demote.move_distance = 1
        elif piece_to_demote.name == "Advisor":
            piece_to_demote.directions = [(1,1),(1,-1),(-1,-1),(-1,1)]
            piece_to_demote.move_distance = 3
        elif piece_to_demote.name == "Monarch":
            piece_to_demote.directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                                (-1, -1), (1, 1), (-1, 1), (1, -1)]
            piece_to_demote.move_distance = 2

    def check_board_promotions(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece != EMPTY:
                    # Check for adjacent friendly pieces
                    adjacent_pieces = self.has_friendly_adjacent_pieces(row, col)

                    if adjacent_pieces:
                        self.should_I_promote_piece(row,col)
                    else:
                        self.demote(row,col)

    def check_reserve_click(self, mouse_x, mouse_y):
        # Calculate reserve area boundaries
        reserve_start_x = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + CELL_SIZE
        reserve_end_x = WINDOW_SIZE
        piece_spacing = CELL_SIZE * 0.8

        # Define Y boundaries for each player's reserve section
        player1_start_y = 60  # White pieces start after header
        player1_end_y = WINDOW_SIZE // 2
        player2_start_y = WINDOW_SIZE // 2 + 40  # Black pieces start after header
        player2_end_y = WINDOW_SIZE

        # Early return if click is outside reserve area x-coordinates
        if mouse_x < reserve_start_x or mouse_x > reserve_end_x:
            return False

        # Check Player 1 reserve area
        if (self.current_player == PLAYER_1 and
                player1_start_y <= mouse_y <= player1_end_y):

            row = int((mouse_y - player1_start_y) // piece_spacing)
            col = int((mouse_x - reserve_start_x) // piece_spacing)

            if (row < len(self.player1_reserve) and
                    col < len(self.player1_reserve[row])):
                piece_type = self.player1_reserve[row][col]
                self.selected_reserve_piece = {
                    'player': PLAYER_1,
                    'row': row,
                    'col': col,
                    'piece_type': piece_type
                }
                return True

        # Check Player 2 reserve area
        elif (self.current_player == PLAYER_2 and
              player2_start_y <= mouse_y <= player2_end_y):

            row = int((mouse_y - player2_start_y) // piece_spacing)
            col = int((mouse_x - reserve_start_x) // piece_spacing)

            if (row < len(self.player2_reserve) and
                    col < len(self.player2_reserve[row])):
                piece_type = self.player2_reserve[row][col]
                self.selected_reserve_piece = {
                    'player': PLAYER_2,
                    'row': row,
                    'col': col,
                    'piece_type': piece_type
                }
                return True

        self.selected_reserve_piece = None
        return False

    def has_friendly_adjacent_pieces(self, row, col):
        adjacent_pieces = set()
        piece = self.board[row][col]

        if piece == EMPTY:
            return adjacent_pieces

        # Define orthogonal directions: up, down, left, right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in directions:
            new_row = row + dx
            new_col = col + dy

            # Check if the position is within board bounds
            if 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE:
                # Check if there's a piece at this position and it belongs to the same player
                adjacent_piece = self.board[new_row][new_col]
                if adjacent_piece != EMPTY and adjacent_piece.owner == piece.owner:
                    adjacent_pieces.add(adjacent_piece.name)

        return adjacent_pieces

    def get_valid_moves(self, row, col):
        """Get valid moves based on piece type"""
        moves = []
        moving_piece = self.board[row][col]
        player = moving_piece.owner

        directions = moving_piece.directions
        move_distance = moving_piece.move_distance

        for dx, dy in directions:
            for distance in range(1, move_distance + 1):
                new_row = row + (dx * distance)
                new_col = col + (dy * distance)
                if (0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE):
                    target_square = self.board[new_row][new_col]
                    if target_square == EMPTY:
                        moves.append((new_row, new_col))
                    elif self.is_enemy_piece(target_square, player):
                        # Only add attack moves for promoted advisors or non-advisor pieces
                        if moving_piece.name != "Advisor" or moving_piece.promoted:
                            moves.append((new_row, new_col))
                        break  # Stop checking this direction after hitting any piece
                    else:
                        break  # Stop checking this direction if we hit our own piece
                else:
                    break  # Stop if we go off the board
        return moves

    def should_I_promote_piece(self,row,col):

        self.demote(row,col)

        promoting_piece = self.board[row][col]
        adjacent_pieces = self.has_friendly_adjacent_pieces(row,col)

        if adjacent_pieces:
            if promoting_piece.name == "Monarch":
                if "Official" in adjacent_pieces and "Advisor" in adjacent_pieces:
                    promoting_piece.promoted = True
                    promoting_piece.move_distance += 1

            elif promoting_piece.name == "Official":
                promoting_piece.promoted = True
                if "Monarch" in adjacent_pieces:
                    promoting_piece.directions += [(1, 1), (1, -1), (-1, -1), (-1, 1)]
                elif "Advisor" in adjacent_pieces:
                    promoting_piece.move_distance += 2
                elif "Official" in adjacent_pieces:
                    promoting_piece.move_distance += 1

            elif promoting_piece.name == "Advisor":
                if "Monarch" in adjacent_pieces:
                    promoting_piece.promoted = True
                if "Advisor" in adjacent_pieces:
                    promoting_piece.directions += [(1, 0), (-1, 0), (0, 1), (0, -1)]
                if "Official" in adjacent_pieces:
                    promoting_piece.promoted = True

    def move_piece(self, from_pos, to_pos):
        """Handle piece movement and capture logic"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        # Check if we're capturing a piece
        target_square = self.board[to_row][to_col]
        moving_piece = self.board[from_row][from_col]
        current_player = moving_piece.owner


        if current_player == PLAYER_1:
            enemy_player = PLAYER_2
            reserve_to_edit = self.player1_reserve
        else:
            enemy_player = PLAYER_1
            reserve_to_edit = self.player2_reserve

        if target_square != EMPTY and target_square.owner == enemy_player:
            if target_square.name == "Monarch":
                print("Black wins by capturing White's Monarch!")
                self.game_over = True
                self.winner = PLAYER_2
            elif target_square.name == "Monarch":
                print("White wins by capturing Black's Monarch!")
                self.game_over = True
                self.winner = PLAYER_1
            elif target_square.name == "Official":
                self.pieces_in_hand[current_player] += 1
                reserve_to_edit[1].append("Official")
                print(f"Captured Official! Player {current_player} now has {self.pieces_in_hand[current_player]} pieces")
            elif target_square.name == "Advisor":
                self.pieces_in_hand[current_player] += 1
                reserve_to_edit[0].append("Advisor")
                print(f"Captured Advisor! Player {current_player} now has {self.pieces_in_hand[current_player]} pieces")

        # Move the piece
        print(f"Player {moving_piece.owner} moved {self.board[from_row][from_col].name} to: {to_row},{to_col}")
        self.board[to_row][to_col] = self.board[from_row][from_col]
        self.board[from_row][from_col] = EMPTY

    def get_valid_placement_squares(self):
        valid_squares = set()  # Using a set to avoid duplicates

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                # If we find our piece
                if self.board[row][col] != 0:
                    if self.board[row][col].owner == self.current_player:
                        valid_moves = self.get_valid_moves(row, col)
                        valid_squares.update(valid_moves)

        return valid_squares

    def handle_click(self, row, col):
        """Handle both piece placement and movement"""
        if self.game_over:  # Don't process clicks if game is over
            return

        # King placement phase
        if self.is_king_placement_phase():
            if self.board[row][col] == EMPTY:

                king_to_place = Piece("Monarch", [(-1, 0), (1, 0), (0, -1), (0, 1),(-1,-1),(1,1),(-1,1),(1,-1)], 2, self.current_player , False)

                self.board[row][col] = king_to_place

                self.kings_placed[self.current_player] = True
                self.current_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2

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

            elif (row, col) == self.selected_piece:
                self.selected_piece = None
                self.valid_moves = []


        # Second priority: If clicking own piece (regular or king), select it
        elif self.board[row][col] != EMPTY and self.board[row][col].owner == self.current_player:
            self.selected_piece = (row, col)
            self.valid_moves = self.get_valid_moves(row, col)

        # Last priority: If clicking empty space and have pieces, try to place a new piece
        elif self.board[row][col] == EMPTY and self.reserve_selected == True:

            if self.current_player == PLAYER_1:
                reserve_to_edit = self.player1_reserve
            else:
                reserve_to_edit = self.player2_reserve


            piece_from_reserve = self.selected_reserve_piece

            if piece_from_reserve['piece_type'] == "Official":
                piece_to_place = Piece("Official",[(1,0),(0,1),(-1,0),(0,-1)],1, self.current_player, False)
            if piece_from_reserve['piece_type'] == "Advisor":
                piece_to_place = Piece("Advisor",[(1,1),(1,-1),(-1,-1),(-1,1)],3, self.current_player, False)

            valid_placements = self.get_valid_placement_squares()

            if (row, col) in valid_placements:
                self.reserve_selected = False
                self.board[row][col] = piece_to_place

                self.check_board_promotions()

                self.pieces_in_hand[self.current_player] -= 1
                self.selected_piece = None
                self.valid_moves = []
                self.current_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2


                if piece_from_reserve['piece_type'] == "Advisor":
                    reserve_to_edit[0].pop()  # Removes and returns the last advisor
                if piece_from_reserve['piece_type'] == "Official":
                    reserve_to_edit[1].pop()  # Removes and returns the last official

                print(f"Player {self.board[row][col].owner} placed {self.board[row][col].name} at: {row},{col}")


            else:
                print("Invalid placement: Must place next to existing pieces")


    def draw(self, screen):
        # Draw the wooden background
        screen.fill(BROWN)

        # Draw the grid
        for i in range(BOARD_SIZE + 1):
            pygame.draw.line(screen, GRID_COLOR,
                             (GRID_OFFSET + i * CELL_SIZE, GRID_OFFSET),
                             (GRID_OFFSET + i * CELL_SIZE, GRID_OFFSET + BOARD_SIZE * CELL_SIZE))
            pygame.draw.line(screen, GRID_COLOR,
                             (GRID_OFFSET, GRID_OFFSET + i * CELL_SIZE),
                             (GRID_OFFSET + BOARD_SIZE * CELL_SIZE, GRID_OFFSET + i * CELL_SIZE))

        # If no piece is selected, show valid placement squares
        if not self.selected_piece and not self.is_king_placement_phase() and len(
                self.player1_reserve[0] + self.player1_reserve[1]) > 0 and self.reserve_selected == True:
            valid_placements = self.get_valid_placement_squares()

            for row, col in valid_placements:
                if self.board[row][col] == EMPTY:  # Only highlight empty squares
                    if self.current_player == PLAYER_1:
                        pygame.draw.rect(screen, PLACE_HIGHLIGHT_PLAYER1,
                                         (GRID_OFFSET + col * CELL_SIZE,
                                          GRID_OFFSET + row * CELL_SIZE,
                                          CELL_SIZE, CELL_SIZE))
                    else:
                        pygame.draw.rect(screen, PLACE_HIGHLIGHT_PLAYER2,
                                         (GRID_OFFSET + col * CELL_SIZE,
                                          GRID_OFFSET + row * CELL_SIZE,
                                          CELL_SIZE, CELL_SIZE))

        # Draw valid moves for selected piece
        for row, col in self.valid_moves:
            if self.current_player == PLAYER_1:
                pygame.draw.rect(screen, MOVE_HIGHLIGHT_PLAYER1,
                                 (GRID_OFFSET + col * CELL_SIZE,
                                  GRID_OFFSET + row * CELL_SIZE,
                                  CELL_SIZE, CELL_SIZE))
            else:
                pygame.draw.rect(screen, MOVE_HIGHLIGHT_PLAYER2,
                                 (GRID_OFFSET + col * CELL_SIZE,
                                  GRID_OFFSET + row * CELL_SIZE,
                                  CELL_SIZE, CELL_SIZE))

        # Draw the selected piece highlight
        if self.selected_piece:
            row, col = self.selected_piece
            pygame.draw.rect(screen, RED,
                             (GRID_OFFSET + col * CELL_SIZE,
                              GRID_OFFSET + row * CELL_SIZE,
                              CELL_SIZE, CELL_SIZE))

        # Draw the pieces on the board
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board[row][col] != EMPTY:
                    piece = self.board[row][col]
                    # Set main piece color based on owner
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
                    if piece.name == "Monarch":
                        # Add crown for kings
                        pygame.draw.circle(screen, GOLD, center, CELL_SIZE // 4)
                    elif piece.name == "Advisor":
                        # Add contrasting inner circle for advisors (matching reserve style)
                        pygame.draw.circle(screen, contrast_color, center, CELL_SIZE // 4)

        # Draw piece reserve area on the right side
        reserve_start_x = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + CELL_SIZE
        piece_spacing = CELL_SIZE * 0.8  # Slightly smaller than board pieces

        # Draw headers for piece reserves
        font = pygame.font.Font(None, 36)
        text_white = font.render("White Pieces", True, WHITE)
        text_black = font.render("Black Pieces", True, BLACK)
        screen.blit(text_white, (reserve_start_x, 20))
        screen.blit(text_black, (reserve_start_x, WINDOW_SIZE // 2))

        # Draw White's pieces from reserve array
        for row_idx, row in enumerate(self.player1_reserve):
            for col_idx, piece_type in enumerate(row):
                x = reserve_start_x + (col_idx * piece_spacing)
                y = 60 + (row_idx * piece_spacing)
                pygame.draw.circle(screen, WHITE,
                                   (int(x + piece_spacing / 2), int(y + piece_spacing / 2)),
                                   int(piece_spacing / 2 - 5))
                if piece_type == "Advisor":
                    # Draw a small indicator for advisor pieces
                    pygame.draw.circle(screen, BLACK,
                                       (int(x + piece_spacing / 2), int(y + piece_spacing / 2)),
                                       int(piece_spacing / 4))

        # Draw Black's pieces from reserve array
        for row_idx, row in enumerate(self.player2_reserve):
            for col_idx, piece_type in enumerate(row):
                x = reserve_start_x + (col_idx * piece_spacing)
                y = WINDOW_SIZE // 2 + 40 + (row_idx * piece_spacing)
                pygame.draw.circle(screen, BLACK,
                                   (int(x + piece_spacing / 2), int(y + piece_spacing / 2)),
                                   int(piece_spacing / 2 - 5))
                if piece_type == "Advisor":
                    # Draw a small indicator for advisor pieces
                    pygame.draw.circle(screen, WHITE,
                                       (int(x + piece_spacing / 2), int(y + piece_spacing / 2)),
                                       int(piece_spacing / 4))

        # Draw phase and current player info at the top
        text3 = font.render(f"Player to move: {self.current_player}", True, WHITE)
        screen.blit(text3, (10, 10))

        # Draw game over message if applicable
        if self.game_over:
            winner_text = "White Wins!" if self.winner == PLAYER_1 else "Black Wins!"
            text5 = font.render(winner_text, True, GOLD)
            screen.blit(text5, (WINDOW_SIZE // 2 - 100, 10))

        # Draw selected reserve piece highlight
        if self.selected_reserve_piece != None:
            reserve_start_x = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + CELL_SIZE
            piece_spacing = CELL_SIZE * 0.8
            if self.selected_reserve_piece['player'] == PLAYER_1:
                y_offset = 60
            else:
                y_offset = WINDOW_SIZE // 2 + 40

            x = reserve_start_x + (self.selected_reserve_piece['col'] * piece_spacing)
            y = y_offset + (self.selected_reserve_piece['row'] * piece_spacing)

            pygame.draw.rect(screen, RED,
                             (x, y, piece_spacing, piece_spacing), 2)

def main():
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Board Game Prototype")

    game = Game()
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                reserve_clicked = game.check_reserve_click(mouse_x, mouse_y)

                if reserve_clicked:
                    game.reserve_selected = True

                    # Your existing board click handling code
                col = (mouse_x - GRID_OFFSET) // CELL_SIZE
                row = (mouse_y - GRID_OFFSET) // CELL_SIZE
                if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                    game.handle_click(row, col)

        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
