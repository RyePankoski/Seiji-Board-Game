import socket
import json
import threading
import queue
from typing import Optional, Dict, Any


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
            # Start network thread to receive updates
            self.connected = True
            threading.Thread(target=self._network_thread, daemon=True).start()
            return True
        except Exception as e:
            print(f"Couldn't connect to server: {e}")
            self.connected = False
            return False

    def _network_thread(self) -> None:
        """Background thread that handles receiving data from the server"""
        while self.connected:
            try:
                data = self.socket.recv(4096)  # Increased buffer size
                if data:
                    new_state = json.loads(data.decode())
                    print("Client says: 'Pushing received data into queue'")
                    self.update_queue.put(new_state)
            except Exception as e:
                print(f"Network error: {e}")
                self.connected = False
                break

    def send_game_state(self, game_state: Dict[str, Any]) -> bool:
        if not self.connected:
            return False

        try:
            state_string = json.dumps(game_state)
            print("Client says: 'Sending data'")
            self.socket.send(state_string.encode())
            return True
        except Exception as e:
            print(f"Error sending game state: {e}")
            self.connected = False
            return False

    def process_network_updates(self, update_callback) -> None:
        try:
            while not self.update_queue.empty():
                new_state = self.update_queue.get_nowait()
                with self.lock:
                    update_callback(new_state)
        except queue.Empty:
            pass

    def disconnect(self) -> None:
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                print(f"Error closing socket: {e}")
        self.socket = None