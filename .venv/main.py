import pygame
import sys
from typing import List
from draw_utils import DrawUtils
from constants import *
import socket
import json
import threading
import queue

# Initialize Pygame
pygame.init()


class MenuScreen:
    def __init__(self):
        try:
            self.font = pygame.font.Font('font.otf', 42)
            self.title_font = pygame.font.Font('font.otf', 72)
        except pygame.error:
            print("Custom font not found, using default")
            self.font = pygame.font.Font(None, 42)

        # Load and scale the texture
        try:
            self.texture = pygame.image.load('tables.png').convert_alpha()
        except pygame.error:
            print("Texture not found")
            self.texture = None

        button_width = 200
        button_height = 50
        button_spacing = 75
        border_width = 3  # Width of the border around buttons

        # Calculate positions
        total_height = (3 * button_height) + (2 * button_spacing)
        start_y = (WINDOW_HEIGHT // 2) - (total_height // 2)

        # Store both outer (with border) and inner rectangles
        self.button_borders = []
        self.buttons = []

        # Create buttons with their borders
        button_positions = [
            ("SinglePlayer", start_y),
            ("Multiplayer", start_y + button_height + button_spacing),
            ("Quit", start_y + 2 * (button_height + button_spacing))
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

    def draw(self, screen):
        # Draw background
        screen.fill((50, 50, 50))

        # Draw each button with its texture and border
        for border_rect, (button_rect, text) in zip(self.button_borders, self.buttons):
            # Draw border
            pygame.draw.rect(screen, (200, 200, 200), border_rect)

            # Draw button background
            pygame.draw.rect(screen, (100, 100, 100), button_rect)

            # Draw texture if available
            if self.texture:
                # Create a subsurface of the texture sized to the button
                texture_rect = self.texture.get_rect()
                scale_factor = max(button_rect.width / texture_rect.width,
                                   button_rect.height / texture_rect.height)

                scaled_width = int(texture_rect.width * scale_factor)
                scaled_height = int(texture_rect.height * scale_factor)

                scaled_texture = pygame.transform.scale(self.texture,
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
            self.draw_text(screen, text, button_rect)

    def handle_click(self, mouse_x, mouse_y):
        for button_rect, text in self.buttons:
            if button_rect.collidepoint(mouse_x, mouse_y):
                if text.lower() == "stone":
                    return "singleplayer"
                return text.lower()
        return None

    def draw_text(self, screen, text, button):
        text_surface = self.font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=button.center)
        screen.blit(text_surface, text_rect)



def fade_transition(screen):
    fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    fade_surface.fill((0, 0, 0))  # Black fade

    for alpha in range(0, 255, 5):  # Fade in
        fade_surface.set_alpha(alpha)
        screen.blit(fade_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(10)  # Small delay to control fade speed

class GameState:
    MENU = "menu"
    PLAYING = "playing"

class Piece:
    def __init__(self, name, directions, move_distance, owner, promoted=False):
        self.name = name
        self.directions = directions
        self.move_distance = move_distance
        self.owner = owner
        self.promoted = promoted
        self.promote_sound_played = False

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
        self.multiplayer = False
        self.monarch_placement_phase = True

        self.update_queue = queue.Queue()
        self.lock = threading.Lock()

        self.place_sound = pygame.mixer.Sound("place_sound.mp3")  # Replace with actual file path
        self.slide_sound = pygame.mixer.Sound("slide_sound.mp3")
        self.pick_up = pygame.mixer.Sound("pick_up.mp3")
        self.capture = pygame.mixer.Sound("capture.mp3")
        self.promote = pygame.mixer.Sound("promote.mp3")
        self.endgame = pygame.mixer.Sound("endgame.mp3")
        self.advisor = pygame.mixer.Sound("advisor.mp3")

        self.is_muted = False
        self.mute_button_rect = pygame.Rect(10, WINDOW_HEIGHT - 70, 60, 60)

        self.background = pygame.image.load("background.png")
        self.background = pygame.transform.scale(self.background, (BOARD_SIZE * CELL_SIZE, BOARD_SIZE * CELL_SIZE))
        self.background_2 = pygame.image.load("background_2.png")
        self.background_2 = pygame.transform.scale(self.background_2, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.table_texture = pygame.image.load("tables.png").convert_alpha()

        self.message_log = []
        self.max_messages = 10  # Maximum number of messages to show
        self.log_font = pygame.font.Font(None, 24)  # Font for the log
        self.log_rect = pygame.Rect(
            WINDOW_WIDTH - 300,  # X position (300 pixels from right)
            WINDOW_HEIGHT - 126,  # Y position (adjusted up since box is smaller)
            280,  # Width of log box
            126  # Height reduced to 70% of original (180 * 0.7 = 126)
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

    def add_to_log(self, message):
        """Add a new message to the game log"""
        self.message_log.append(message)
        if len(self.message_log) > self.max_messages:
            self.message_log.pop(0)  # Remove oldest message if we exceed max

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
                current_y -= 25  # Move up for next message

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

    def demote(self, row, col):
        piece_to_demote = self.board[row][col]
        piece_to_demote.promoted = False
        piece_to_demote.advisor_next_advisor = False

        demotion_settings = {
            "Official": ([(1, 0), (0, 1), (-1, 0), (0, -1)], 1),
            "Advisor": ([(1, 1), (1, -1), (-1, -1), (-1, 1)], 3),
            "Monarch": ([(-1, 0), (1, 0), (0, -1), (0, 1),
                         (-1, -1), (1, 1), (-1, 1), (1, -1)], 1)
        }

        if piece_to_demote.name in demotion_settings:
            piece_to_demote.directions, piece_to_demote.move_distance = demotion_settings[piece_to_demote.name]

    def handle_promotion_status(self, row, col):
        promoting_piece = self.board[row][col]
        adjacent_pieces = self.has_friendly_adjacent_pieces(row, col)

        if promoting_piece.name == "Monarch" and not adjacent_pieces:
            self.demote(row, col)
        if promoting_piece.name == "Advisor" and "Monarch" not in adjacent_pieces:
            self.demote(row, col)
        if promoting_piece.name == "Official" and "Monarch" not in adjacent_pieces and "Advisor" not in adjacent_pieces:
            self.demote(row, col)

        if not adjacent_pieces or adjacent_pieces == {"Palace"}:
            self.demote(row, col)
            self.advisor_next_advisor = False
            return

        def promote(piece, move_distance=0, new_directions=None):
            if piece.promoted == False:
                self.promote.play()
                piece.promoted = True
                piece.move_distance = move_distance  # Set move_distance directly
                if new_directions:
                    piece.directions = new_directions  # Set directions directly

        name = promoting_piece.name

        if name == "Monarch":
            if adjacent_pieces:
                promote(promoting_piece, move_distance=2)

        elif name == "Advisor":
            if "Monarch" in adjacent_pieces:
                promote(promoting_piece, 3, new_directions=[(1, 1), (1, -1), (-1, -1), (-1, 1), (1, 0), (0, 1), (-1, 0),
                                                            (0, -1)])
        elif name == "Official":
            if "Monarch" in adjacent_pieces:
                promote(promoting_piece, 1,
                        new_directions=[(1, 1), (1, -1), (-1, -1), (-1, 1), (1, 0), (0, 1), (-1, 0), (0, -1)])
            elif "Advisor" in adjacent_pieces:
                promote(promoting_piece, move_distance=2)

    def check_board_promotions(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece != EMPTY:
                    action = self.handle_promotion_status if self.has_friendly_adjacent_pieces(row,
                                                                                               col) else self.demote
                    action(row, col)

    def did_someone_win(self):

        # Skip if game is in king placement phase
        if self.monarch_placement_phase:
            return False

        # Initialize monarch counters for each player
        monarchs = {PLAYER_1: False, PLAYER_2: False}

        # Scan the board for monarchs
        for row in self.board:
            for piece in row:
                if piece != EMPTY and piece.name == "Monarch":
                    monarchs[piece.owner] = True

        # Check if either monarch is missing
        if not monarchs[PLAYER_1]:

            self.game_over = True
            self.winner = PLAYER_2
            if not self.is_muted:
                self.endgame.play()
            return True

        if not monarchs[PLAYER_2]:
            self.game_over = True
            self.winner = PLAYER_1
            if not self.is_muted:
                self.endgame.play()
            return True

        return False

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
            self.capture.play()
            # Add captured piece to the current player's reserve
            piece_reserve = reserve_to_edit[0] if captured_piece_name == "Advisor" else reserve_to_edit[1]
            if captured_piece_name != "Palace":
                piece_reserve.append(captured_piece_name)
            self.pieces_in_hand[current_player] += 1
            self.add_to_log(f"Captured {captured_piece_name}! Player {current_player} now has {self.pieces_in_hand[current_player]} pieces")


        # Move the piece
        self.add_to_log(f"Player {moving_piece.owner} moved {moving_piece.name} to: {to_row},{to_col}")
        self.board[to_row][to_col] = moving_piece
        self.board[from_row][from_col] = EMPTY
        self.did_someone_win()

    def check_reserve_click(self, mouse_x, mouse_y):
        # Calculate reserve area boundaries
        reserve_start_x = GRID_OFFSET + (BOARD_SIZE * CELL_SIZE) + CELL_SIZE
        piece_spacing = CELL_SIZE * 0.8
        padding = piece_spacing * 0.5
        max_pieces_per_row = 4

        # Reserve area boundaries for both players
        reserve_areas = {
            PLAYER_1: (60, WINDOW_HEIGHT // 2, self.player1_reserve),
            PLAYER_2: (WINDOW_HEIGHT // 2 - 60, WINDOW_HEIGHT - 60, self.player2_reserve)
        }

        if mouse_x < reserve_start_x:
            return False

        # Helper function to process reserve click
        def process_reserve_click(start_y, end_y, reserve):
            if start_y <= mouse_y <= end_y:
                current_y = start_y + padding
                col = int((mouse_x - (reserve_start_x + padding)) // piece_spacing)

                # Find which section was clicked
                for section_idx, section in enumerate(reserve):
                    num_pieces = len(section)
                    rows_needed = (num_pieces + max_pieces_per_row - 1) // max_pieces_per_row
                    section_height = rows_needed * piece_spacing + padding

                    if current_y <= mouse_y < current_y + section_height:
                        # Calculate row within this section
                        relative_y = mouse_y - current_y
                        row = int(relative_y // piece_spacing)

                        # Calculate piece index and verify it exists
                        piece_idx = (row * max_pieces_per_row) + col
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

        # Check current player's reserve area
        if self.current_player in reserve_areas:
            start_y, end_y, reserve = reserve_areas[self.current_player]
            if process_reserve_click(start_y, end_y, reserve):
                self.pick_up.play()
                return True

        self.selected_reserve_piece = None
        return False

    def finish_move(self):
        if self.multiplayer == True:
            self.send_game_state()

    def deselect(self):
        """Clear all current selections in the game state"""
        # Clear piece selection
        self.selected_piece = None

        # Clear reserve piece selection
        self.selected_reserve_piece = None
        self.reserve_selected = False

        # Clear valid moves
        self.valid_moves = []

        # Optional: Clear any temporary game states related to selection
        # self.temp_state = None  # Uncomment if you have temporary states to clear

    def handle_click(self, row, col):

        if self.game_over:
            return

        # King placement phase
        if self.is_king_placement_phase():
            if self.board[row][col] == EMPTY:  # Added center area check
                king_to_place = Piece("Monarch", [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)],
                                      1, self.current_player, False)
                self.board[row][col] = king_to_place
                self.kings_placed[self.current_player] = True
                self.current_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2
                self.place_sound.play()
                self.add_to_log(f"Player {king_to_place.owner} placed their Monarch")
                self.finish_move()
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
                self.finish_move()

            elif (row, col) == self.selected_piece:
                self.selected_piece = None
                self.valid_moves = []

        # Second priority: If clicking own piece (regular or king), select it
        elif self.board[row][col] != EMPTY and self.board[row][col].owner == self.current_player:
            self.selected_piece = (row, col)
            self.valid_moves = self.get_valid_moves(row, col)
            self.advisor.play()

        # Last priority: If clicking empty space and have pieces, try to place a new piece
        elif self.reserve_selected == True:
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

                    self.add_to_log(f"Player {self.board[row][col].owner} placed {self.board[row][col].name} at: {row},{col}")

                    # Play place sound when a piece is placed
                    self.place_sound.play()
                    self.finish_move()

                else:
                    self.deselect()


    def get_game_state(self):
        # Create a serializable version of the board
        serializable_board = []
        for row in self.board:
            board_row = []
            for piece in row:
                if piece == 0:
                    board_row.append(0)
                else:
                    # Convert Piece object to a dictionary with all its properties
                    board_row.append({
                        "name": piece.name,
                        "directions": piece.directions,
                        "move_distance": piece.move_distance,
                        "owner": piece.owner,
                        "promoted": piece.promoted,
                        "promote_sound_played": piece.promote_sound_played
                    })
            serializable_board.append(board_row)

        return {
            "board": serializable_board,
            "current_player": self.current_player,
            "player_1_reserve": self.player1_reserve,
            "player_2_reserve": self.player2_reserve
        }

    def update_game_state(self, new_state):
        # Convert the serialized board back to Piece objects
        board = []
        for row in new_state["board"]:
            board_row = []
            for cell in row:
                if cell == 0:
                    board_row.append(0)
                else:
                    # Reconstruct the Piece object from the dictionary
                    piece = Piece(
                        name=cell["name"],
                        directions=cell["directions"],
                        move_distance=cell["move_distance"],
                        owner=cell["owner"],
                        promoted=cell["promoted"]
                    )
                    piece.promote_sound_played = cell["promote_sound_played"]
                    board_row.append(piece)
            board.append(board_row)

        self.board = board
        self.current_player = new_state["current_player"]
        self.player1_reserve = new_state["player_1_reserve"]
        self.player2_reserve = new_state["player_2_reserve"]

        self.did_someone_win()

    def send_game_state(self):  # Remove the connection parameter
        current_state = self.get_game_state()
        try:
            state_string = json.dumps(current_state)
            print("Client says: 'Sending data'")
            self.socket.send(state_string.encode())  # Use self.socket instead of connection
        except Exception as e:
            print(f"Error sending game state: {e}")

    def connect_to_server(self, server_ip="localhost"):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((server_ip, 5555))
            print("Connected to server!")
            # Start network thread to receive updates
            threading.Thread(target=self.network_thread, daemon=True).start()
        except Exception as e:
            print(f"Couldn't connect to server: {e}")

    def network_thread(self):
        while True:
            try:
                data = self.socket.recv(4096)  # Increased buffer size
                if data:
                    new_state = json.loads(data.decode())
                    # Instead of updating directly, put the state in the queue
                    print("Client says: 'Pushing recieved data into queue'")
                    self.update_queue.put(new_state)
            except Exception as e:
                print(f"Network error: {e}")
                break

    def process_network_updates(self):
        """Process any pending network updates - call this in the main game loop"""
        try:
            while not self.update_queue.empty():
                new_state = self.update_queue.get_nowait()
                with self.lock:
                    self.update_game_state(new_state)
        except queue.Empty:
            pass  # No updates to process


import pygame
import sys
from pygame import mixer  # For handling audio


def main():
    pygame.init()
    mixer.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Board Game Prototype")

    # Load and start playing the ambient track
    try:
        mixer.music.load('menu_theme.mp3')  # Create a separate menu music file
        mixer.music.set_volume(0.5)
        mixer.music.play(-1)
    except pygame.error as e:
        print(f"Could not load or play the menu music file: {e}")

    game = Game()
    current_state = GameState.MENU
    menu = MenuScreen()
    clock = pygame.time.Clock()

    while True:
        if current_state == GameState.MENU:
            # Handle menu state
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    action = menu.handle_click(mouse_x, mouse_y)

                    if action == "singleplayer":
                        fade_transition(screen)

                        try:
                            mixer.music.fadeout(1000)  # Fade out over 1 second
                            mixer.music.load('ambient_track.mp3')
                            mixer.music.play(-1)
                        except pygame.error as e:
                            print(f"Could not load or play the game music file: {e}")


                        game.multiplayer = False
                        current_state = GameState.PLAYING
                    elif action == "multiplayer":
                        fade_transition(screen)

                        try:
                            mixer.music.fadeout(1000)  # Fade out over 1 second
                            mixer.music.load('ambient_track.mp3')
                            mixer.music.play(-1)
                        except pygame.error as e:
                            print(f"Could not load or play the game music file: {e}")

                        game.multiplayer = True
                        game.connect_to_server(menu.get_ip_address())
                        current_state = GameState.PLAYING
                    elif action == "quit":
                        pygame.quit()
                        sys.exit()

            menu.draw(screen)

        elif current_state == GameState.PLAYING:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:  # Volume up
                        current_volume = mixer.music.get_volume()
                        mixer.music.set_volume(min(1.0, current_volume + 0.1))
                    elif event.key == pygame.K_DOWN:  # Volume down
                        current_volume = mixer.music.get_volume()
                        mixer.music.set_volume(max(0.0, current_volume - 0.1))

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()

                    # Check if mute button was clicked
                    if game.mute_button_rect.collidepoint(mouse_x, mouse_y):
                        game.is_muted = not game.is_muted
                        if game.is_muted:
                            mixer.music.set_volume(0)
                        else:
                            mixer.music.set_volume(1)
                        continue

                    # Check if a reserve piece is clicked
                    reserve_clicked = game.check_reserve_click(mouse_x, mouse_y)
                    if reserve_clicked:
                        game.reserve_selected = True

                    # Handle the board click if within bounds
                    col = (mouse_x - GRID_OFFSET) // CELL_SIZE
                    row = (mouse_y - GRID_OFFSET) // CELL_SIZE
                    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                        game.handle_click(row, col)

            game.process_network_updates()
            DrawUtils.draw(game, screen)

        pygame.display.flip()
        clock.tick(15)

if __name__ == "__main__":
    main()
