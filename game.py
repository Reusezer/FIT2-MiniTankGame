import pyxel
import math
from constants import *
from player import Player
from bullet import Bullet
from map_generator import MapGenerator
from items import ItemSpawner, Mine
from network import NetworkManager


class Game:
    def __init__(self, num_players=2, use_network=False, is_host=False):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Tank Tank", fps=FPS)

        self.num_players = num_players
        self.use_network = use_network
        self.is_host = is_host

        # Generate map
        self.game_map = MapGenerator.generate()
        self.spawn_positions = MapGenerator.get_spawn_positions()

        # Create players
        self.players = []
        colors = [COLOR_PLAYER_1, COLOR_PLAYER_2, COLOR_PLAYER_3, COLOR_PLAYER_4]
        for i in range(num_players):
            x, y = self.spawn_positions[i]
            player = Player(i, x, y, colors[i])
            self.players.append(player)

        # Game state
        self.bullets = []
        self.mines = []
        self.explosions = []
        self.item_spawner = ItemSpawner(self.game_map)

        # UI
        self.game_over = False
        self.winner = None
        self.camera_x = 0
        self.camera_y = 0

        # Network
        self.network = None
        if use_network:
            self.network = NetworkManager(is_host)
            self.network.start()

        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        if self.game_over:
            if pyxel.btnp(pyxel.KEY_R):
                self.restart()
            return

        # Update network
        if self.network:
            self.network.update()

        # Update players
        for i, player in enumerate(self.players):
            player.update(self.game_map)

            # Handle local player input
            if i == 0 or (not self.use_network):
                self._handle_player_input(player, i)

        # Update bullets
        for bullet in self.bullets:
            bullet.update(self.game_map)

            # Check player collisions
            for player in self.players:
                if bullet.check_player_collision(player):
                    if player.take_damage():
                        # Player died
                        killer = self._get_player_by_id(bullet.owner_id)
                        if killer:
                            killer.kills += 1
                            if killer.kills >= WIN_KILLS:
                                self.game_over = True
                                self.winner = killer
                        # Respawn player
                        self._respawn_player(player)
                    bullet.active = False
                    self._add_explosion(bullet.x, bullet.y)

        # Remove inactive bullets
        self.bullets = [b for b in self.bullets if b.active]

        # Update mines
        for mine in self.mines:
            mine.update()
            for player in self.players:
                if mine.check_trigger(player):
                    if player.take_damage():
                        self._respawn_player(player)
                    self._add_explosion(mine.x, mine.y)

        self.mines = [m for m in self.mines if m.active]

        # Update items
        self.item_spawner.update(self.players)

        # Update explosions
        self.explosions = [(x, y, t - 1) for x, y, t in self.explosions if t > 1]

        # Update camera (follow player 1)
        if self.players:
            self.camera_x = self.players[0].x - SCREEN_WIDTH // 2
            self.camera_y = self.players[0].y - SCREEN_HEIGHT // 2
            self.camera_x = max(0, min(self.camera_x, SCREEN_WIDTH - SCREEN_WIDTH))
            self.camera_y = max(0, min(self.camera_y, SCREEN_HEIGHT - SCREEN_HEIGHT))

    def _handle_player_input(self, player, player_index):
        """Handle input for a player"""
        dx = 0
        dy = 0

        # Movement keys (different for each local player)
        if player_index == 0:
            if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W):
                dy = -1
            if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S):
                dy = 1
            if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
                dx = -1
            if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
                dx = 1
            if pyxel.btnp(pyxel.KEY_SPACE):
                new_bullets = player.shoot()
                self.bullets.extend(new_bullets)
            if pyxel.btnp(pyxel.KEY_E):
                self._place_mine(player)
        elif player_index == 1:
            if pyxel.btn(pyxel.KEY_I):
                dy = -1
            if pyxel.btn(pyxel.KEY_K):
                dy = 1
            if pyxel.btn(pyxel.KEY_J):
                dx = -1
            if pyxel.btn(pyxel.KEY_L):
                dx = 1
            if pyxel.btnp(pyxel.KEY_H):
                new_bullets = player.shoot()
                self.bullets.extend(new_bullets)

        if dx != 0 or dy != 0:
            player.move(dx, dy, self.game_map)

    def _place_mine(self, player):
        """Place a mine at player's location"""
        if player.alive:
            mine = Mine(player.x, player.y, player.id)
            self.mines.append(mine)

    def _add_explosion(self, x, y):
        """Add explosion effect"""
        self.explosions.append((x, y, 15))

    def _get_player_by_id(self, player_id):
        """Get player by ID"""
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def _respawn_player(self, player):
        """Respawn a player at their spawn point"""
        x, y = self.spawn_positions[player.id]
        player.x = x
        player.y = y

    def restart(self):
        """Restart the game"""
        self.__init__(self.num_players, self.use_network, self.is_host)

    def draw(self):
        pyxel.cls(COLOR_BG)

        # Draw map
        MapGenerator.draw_map(self.game_map)

        # Draw items
        self.item_spawner.draw()

        # Draw mines
        for mine in self.mines:
            mine.draw()

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw()

        # Draw players
        for player in self.players:
            player.draw()

        # Draw explosions
        for x, y, timer in self.explosions:
            size = int(8 * (timer / 15))
            pyxel.circ(x, y, size, COLOR_EXPLOSION)
            pyxel.circb(x, y, size + 2, COLOR_UI)

        # Draw vignette effect for vision
        self._draw_vignette()

        # Draw UI
        self._draw_ui()

        if self.game_over:
            self._draw_game_over()

    def _draw_vignette(self):
        """Draw vision vignette effect"""
        # For simplicity, we'll skip the complex vignette
        # In a full implementation, you'd darken areas far from the player
        pass

    def _draw_ui(self):
        """Draw UI elements"""
        # Draw scoreboard
        y_offset = 2
        for i, player in enumerate(self.players):
            x_offset = 2 if i < 2 else SCREEN_WIDTH - 60
            y = y_offset if i % 2 == 0 else y_offset + 10

            # Player color indicator
            pyxel.rect(x_offset, y, 4, 4, player.color)

            # Score
            text = f"P{i+1}: {player.kills}/{WIN_KILLS}"
            pyxel.text(x_offset + 6, y, text, COLOR_UI)

            # HP
            hp_text = "HP:" + "♥" * player.hp
            pyxel.text(x_offset + 6, y + 4, hp_text, COLOR_EXPLOSION if player.hp <= 1 else COLOR_UI)

    def _draw_game_over(self):
        """Draw game over screen"""
        # Semi-transparent overlay
        for y in range(0, SCREEN_HEIGHT, 2):
            pyxel.line(0, y, SCREEN_WIDTH, y, COLOR_BG)

        # Winner text
        if self.winner:
            text = f"Player {self.winner.id + 1} Wins!"
            x = SCREEN_WIDTH // 2 - len(text) * 2
            y = SCREEN_HEIGHT // 2 - 10

            # Shadow
            pyxel.text(x + 1, y + 1, text, COLOR_BG)
            # Text
            pyxel.text(x, y, text, self.winner.color)

        # Restart prompt
        restart_text = "Press R to Restart"
        x = SCREEN_WIDTH // 2 - len(restart_text) * 2
        pyxel.text(x, SCREEN_HEIGHT // 2 + 10, restart_text, COLOR_UI)
