import socket
import threading
import json
import queue


class GameServer:
    def __init__(self):
        self.clients = []  # List to store client connections
        self.game_states = {}  # Dictionary to store game states for each client
        self.lock = threading.Lock()

    def handle_client(self, conn, addr):
        print(f"Connected by {addr}")

        # Add client to list
        with self.lock:
            self.clients.append(conn)
            client_id = len(self.clients) - 1

        try:
            while True:
                # Receive game state from client
                data = conn.recv(4096)  # Increased buffer size

                if not data:
                    print(f"Client {addr} disconnected")
                    break

                print("Recieving data")
                # Parse the received game state
                game_state = json.loads(data.decode())

                # Store this client's game state
                with self.lock:
                    self.game_states[client_id] = game_state

                    # Broadcast to other client
                    for i, client in enumerate(self.clients):
                        if i != client_id:  # Don't send back to the sender
                            try:
                                client.send(data)
                            except:
                                print(f"Failed to send to client {i}")

        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            # Clean up when client disconnects
            with self.lock:
                if conn in self.clients:
                    self.clients.remove(conn)
                if client_id in self.game_states:
                    del self.game_states[client_id]
            conn.close()

    def start(self, host='0.0.0.0', port=5555):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("192.168.0.15", 5555))
        server.listen()
        print(f"Server is listening on {host}:{port}")

        try:
            while True:
                conn, addr = server.accept()
                # Only allow 2 players
                if len(self.clients) < 2:
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    thread.start()
                    print(f"Active connections: {len(self.clients)}")
                else:
                    print(f"Rejected connection from {addr}: game full")
                    conn.close()
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            server.close()


if __name__ == "__main__":
    server = GameServer()
    server.start()