import pyxel
from constants import *
from menu import Menu, MenuState
from game import Game
from network_tcp import NetworkManager  # Using new TCP implementation


class TankTankApp:
    """Main application that handles menu and game states"""

    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Tank Tank", fps=FPS)

        self.menu = Menu()
        self.game = None
        self.network = None
        self.in_game = False

        pyxel.run(self.update, self.draw)

    def update(self):
        if self.in_game:
            self._update_game()
        else:
            self._update_menu()

    def _update_menu(self):
        # Update network state first
        if self.network:
            self.network.update()

            # Check if host has signaled game start (for clients)
            if not self.menu.is_host and self.network.game_starting:
                print("[App] Client detected game start signal from host")
                # Calculate num_players: at least 2 for network game
                num_players = max(2, len(self.network.player_names))
                print(f"[App] Client starting game with {num_players} players")
                self._start_game(num_players=num_players, use_network=True, is_host=False)
                return

        action = self.menu.update(self.network)

        if action == "quit":
            pyxel.quit()

        elif action == "start_local":
            # Start local multiplayer game
            self._start_game(num_players=2, use_network=False)

        elif action == "setup_network":
            # Initialize network (only once!)
            if self.network is None:
                print(f"[App] Creating NetworkManager (is_host={self.menu.is_host})")
                # Pass direct IP if client has entered one
                direct_ip = self.menu.host_ip if not self.menu.is_host and self.menu.host_ip else None
                self.network = NetworkManager(self.menu.is_host, direct_ip=direct_ip)
                self.network.start()

                # Check if connection was established (for host)
                if self.menu.is_host and not self.network.connection_established:
                    self.menu.error_message = f"Failed to bind port {NETWORK_PORT}"
                    self.menu.state = MenuState.MAIN_MENU
                    self.network.stop()
                    self.network = None
            else:
                print(f"[App] NetworkManager already exists, skipping creation")

        elif action == "join_lobby":
            # Client found host, send join request with player name
            if self.network:
                self.network.join_game(self.menu.player_name)

        elif action == "start_network":
            # Host starts network game
            if self.network:
                # Broadcast start signal to all clients
                self.network.broadcast_start_game()
                print("[App] Host broadcasting start_game signal")

            # Calculate num_players: at least 2 for network game
            num_players = max(2, len(self.network.player_names)) if self.network else 2
            print(f"[App] Starting game with {num_players} players")
            self._start_game(num_players=num_players, use_network=True, is_host=self.menu.is_host)

        elif action == "cancel_network":
            # Clean up network
            if self.network:
                self.network.stop()
                self.network = None

    def _update_game(self):
        # Update the game instance
        if self.game:
            self.game.update()

        # Check if we should return to menu
        if pyxel.btnp(pyxel.KEY_ESCAPE) and self.game.game_over:
            self._return_to_menu()

    def _start_game(self, num_players=2, use_network=False, is_host=False):
        """Start the game"""
        self.in_game = True
        # We need to create a game instance that doesn't call pyxel.run
        # So we'll modify the game to have a separate run mode
        self.game = GameInstance(
            num_players=num_players,
            use_network=use_network,
            is_host=is_host,
            network=self.network
        )

    def _return_to_menu(self):
        """Return to main menu"""
        self.in_game = False
        self.game = None
        if self.network:
            self.network.stop()
            self.network = None
        self.menu = Menu()

    def draw(self):
        if self.in_game and self.game:
            self.game.draw()
        else:
            self.menu.draw()


class GameInstance:
    """Game instance that doesn't control the main loop"""

    def __init__(self, num_players=2, use_network=False, is_host=False, network=None):
        self.num_players = num_players
        self.use_network = use_network
        self.is_host = is_host

        # Import here to avoid circular dependency
        from map_generator import MapGenerator
        from player import Player
        from items import ItemSpawner

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
        self.network = network

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            if self.network:
                self.network.stop()
            pyxel.quit()

        if self.game_over:
            if pyxel.btnp(pyxel.KEY_R):
                self.__init__(self.num_players, self.use_network, self.is_host, self.network)
            return

        # Update network and receive remote player inputs
        remote_inputs = []
        if self.network:
            self.network.update()
            # Receive ALL inputs from remote player
            if self.network.peer:
                messages = self.network.peer.recv_all()
                for msg in messages:
                    if msg.get("type") == "player_input":
                        remote_inputs.append(msg)

        # Update players
        for i, player in enumerate(self.players):
            player.update(self.game_map)

            # Handle player input
            if not self.use_network:
                # Local multiplayer: handle all players
                self._handle_player_input(player, i)
            else:
                # Network multiplayer
                if self.network and self.network.my_player_id is not None:
                    if i == self.network.my_player_id:
                        # Handle our own player's input
                        self._handle_player_input(player, i)
                    else:
                        # Apply ALL remote inputs for this player
                        for remote_input in remote_inputs:
                            if remote_input.get("player_id") == i:
                                self._apply_remote_input(player, remote_input)

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

    def _handle_player_input(self, player, player_index):
        """Handle input for a player"""
        dx = 0
        dy = 0
        shoot = False
        place_mine = False

        # For network play, each player uses WASD/Arrow keys on their own machine
        # For local multiplayer, player 0 uses WASD/Arrows, player 1 uses IJKL
        if self.use_network or player_index == 0:
            # Primary controls: WASD or Arrow keys
            if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W):
                dy = -1
            if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S):
                dy = 1
            if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
                dx = -1
            if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
                dx = 1
            if pyxel.btnp(pyxel.KEY_SPACE):
                shoot = True
            if pyxel.btnp(pyxel.KEY_E):
                place_mine = True
        elif player_index == 1:
            # Local multiplayer only: secondary controls for player 2
            if pyxel.btn(pyxel.KEY_I):
                dy = -1
            if pyxel.btn(pyxel.KEY_K):
                dy = 1
            if pyxel.btn(pyxel.KEY_J):
                dx = -1
            if pyxel.btn(pyxel.KEY_L):
                dx = 1
            if pyxel.btnp(pyxel.KEY_H):
                shoot = True

        # Apply movement
        if dx != 0 or dy != 0:
            player.move(dx, dy, self.game_map)

        # Apply actions
        if shoot:
            new_bullets = player.shoot()
            self.bullets.extend(new_bullets)
        if place_mine:
            self._place_mine(player)

        # Send input to network if this is our player
        if self.use_network and self.network and player_index == self.network.my_player_id:
            self._send_player_input(dx, dy, shoot, place_mine, player_index)

    def _place_mine(self, player):
        """Place a mine at player's location"""
        from items import Mine
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

    def _send_player_input(self, dx, dy, shoot, place_mine, player_id):
        """Send local player input to network"""
        if self.network and self.network.peer:
            input_data = {
                "type": "player_input",
                "player_id": player_id,
                "dx": dx,
                "dy": dy,
                "shoot": shoot,
                "place_mine": place_mine
            }
            self.network.peer.send(input_data)

    def _apply_remote_input(self, player, input_data):
        """Apply remote player's input"""
        dx = input_data.get("dx", 0)
        dy = input_data.get("dy", 0)
        shoot = input_data.get("shoot", False)
        place_mine = input_data.get("place_mine", False)

        # Apply movement
        if dx != 0 or dy != 0:
            player.move(dx, dy, self.game_map)

        # Apply actions
        if shoot:
            new_bullets = player.shoot()
            self.bullets.extend(new_bullets)
        if place_mine:
            self._place_mine(player)

    def draw(self):
        pyxel.cls(COLOR_BG)

        # Draw map
        from map_generator import MapGenerator
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

        # Draw UI
        self._draw_ui()

        if self.game_over:
            self._draw_game_over()

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
        restart_text = "R: Restart | ESC: Menu"
        x = SCREEN_WIDTH // 2 - len(restart_text) * 2
        pyxel.text(x, SCREEN_HEIGHT // 2 + 10, restart_text, COLOR_UI)


# For direct testing
if __name__ == "__main__":
    TankTankApp()
