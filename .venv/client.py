import pygame
import sys
import socket
import pickle
import threading
from game import Game, WINDOW_SIZE, BOARD_SIZE, CELL_SIZE, GRID_OFFSET


class NetworkGame:
    def __init__(self, host='localhost', port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = (host, port)
        self.player_num = self.connect()
        self.game = Game()

    def connect(self):
        try:
            self.client.connect(self.addr)
            return int(self.client.recv(2048).decode())
        except Exception as e:
            print(f"Connection error: {e}")
            return None

    def send_state(self, game_state):
        try:
            self.client.send(pickle.dumps(game_state))
            return pickle.loads(self.client.recv(4096))
        except socket.error as e:
            print(f"Socket error: {e}")
            return None


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Multiplayer Board Game")

    network = NetworkGame()
    game = network.game
    clock = pygame.time.Clock()

    # Only allow moves when it's the player's turn
    def is_my_turn():
        return game.current_player == network.player_num

    def receive_state():
        while True:
            try:
                data = network.client.recv(4096)
                if data:
                    game_state = pickle.loads(data)
                    # Update local game state
                    game.board = game_state.board
                    game.current_player = game_state.current_player
                    game.pieces_in_hand = game_state.pieces_in_hand
                    game.kings_placed = game_state.kings_placed
                    game.game_over = game_state.game_over
                    game.winner = game_state.winner
                    game.player1_reserve = game_state.player1_reserve
                    game.player2_reserve = game_state.player2_reserve
            except:
                break

    # Start receive thread
    receive_thread = threading.Thread(target=receive_state)
    receive_thread.daemon = True
    receive_thread.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and is_my_turn():
                mouse_x, mouse_y = pygame.mouse.get_pos()
                reserve_clicked = game.check_reserve_click(mouse_x, mouse_y)

                if reserve_clicked:
                    game.reserve_selected = True

                col = (mouse_x - GRID_OFFSET) // CELL_SIZE
                row = (mouse_y - GRID_OFFSET) // CELL_SIZE
                if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                    game.handle_click(row, col)
                    # Send updated game state to server
                    network.send_state(game)

        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()