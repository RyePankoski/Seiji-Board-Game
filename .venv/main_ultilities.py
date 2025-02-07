import pygame
from pygame import mixer
import sys
from game_state import GameState
from constants import WINDOW_WIDTH, WINDOW_HEIGHT



class MainUtilities:
    def __init__(self):
        self.sounds = {}
        self.init_sounds()

    def init_sounds(self):
        """Initialize all game sounds and music"""
        try:
            mixer.music.load('Sounds/menu_theme.mp3')
            self.sounds = {
                'multiplayer_connect': pygame.mixer.Sound("Sounds/multiplayer_connect_sound.mp3"),
                'failed_connect': pygame.mixer.Sound("Sounds/failed_to_connect.mp3"),
                'exit': pygame.mixer.Sound("Sounds/exit_sound.mp3")
            }
            mixer.music.set_volume(0.5)
            mixer.music.play(-1)
        except pygame.error as e:
            print(f"Could not load or play sound files: {e}")

    def play_sound(self, sound_name):
        """Play a sound effect by name"""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def handle_music_transition(self, new_track, fadeout_time=1000):
        """Handle smooth transition between music tracks"""
        try:
            mixer.music.fadeout(fadeout_time)
            mixer.music.load(new_track)
            mixer.music.play(-1)
        except pygame.error as e:
            print(f"Could not load or play music file: {e}")

    def handle_volume_control(game, self, event):
        """Handle volume up/down controls with arrow keys"""
        current_volume = mixer.music.get_volume()

        if event.key == pygame.K_UP:
            new_volume = min(1.0, current_volume + 0.1)
        elif event.key == pygame.K_DOWN:
            new_volume = max(0.0, current_volume - 0.1)
        else:
            return

        # Update music volume
        mixer.music.set_volume(new_volume)

        # Update all sound effect volumes
        for sound in [
            self.place_sound,
            self.slide_sound,
            self.pick_up,
            self.capture,
            self.promote_sound,
            self.endgame,
            self.select_piece,
            self.de_select
        ]:
            sound.set_volume(new_volume)

    def fade_to_black(self, screen, speed=5):
        """Create a fade to black transition effect"""
        fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        fade_surface.fill((0, 0, 0))
        for alpha in range(0, 255, speed):
            fade_surface.set_alpha(alpha)
            screen.blit(fade_surface, (0, 0))
            pygame.display.flip()
            pygame.time.wait(5)

    def handle_exit(self, screen):
        """Handle game exit with fade effect and sound"""
        mixer.music.fadeout(1000)
        self.play_sound('exit')
        self.fade_to_black(screen)
        pygame.time.wait(3000)
        pygame.quit()
        sys.exit()

    def handle_ip_input(self, event, menu):
        """Handle IP address input in multiplayer menu"""
        if event.key == pygame.K_ESCAPE:
            menu.show_ip_dialog = False
            menu.ip_input = ""
        elif event.key == pygame.K_BACKSPACE:
            menu.ip_input = menu.ip_input[:-1]
        elif event.key == pygame.K_RETURN:
            return True
        else:
            if event.unicode.isprintable():
                menu.ip_input += event.unicode
        return False

    def handle_multiplayer_connection(self, game, menu, screen):
        """Handle multiplayer connection attempt"""
        if not menu.ip_input.strip():
            return GameState.MENU

        self.fade_to_black(screen)

        try:
            connection_result = game.network_manager.connect_to_server(menu.ip_input)
            if connection_result:
                self.handle_music_transition('Sounds/ambient_track.mp3')
                game.multiplayer = True
                menu.show_ip_dialog = False
                return GameState.PLAYING
            else:
                print("Connection failed")
                self.handle_music_transition('Sounds/menu_theme.mp3')
                self.play_sound('failed_connect')
                pygame.time.wait(500)
                menu.show_ip_dialog = False
                menu.ip_input = ""
                return GameState.MENU

        except Exception as e:
            print(f"Connection error: {e}")
            self.handle_music_transition('Sounds/menu_theme.mp3')
            self.play_sound('failed_connect')
            pygame.time.wait(500)
            menu.show_ip_dialog = False
            menu.ip_input = ""
            return GameState.MENU