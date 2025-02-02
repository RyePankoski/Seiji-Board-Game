import socket
import threading
import pickle
import json


class GameServer:
    def __init__(self, host='localhost', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        print(f"Server started on {host}:{port}")

        self.clients = []
        self.addresses = []
        self.game_state = None

    def start(self):
        while len(self.clients) < 2:
            client, address = self.server.accept()
            print(f"Connection from {address}")

            self.clients.append(client)
            self.addresses.append(address)

            # Assign player number (1 or 2)
            player_num = len(self.clients)
            client.send(str(player_num).encode())

            # Start a thread to handle this client
            thread = threading.Thread(target=self.handle_client, args=(client, player_num))
            thread.start()

    def handle_client(self, client, player_num):
        while True:
            try:
                # Receive game state updates from client
                data = client.recv(4096)
                if not data:
                    break

                # Deserialize the game state
                game_state = pickle.loads(data)
                self.game_state = game_state

                # Broadcast the updated state to all clients
                self.broadcast_state(game_state, client)

            except Exception as e:
                print(f"Error handling client {player_num}: {e}")
                break

        # Remove disconnected client
        if client in self.clients:
            self.clients.remove(client)
        client.close()

    def broadcast_state(self, state, sender):
        """Send game state to all clients except the sender"""
        for client in self.clients:
            if client != sender:
                try:
                    client.send(pickle.dumps(state))
                except:
                    client.close()
                    self.clients.remove(client)


if __name__ == "__main__":
    server = GameServer()
    print("Starting server...")
    server.start()