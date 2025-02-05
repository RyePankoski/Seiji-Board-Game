from typing import Optional, Dict, Any, Callable
import socket
import json
import threading
import queue
from piece import Piece  # You'll need to create this file


class NetworkManager:
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.update_queue: queue.Queue = queue.Queue()
        self.lock = threading.Lock()
        self.connected = False

    def connect_to_server(self, server_ip: str = "localhost", port: int = 5555) -> bool:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((server_ip, port))
            print("Connected to server!")
            self.connected = True
            threading.Thread(target=self._network_thread, daemon=True).start()
            return True
        except Exception as e:
            print(f"Couldn't connect to server: {e}")
            self.connected = False
            return False

    def send_game_state(self, board: list, current_player: int,
                        player1_reserve: list, player2_reserve: list,
                        most_recent_message: str) -> bool:
        if not self.connected:
            return False

        # Create serializable game state
        serializable_board = []
        for row in board:
            board_row = []
            for piece in row:
                if piece == 0:  # Assuming EMPTY is 0
                    board_row.append(0)
                else:
                    board_row.append({
                        "name": piece.name,
                        "directions": piece.directions,
                        "move_distance": piece.move_distance,
                        "owner": piece.owner,
                        "promoted": piece.promoted,
                    })
            serializable_board.append(board_row)

        game_state = {
            "board": serializable_board,
            "current_player": current_player,
            "player_1_reserve": player1_reserve,
            "player_2_reserve": player2_reserve,
            "most_recent_message": most_recent_message
        }

        try:
            state_string = json.dumps(game_state)
            print("Client says: 'Sending data'")
            self.socket.send(state_string.encode())
            return True
        except Exception as e:
            print(f"Error sending game state: {e}")
            self.connected = False
            return False

    def process_network_updates(self, game) -> None:
        """Process any pending network updates and apply them to the game state"""
        try:
            while not self.update_queue.empty():
                new_state = self.update_queue.get_nowait()
                with self.lock:
                    self.update_game_state(game, new_state)
        except queue.Empty:
            pass

    def update_game_state(self, game, new_state: Dict) -> None:
        """Updates the game state with data received from network"""
        # Convert the serialized board back to Piece objects
        board = []
        for row in new_state["board"]:
            board_row = []
            for cell in row:
                if cell == 0:
                    board_row.append(0)
                else:
                    piece = Piece(
                        name=cell["name"],
                        directions=cell["directions"],
                        move_distance=cell["move_distance"],
                        owner=cell["owner"],
                        promoted=cell["promoted"]
                    )
                    board_row.append(piece)
            board.append(board_row)

        game.board = board
        game.current_player = new_state["current_player"]
        game.player1_reserve = new_state["player_1_reserve"]
        game.player2_reserve = new_state["player_2_reserve"]
        game.add_to_log(new_state["most_recent_message"])

        game.did_someone_win()

    def _network_thread(self) -> None:
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if data:
                    new_state = json.loads(data.decode())
                    print("Client says: 'Pushing received data into queue'")
                    self.update_queue.put(new_state)
            except Exception as e:
                print(f"Network error: {e}")
                self.connected = False
                break

    def disconnect(self) -> None:
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                print(f"Error closing socket: {e}")
        self.socket = None