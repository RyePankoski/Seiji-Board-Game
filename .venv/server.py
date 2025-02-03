import socket
import threading
import json  # for converting game state to string


def handle_client(conn, addr):
    print(f"Connected by {addr}")
    while True:
        try:
            # Receive game state
            data = conn.recv(1024)
            if not data:
                break

            # Convert received data to game state
            game_state = json.loads(data.decode())

            # Update your game with new state
            update_game(game_state)

            # Send your game state back
            your_game_state = get_game_state()  # your function to get current state
            conn.send(json.dumps(your_game_state).encode())

        except:
            break

    conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', 5555))  # Empty string means bind to all available interfaces
    server.listen()
    print(f"Server is listening on port 5555...")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"Active connections: {threading.active_count() - 1}")


if __name__ == "__main__":
    start_server()