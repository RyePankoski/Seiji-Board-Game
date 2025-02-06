import pygame
from pygame import mixer
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, BOARD_SIZE, CELL_SIZE, GRID_OFFSET
from game_state import GameState
from UI import MenuScreen
from draw_utils import DrawUtils
from main_ultilities import MainUtilities
from constants import *
from network_manager import NetworkManager
import queue
import threading
from piece import Piece
from UI import PostGameScreen
# Initialize Pygame
pygame.init()
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
        self.monarch_placement_phase = True

        self.network_manager = NetworkManager()
        self.multiplayer = False

        self.place_sound = pygame.mixer.Sound("Sounds/place_sound.mp3")  # Replace with actual file path
        self.slide_sound = pygame.mixer.Sound("Sounds/slide_sound.mp3")
        self.pick_up = pygame.mixer.Sound("Sounds/pick_up.mp3")
        self.capture = pygame.mixer.Sound("Sounds/capture.mp3")
        self.promote_sound = pygame.mixer.Sound("Sounds/promote.mp3")
        self.endgame = pygame.mixer.Sound("Sounds/endgame.mp3")
        self.select_piece = pygame.mixer.Sound("Sounds/advisor.mp3")
        self.de_select = pygame.mixer.Sound("Sounds/de-select.mp3")

        self.is_muted = False
        self.mute_button_rect = pygame.Rect(10, WINDOW_HEIGHT - 70, 60, 60)

        self.background = pygame.image.load("Textures/background.png")
        self.background = pygame.transform.scale(self.background, (BOARD_SIZE * CELL_SIZE, BOARD_SIZE * CELL_SIZE))
        self.background_2 = pygame.image.load("Textures/background_2.png")
        self.background_2 = pygame.transform.scale(self.background_2, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.table_texture = pygame.image.load("Textures/tables.png").convert_alpha()

        self.resign_button_rect = pygame.Rect(WINDOW_WIDTH - 120, 10, 100, 40)  # Top right corner
        self.resign_hover = False

        self.message_log = []
        self.most_recent_message = None
        self.max_messages = 10  # Maximum number of messages to show
        self.log_font = pygame.font.Font(None, 24)  # Font for the log
        self.log_rect = pygame.Rect(
            WINDOW_WIDTH - 300,  # X position (300 pixels from right)
            WINDOW_HEIGHT - 160,  # Y position (adjusted up since box is smaller)
            280,  # Width of log box
            140  # Height reduced to 70% of original (180 * 0.7 = 126)
        )

        self.player1_reserve = [
            ["Advisor"] * ADVISOR_NUMBER,  # First row: 2 advisors
            ["Official"] * OFFICIAL_NUMBER,
            ["Palace"] * PALACE_NUMBER
        ]
        self.player2_reserve = [
            ["Advisor"] * ADVISOR_NUMBER,  # First row: 2 advisors
            ["Official"] * OFFICIAL_NUMBER,
            ["Palace"] * PALACE_NUMBER
        ]

    def network_finish_move(self):
        """Called at the end of each move to update network state"""
        if self.multiplayer:
            self.network_manager.send_game_state(
                self.board,
                self.current_player,
                self.player1_reserve,
                self.player2_reserve,
                self.most_recent_message
            )

    def reset_game(self):
        """Reset the game state for a new game"""
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = PLAYER_1
        self.pieces_in_hand = {PLAYER_1: NUMBER_OF_PIECES, PLAYER_2: NUMBER_OF_PIECES}
        self.selected_piece = None
        self.valid_moves = []
        self.kings_placed = {PLAYER_1: False, PLAYER_2: False}
        self.game_over = False
        self.winner = None
        self.reserve_selected = False
        self.selected_reserve_piece = None
        self.monarch_placement_phase = True

        # Reset piece reserves
        self.player1_reserve = [
            ["Advisor"] * ADVISOR_NUMBER,
            ["Official"] * OFFICIAL_NUMBER,
            ["Palace"] * PALACE_NUMBER
        ]
        self.player2_reserve = [
            ["Advisor"] * ADVISOR_NUMBER,
            ["Official"] * OFFICIAL_NUMBER,
            ["Palace"] * PALACE_NUMBER
        ]

        # Clear message log
        self.message_log = []
        self.most_recent_message = None

    def handle_resign(self):
        """Handle the resignation of current player"""
        if not self.game_over:
            self.game_over = True
            self.winner = PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1
            self.add_to_log(f"Player {self.current_player} resigned")
            if not self.is_muted:
                self.endgame.play()
            self.network_finish_move()

    def process_network_updates(self):
        """Process any pending network updates"""
        if self.multiplayer:
            self.network_manager.process_network_updates(self)

    def add_to_log(self, message):
        """Add a new message to the game log"""
        self.message_log.append(message)
        self.most_recent_message = message
        if len(self.message_log) > self.max_messages:
            self.message_log.pop(0)  # Remove oldest message if we exceed max

    def is_king_placement_phase(self):
        """Check if we're still in the king placement phase by counting Monarchs on the board"""
        monarch_count = sum(
            1 for row in self.board
            for piece in row
            if piece != EMPTY and piece.name == "Monarch"
        )

        if monarch_count == 2:
            self.monarch_placement_phase = False

        return monarch_count < 2
        

    def did_someone_win(self):
        if self.monarch_placement_phase:
            return False

        monarchs = {PLAYER_1: False, PLAYER_2: False}

        for row in self.board:
            for piece in row:
                if piece != EMPTY and piece.name == "Monarch":
                    monarchs[piece.owner] = True

        for player, opponent in [(PLAYER_1, PLAYER_2), (PLAYER_2, PLAYER_1)]:
            if not monarchs[player]:
                self.game_over, self.winner = True, opponent
                if not self.is_muted:
                    self.endgame.play()
                return True

        return False

    def is_enemy_piece(self, piece, player) -> bool:
        if piece.owner != player:
            return True
        else:
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
        piece = self.board[row][col]
        player = piece.owner

        for dx, dy in piece.directions:
            for dist in range(1, piece.move_distance + 1):
                new_row, new_col = row + dx * dist, col + dy * dist

                if not (0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE):
                    break  # Off the board

                target = self.board[new_row][new_col]

                if target == EMPTY:
                    moves.append((new_row, new_col))
                else:
                    if self.is_enemy_piece(target, player) and (piece.name != "Advisor" or piece.promoted):
                        moves.append((new_row, new_col))  # Attack allowed
                    break  # Stop after hitting any piece
        return moves

    def get_valid_placement_squares(self):
        valid_squares = set()

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]

                if piece == EMPTY or piece.owner != self.current_player:
                    continue

                if piece.name == "Palace":
                    half_area = PALACE_AREA // 2
                    for i in range(max(0, row - half_area), min(BOARD_SIZE, row + half_area + 1)):
                        for j in range(max(0, col - half_area), min(BOARD_SIZE, col + half_area + 1)):
                            valid_squares.add((i, j))
                else:
                    valid_squares.update(self.get_valid_moves(row, col))

        return valid_squares

    def promote(self, piece, move_distance=0, new_directions=None):
        was_promoted = piece.promoted

        # Always update stats
        piece.promoted = True
        piece.move_distance = move_distance
        if new_directions:
            piece.directions = new_directions

        # Only play sound for new promotions
        if not was_promoted:
            print(f"Promoting: {piece.name}")
            self.promote_sound.play()

    def demote(self, row, col):
        if self.board[row][col] and self.board[row][col].promoted:
            piece_to_demote = self.board[row][col]
            piece_to_demote.promoted = False

            demotion_settings = {
                "Official": ([(1, 0), (0, 1), (-1, 0), (0, -1)], 1),
                "Advisor": ([(1, 1), (1, -1), (-1, -1), (-1, 1)], 3),
                "Monarch": ([(-1, 0), (1, 0), (0, -1), (0, 1),
                             (-1, -1), (1, 1), (-1, 1), (1, -1)], 1)
            }

            if piece_to_demote.name in demotion_settings:
                piece_to_demote.directions, piece_to_demote.move_distance = demotion_settings[piece_to_demote.name]

    def handle_piece_status(self, row, col):
        """Handle all piece promotion/demotion logic including promotion type changes"""
        piece = self.board[row][col]
        if piece == EMPTY:
            return

        adj_pieces = self.has_friendly_adjacent_pieces(row, col)

        # First check for demotion
        should_demote = (
                not adj_pieces or
                adj_pieces == {"Palace"} or
                (piece.name == "Monarch" and not adj_pieces) or
                (piece.name == "Advisor" and "Monarch" not in adj_pieces) or
                (piece.name == "Official" and "Monarch" not in adj_pieces and "Advisor" not in adj_pieces)
        )

        if should_demote and piece.promoted:
            self.demote(row, col)
            return

        # Special case for promoted Official
        if piece.name == "Official" and piece.promoted:
            if "Monarch" in adj_pieces:
                # King promotion takes precedence
                self.promote(piece, 1, new_directions=[
                    (1, 1), (1, -1), (-1, -1), (-1, 1),
                    (1, 0), (0, 1), (-1, 0), (0, -1)
                ])
            elif "Advisor" in adj_pieces:
                # Revert to Advisor promotion if King moved away but Advisor still adjacent
                self.promote(piece, move_distance=2, new_directions=[(1, 0), (0, 1), (-1, 0), (0, -1)])
            return

        # Handle initial promotions for unpromoted pieces
        if piece.name == "Monarch" and adj_pieces and adj_pieces != {"Palace"}:
            if not piece.promoted:
                self.promote(piece, move_distance=2)

        elif piece.name == "Advisor":
            if "Monarch" in adj_pieces and not piece.promoted:
                self.promote(piece, 2, new_directions=[
                    (1, 1), (1, -1), (-1, -1), (-1, 1),
                    (1, 0), (0, 1), (-1, 0), (0, -1)
                ])

        elif piece.name == "Official":
            if "Monarch" in adj_pieces and not piece.promoted:
                self.promote(piece, 1, new_directions=[
                    (1, 1), (1, -1), (-1, -1), (-1, 1),
                    (1, 0), (0, 1), (-1, 0), (0, -1)
                ])
            elif "Advisor" in adj_pieces and not piece.promoted:
                self.promote(piece, move_distance=2)

    def check_board_promotions(self):
        """Check all pieces on the board for promotion/demotion"""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                self.handle_piece_status(row, col)

    def move_piece(self, from_pos, to_pos):
        """Handle piece movement and capture logic"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        piece = self.board[from_row][from_col]
        target = self.board[to_row][to_col]
        player = piece.owner
        enemy = PLAYER_2 if player == PLAYER_1 else PLAYER_1
        reserve = self.player1_reserve if player == PLAYER_1 else self.player2_reserve

        # Handle capture
        if target != EMPTY and target.owner == enemy:
            if target.name != "Palace":
                reserve[0 if target.name == "Advisor" else 1].append(target.name)
                self.pieces_in_hand[player] += 1
            self.capture.play()
            action = f"captured {target.name} at {to_col + 1},{BOARD_SIZE - to_row}"
        else:
            action = f"moved {piece.name} to: {to_col + 1},{BOARD_SIZE - to_row}"

        self.add_to_log(f"Player {player} {action}")
        self.board[to_row][to_col], self.board[from_row][from_col] = piece, EMPTY

    def deselect(self):
        self.selected_piece = None
        self.selected_reserve_piece = None
        self.reserve_selected = False
        self.valid_moves = []

    def place_new_piece(self, row, col):

        if (row, col) not in self.get_valid_placement_squares():
            return False

        # Define piece configurations in a dictionary
        piece_configs = {
            "Official": ([(1, 0), (0, 1), (-1, 0), (0, -1)], 1, 1, False),
            "Advisor": ([(1, 1), (1, -1), (-1, -1), (-1, 1)], 3, 0, False),
            "Palace": ([], 0, 2, False)
        }

        piece_type = self.selected_reserve_piece['piece_type']
        moves, value, reserve_index, promotion_status = piece_configs[piece_type]

        # Create and place the piece
        piece_to_place = Piece(piece_type, moves, value, self.current_player, False)
        self.board[row][col] = piece_to_place

        # Update game state
        reserve = self.player1_reserve if self.current_player == PLAYER_1 else self.player2_reserve
        reserve[reserve_index].pop()

        self.reserve_selected = False
        self.pieces_in_hand[self.current_player] -= 1
        self.selected_piece = None
        self.valid_moves = []
        self.current_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2

        # Log and sound
        self.add_to_log(f"Player {self.board[row][col].owner} placed {piece_type} at: {col + 1},{BOARD_SIZE - row}")
        self.place_sound.play()

        return True

    def place_monarch(self, row, col):
        king_to_place = Piece("Monarch", [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)],
                              1, self.current_player, False)
        self.board[row][col] = king_to_place
        self.kings_placed[self.current_player] = True
        self.current_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2
        self.place_sound.play()
        self.add_to_log(f"Player {king_to_place.owner} placed Monarch at {col + 1},{BOARD_SIZE - row}")

    def end_of_move(self):
        self.check_board_promotions()
        self.did_someone_win()
        self.network_finish_move()

    def check_reserve_click(self, mouse_x, mouse_y):
        reserve_start_x = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + CELL_SIZE
        piece_spacing, padding = CELL_SIZE * 0.8, CELL_SIZE * 0.4
        max_pieces_per_row = 4

        reserve_areas = {
            PLAYER_1: (60, WINDOW_HEIGHT // 2, self.player1_reserve),
            PLAYER_2: (WINDOW_HEIGHT // 2 - 60, WINDOW_HEIGHT - 60, self.player2_reserve)
        }

        if mouse_x < reserve_start_x:
            return False

        def process_click(start_y, end_y, reserve):
            if not (start_y <= mouse_y <= end_y):
                return False

            self.deselect()
            col = int((mouse_x - (reserve_start_x + padding)) // piece_spacing)
            current_y = start_y + padding

            for section_idx, section in enumerate(reserve):
                section_height = ((
                                          len(section) + max_pieces_per_row - 1) // max_pieces_per_row) * piece_spacing + padding
                if current_y <= mouse_y < current_y + section_height:
                    row = int((mouse_y - current_y) // piece_spacing)
                    piece_idx = row * max_pieces_per_row + col

                    if 0 <= col < max_pieces_per_row and piece_idx < len(section):
                        self.selected_reserve_piece = {
                            'player': self.current_player,
                            'section': section_idx,
                            'piece_type': section[piece_idx],
                            'row': row,
                            'col': col
                        }
                        return True
                current_y += section_height
            return False

        start_y, end_y, reserve = reserve_areas.get(self.current_player, (0, 0, []))
        if process_click(start_y, end_y, reserve):
            self.pick_up.play()
            return True

        self.selected_reserve_piece = None
        return False

    def handle_click(self, row, col):
        try:
            if self.game_over:
                return

            if self.is_king_placement_phase():
                # Check if clicked position is the center
                center_row = BOARD_SIZE // 2
                center_col = BOARD_SIZE // 2
                if row == center_row and col == center_col:
                    return  # Don't allow placement in center

                if self.board[row][col] == EMPTY:
                    self.place_monarch(row, col)
                return

            piece = self.board[row][col]

            # Handle movement if a piece is selected
            if self.selected_piece:
                if (row, col) in self.valid_moves:
                    self.move_piece(self.selected_piece, (row, col))
                    self.selected_piece, self.valid_moves = None, []

                    if not self.game_over:
                        self.current_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2

                    self.slide_sound.play()
                else:
                    self.deselect()

            # Select own piece
            elif piece != EMPTY and piece.owner == self.current_player:
                self.selected_piece = (row, col)
                self.valid_moves = self.get_valid_moves(row, col)
                self.select_piece.play()

            # Place new piece from reserve
            elif self.reserve_selected:
                if self.place_new_piece(row, col):
                    pass
                else:
                    self.de_select.play()
                self.deselect()

        finally:
            self.end_of_move()

def main():
    pygame.init()
    mixer.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Board Game Prototype")

    utils = MainUtilities()
    game = Game()
    current_state = GameState.MENU
    menu = MenuScreen()
    post_game_screen = PostGameScreen()
    menu.ip_input = ""
    clock = pygame.time.Clock()

    while True:
        if current_state == GameState.MENU:
            clock.tick(35)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    utils.handle_exit(screen)

                if event.type == pygame.MOUSEBUTTONDOWN and not menu.show_ip_dialog:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    action = menu.handle_click(mouse_x, mouse_y)

                    if action == "Alone":
                        utils.fade_to_black(screen)
                        utils.handle_music_transition('Sounds/ambient_track.mp3')
                        game.multiplayer = False
                        current_state = GameState.PLAYING
                    elif action == "Amidst":
                        menu.show_ip_dialog = True
                        utils.play_sound('multiplayer_connect')
                        menu.ip_input = ""
                    elif action == "Abandon":
                        utils.handle_exit(screen)

                if menu.show_ip_dialog and event.type == pygame.KEYDOWN:
                    if utils.handle_ip_input(event, menu):
                        current_state = utils.handle_multiplayer_connection(game, menu, screen)

        elif current_state == GameState.PLAYING:
            clock.tick(10)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    utils.handle_exit(screen)

                if event.type == pygame.KEYDOWN:
                    utils.handle_volume_control(event)

                if event.type == pygame.MOUSEMOTION:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    game.resign_hover = game.resign_button_rect.collidepoint(mouse_x, mouse_y)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()

                    if game.mute_button_rect.collidepoint(mouse_x, mouse_y):
                        game.is_muted = not game.is_muted
                        mixer.music.set_volume(0 if game.is_muted else 1)
                        continue

                    if game.resign_button_rect.collidepoint(mouse_x, mouse_y):
                        game.handle_resign()
                        current_state = GameState.POST_GAME
                        continue

                    if game.check_reserve_click(mouse_x, mouse_y):
                        game.reserve_selected = True

                    col = (mouse_x - GRID_OFFSET) // CELL_SIZE
                    row = (mouse_y - GRID_OFFSET) // CELL_SIZE
                    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                        game.handle_click(row, col)

            game.process_network_updates()
            if game.game_over:
                current_state = GameState.POST_GAME
            else:
                DrawUtils.draw(game, screen)
                DrawUtils.draw_message_log(game, screen)

        elif current_state == GameState.POST_GAME:
            clock.tick(35)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    utils.handle_exit(screen)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    action = post_game_screen.handle_click(mouse_x, mouse_y)

                    if action == "Rematch":
                        game.reset_game()
                        current_state = GameState.PLAYING
                    elif action == "Menu":
                        game.reset_game()
                        current_state = GameState.MENU
                        utils.handle_music_transition('Sounds/menu_track.mp3')

            winner_text = "WHITE WINS" if game.winner == PLAYER_1 else "BLACK WINS"
            post_game_screen.draw(screen, winner_text)

        if current_state == GameState.MENU:
            menu.draw(screen)

        pygame.display.flip()

if __name__ == "__main__":
    main()
