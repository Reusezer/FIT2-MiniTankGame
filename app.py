import pyxel
from constants import *
from menu import Menu, MenuState
from network_tcp import NetworkManager


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

                # Reconstruct map from network data
                shared_map = None
                if self.network.shared_map_data is not None:
                    width = self.network.map_width or MAP_WIDTH
                    height = self.network.map_height or MAP_HEIGHT
                    flat_map = self.network.shared_map_data
                    shared_map = []
                    for y in range(height):
                        row = flat_map[y * width:(y + 1) * width]
                        shared_map.append(row)
                    print(f"[App] Client reconstructed map from host data")

                self._start_game(num_players=num_players, use_network=True, is_host=False, shared_map=shared_map)
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
            # Generate map FIRST, then broadcast it with start_game signal
            from map_generator import MapGenerator
            shared_map = MapGenerator.generate()

            if self.network:
                # Broadcast start signal with map data
                self.network.broadcast_start_game(game_map=shared_map)
                print("[App] Host broadcasting start_game signal with map")

            # Calculate num_players: at least 2 for network game
            num_players = max(2, len(self.network.player_names)) if self.network else 2
            print(f"[App] Starting game with {num_players} players")
            self._start_game(num_players=num_players, use_network=True, is_host=self.menu.is_host, shared_map=shared_map)

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

    def _start_game(self, num_players=2, use_network=False, is_host=False, shared_map=None):
        """Start the game"""
        self.in_game = True
        # We need to create a game instance that doesn't call pyxel.run
        # So we'll modify the game to have a separate run mode
        self.game = GameInstance(
            num_players=num_players,
            use_network=use_network,
            is_host=is_host,
            network=self.network,
            shared_map=shared_map
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

    def __init__(self, num_players=2, use_network=False, is_host=False, network=None, shared_map=None):
        self.num_players = num_players
        self.use_network = use_network
        self.is_host = is_host

        # Import here to avoid circular dependency
        from map_generator import MapGenerator
        from player import Player
        from items import ItemSpawner

        # Generate or use shared map
        if shared_map is not None:
            self.game_map = shared_map
        else:
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
        self.winner_id = None
        self.camera_x = 0
        self.camera_y = 0

        # Network
        self.network = network
        self.state_sync_timer = 0  # Timer for periodic state sync

        # Network interpolation for smooth remote player movement
        self.remote_targets = {}  # player_id -> (target_x, target_y, target_dir)
        self.interpolation_speed = 0.3  # How fast to interpolate (0-1)

        # Note: Map is now sent via start_game message in broadcast_start_game()
        # No need to send it again here

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            if self.network:
                self.network.stop()
            pyxel.quit()

        if self.game_over:
            if pyxel.btnp(pyxel.KEY_R):
                # Preserve the current map for restart
                self.__init__(self.num_players, self.use_network, self.is_host, self.network, self.game_map)
            return

        # Update network and receive remote player inputs
        remote_inputs = []
        if self.network:
            # Get game messages from network update (lobby messages handled internally)
            game_messages = self.network.update()
            if game_messages is None:
                game_messages = []
            for msg in game_messages:
                msg_type = msg.get("type")
                if msg_type in ("player_input", "position_sync"):
                    remote_inputs.append(msg)
                elif msg_type == "map_data":
                    self._apply_map_data(msg)
                elif msg_type == "game_state":
                    self._apply_game_state(msg)
                elif msg_type == "bullet_spawn":
                    self._apply_bullet_spawn(msg)
                elif msg_type == "item_spawn":
                    self._apply_item_spawn(msg)
                elif msg_type == "item_pickup":
                    self._apply_item_pickup(msg)
                elif msg_type == "player_damage":
                    self._apply_player_damage(msg)
                elif msg_type == "explosion":
                    self._apply_explosion(msg)
                elif msg_type == "mine_spawn":
                    self._apply_mine_spawn(msg)

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

        # Smoothly interpolate remote players
        self._interpolate_remote_players()

        # Update bullets
        for bullet in self.bullets:
            bullet.update(self.game_map)

            # Check player collisions (host authoritative for network games)
            if not self.use_network or self.is_host:
                for player in self.players:
                    if bullet.check_player_collision(player):
                        died = player.take_damage()
                        if died:
                            # Player died
                            killer = self._get_player_by_id(bullet.owner_id)
                            if killer:
                                killer.kills += 1
                                if killer.kills >= WIN_KILLS:
                                    self.game_over = True
                                    self.winner = killer
                                    self.winner_id = killer.id
                            # Respawn player
                            self._respawn_player(player)
                        bullet.active = False
                        self._add_explosion(bullet.x, bullet.y)
                        # Sync damage to client
                        if self.use_network and self.is_host:
                            self._send_player_damage(player, died, bullet.owner_id)
                            self._send_explosion(bullet.x, bullet.y)

        # Remove inactive bullets
        self.bullets = [b for b in self.bullets if b.active]

        # Update mines (host authoritative)
        if not self.use_network or self.is_host:
            for mine in self.mines:
                mine.update()
                for player in self.players:
                    if mine.check_trigger(player):
                        died = player.take_damage()
                        if died:
                            self._respawn_player(player)
                        self._add_explosion(mine.x, mine.y)
                        if self.use_network and self.is_host:
                            self._send_player_damage(player, died, mine.owner_id)
                            self._send_explosion(mine.x, mine.y)

            self.mines = [m for m in self.mines if m.active]

        # Update items (host authoritative for spawning)
        if not self.use_network or self.is_host:
            old_item_count = len(self.item_spawner.items)
            self.item_spawner.update(self.players)

            # Check for new item spawns
            if self.use_network and self.is_host:
                if len(self.item_spawner.items) > old_item_count:
                    # New item was spawned, sync it
                    new_item = self.item_spawner.items[-1]
                    self._send_item_spawn(new_item)

                # Check for item pickups
                for player in self.players:
                    for item in self.item_spawner.items:
                        if not item.active:
                            self._send_item_pickup(item, player.id)
        else:
            # Client: just update item animations
            for item in self.item_spawner.items:
                item.update()
            self.item_spawner.items = [item for item in self.item_spawner.items if item.active]

        # Update explosions
        self.explosions = [(x, y, t - 1) for x, y, t in self.explosions if t > 1]

        # Host: periodic full state sync (every 30 frames = 1 second)
        if self.use_network and self.is_host:
            self.state_sync_timer += 1
            if self.state_sync_timer >= 30:
                self._send_game_state()
                self.state_sync_timer = 0

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
            # Host syncs bullets to client
            if self.use_network and self.is_host:
                for bullet in new_bullets:
                    self._send_bullet_spawn(bullet)
        if place_mine:
            self._place_mine(player)

        # Send input to network if this is our player
        if self.use_network and self.network and player_index == self.network.my_player_id:
            # Only send if there's actual input (movement or action)
            if dx != 0 or dy != 0 or shoot or place_mine:
                self._send_player_input(dx, dy, shoot, place_mine, player)
            # Position sync less frequently when idle (every 15 frames = 0.5 seconds at 30fps)
            elif pyxel.frame_count % 15 == 0:
                self._send_position_sync(player)

    def _place_mine(self, player):
        """Place a mine at player's location"""
        from items import Mine
        if player.alive:
            mine = Mine(player.x, player.y, player.id)
            self.mines.append(mine)
            # Host syncs mine to client
            if self.use_network and self.is_host:
                self._send_mine_spawn(mine)

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

    def _send_player_input(self, dx, dy, shoot, place_mine, player):
        """Send local player input to network with position"""
        if self.network and self.network.peer:
            input_data = {
                "type": "player_input",
                "player_id": player.id,
                "dx": dx,
                "dy": dy,
                "shoot": shoot,
                "place_mine": place_mine,
                "x": player.x,
                "y": player.y,
                "direction": player.direction
            }
            self.network.peer.send(input_data)

    def _send_position_sync(self, player):
        """Send position sync for idle player"""
        if self.network and self.network.peer:
            sync_data = {
                "type": "position_sync",
                "player_id": player.id,
                "x": player.x,
                "y": player.y,
                "direction": player.direction
            }
            self.network.peer.send(sync_data)

    def _apply_remote_input(self, player, input_data):
        """Apply remote player's input with interpolation for smooth movement"""
        msg_type = input_data.get("type")

        # Get target position from network
        target_x = input_data.get("x", player.x)
        target_y = input_data.get("y", player.y)
        target_dir = input_data.get("direction", player.direction)

        # Store target for interpolation
        self.remote_targets[player.id] = (target_x, target_y, target_dir)

        # Direction updates immediately (looks better)
        player.direction = target_dir

        if msg_type == "position_sync":
            # Position sync - just update target, interpolation happens in update
            return

        # player_input message - apply actions immediately
        shoot = input_data.get("shoot", False)
        place_mine = input_data.get("place_mine", False)

        # Apply actions
        if shoot:
            new_bullets = player.shoot()
            self.bullets.extend(new_bullets)
            # Host syncs bullets to client
            if self.is_host:
                for bullet in new_bullets:
                    self._send_bullet_spawn(bullet)
        if place_mine:
            self._place_mine(player)

    def _interpolate_remote_players(self):
        """Smoothly interpolate remote players toward their target positions"""
        if not self.use_network or not self.network:
            return

        my_id = self.network.my_player_id

        for player in self.players:
            if player.id == my_id:
                continue  # Don't interpolate our own player

            if player.id in self.remote_targets:
                target_x, target_y, _ = self.remote_targets[player.id]

                # Calculate distance
                dx = target_x - player.x
                dy = target_y - player.y
                distance = (dx * dx + dy * dy) ** 0.5

                # If too far away (teleport/respawn), snap immediately
                if distance > 50:
                    player.x = target_x
                    player.y = target_y
                elif distance > 0.5:
                    # Smooth interpolation
                    player.x += dx * self.interpolation_speed
                    player.y += dy * self.interpolation_speed

    # ===== Network Sync Methods (Host -> Client) =====

    def _send_map_data(self):
        """Host sends map data to client at game start"""
        if self.network and self.network.peer:
            # Flatten the 2D map array
            flat_map = []
            for row in self.game_map:
                flat_map.extend(row)
            self.network.peer.send({
                "type": "map_data",
                "map": flat_map,
                "width": MAP_WIDTH,
                "height": MAP_HEIGHT
            })
            print("[GameInstance] Host sent map data to client")

    def _send_game_state(self):
        """Host sends periodic full game state sync"""
        if self.network and self.network.peer:
            # Player states (including power-up effects)
            players_data = []
            for p in self.players:
                players_data.append({
                    "id": p.id,
                    "x": p.x,
                    "y": p.y,
                    "direction": p.direction,
                    "hp": p.hp,
                    "kills": p.kills,
                    "alive": p.alive,
                    # Power-up states for visual effects
                    "has_shield": p.has_shield,
                    "has_triple_shot": p.has_triple_shot,
                    "has_speed_boost": p.has_speed_boost,
                    "has_full_vision": p.has_full_vision
                })

            # Item states
            items_data = []
            for item in self.item_spawner.items:
                items_data.append({
                    "x": item.x,
                    "y": item.y,
                    "type": item.type,
                    "active": item.active
                })

            self.network.peer.send({
                "type": "game_state",
                "players": players_data,
                "items": items_data,
                "game_over": self.game_over,
                "winner_id": self.winner_id
            })

    def _send_bullet_spawn(self, bullet):
        """Host sends bullet spawn to client"""
        if self.network and self.network.peer:
            self.network.peer.send({
                "type": "bullet_spawn",
                "x": bullet.x,
                "y": bullet.y,
                "vx": bullet.vx,
                "vy": bullet.vy,
                "owner_id": bullet.owner_id
            })

    def _send_item_spawn(self, item):
        """Host sends item spawn to client"""
        if self.network and self.network.peer:
            self.network.peer.send({
                "type": "item_spawn",
                "x": item.x,
                "y": item.y,
                "item_type": item.type
            })

    def _send_item_pickup(self, item, player_id):
        """Host sends item pickup to client"""
        if self.network and self.network.peer:
            self.network.peer.send({
                "type": "item_pickup",
                "x": item.x,
                "y": item.y,
                "player_id": player_id,
                "item_type": item.type  # Include item type for immediate effect
            })

    def _send_player_damage(self, player, died, attacker_id):
        """Host sends player damage to client"""
        if self.network and self.network.peer:
            self.network.peer.send({
                "type": "player_damage",
                "player_id": player.id,
                "hp": player.hp,
                "died": died,
                "attacker_id": attacker_id,
                "x": player.x,
                "y": player.y
            })

    def _send_explosion(self, x, y):
        """Host sends explosion to client"""
        if self.network and self.network.peer:
            self.network.peer.send({
                "type": "explosion",
                "x": x,
                "y": y
            })

    def _send_mine_spawn(self, mine):
        """Host sends mine spawn to client"""
        if self.network and self.network.peer:
            self.network.peer.send({
                "type": "mine_spawn",
                "x": mine.x,
                "y": mine.y,
                "owner_id": mine.owner_id
            })

    # ===== Network Apply Methods (Client receives from Host) =====

    def _apply_map_data(self, msg):
        """Client applies map data from host"""
        flat_map = msg.get("map", [])
        width = msg.get("width", MAP_WIDTH)
        height = msg.get("height", MAP_HEIGHT)

        # Reconstruct 2D map
        self.game_map = []
        for y in range(height):
            row = flat_map[y * width:(y + 1) * width]
            self.game_map.append(row)

        # Reinitialize item spawner with new map
        from items import ItemSpawner
        self.item_spawner = ItemSpawner(self.game_map)
        print("[GameInstance] Client received map data from host")

    def _apply_game_state(self, msg):
        """Client applies full game state from host"""
        # Update players
        players_data = msg.get("players", [])
        for pdata in players_data:
            player_id = pdata.get("id")
            if player_id is not None and player_id < len(self.players):
                player = self.players[player_id]
                # Only update remote player positions (local player is authoritative)
                if self.network and player_id != self.network.my_player_id:
                    self.remote_targets[player_id] = (pdata.get("x"), pdata.get("y"), pdata.get("direction"))
                # Always sync HP and kills
                player.hp = pdata.get("hp", player.hp)
                player.kills = pdata.get("kills", player.kills)
                player.alive = pdata.get("alive", player.alive)
                # Sync power-up states for visual effects
                player.has_shield = pdata.get("has_shield", player.has_shield)
                player.has_triple_shot = pdata.get("has_triple_shot", player.has_triple_shot)
                player.has_speed_boost = pdata.get("has_speed_boost", player.has_speed_boost)
                player.has_full_vision = pdata.get("has_full_vision", player.has_full_vision)

        # Update items
        items_data = msg.get("items", [])
        from items import Item
        self.item_spawner.items = []
        for idata in items_data:
            if idata.get("active", True):
                item = Item(idata.get("x"), idata.get("y"), idata.get("type"))
                self.item_spawner.items.append(item)

        # Update game over state
        self.game_over = msg.get("game_over", False)
        winner_id = msg.get("winner_id")
        if winner_id is not None and winner_id < len(self.players):
            self.winner = self.players[winner_id]
            self.winner_id = winner_id

    def _apply_bullet_spawn(self, msg):
        """Client applies bullet spawn from host"""
        from bullet import Bullet
        bullet = Bullet(
            msg.get("x"),
            msg.get("y"),
            msg.get("vx"),
            msg.get("vy"),
            msg.get("owner_id")
        )
        self.bullets.append(bullet)

    def _apply_item_spawn(self, msg):
        """Client applies item spawn from host"""
        from items import Item
        item = Item(msg.get("x"), msg.get("y"), msg.get("item_type"))
        self.item_spawner.items.append(item)

    def _apply_item_pickup(self, msg):
        """Client applies item pickup from host"""
        x = msg.get("x")
        y = msg.get("y")
        player_id = msg.get("player_id")
        item_type = msg.get("item_type")

        # Activate item effect on player immediately
        if player_id is not None and player_id < len(self.players) and item_type is not None:
            self.players[player_id].activate_item(item_type)

        # Find and remove the item from the list
        for item in self.item_spawner.items:
            if abs(item.x - x) < 1 and abs(item.y - y) < 1:
                item.active = False
                break

    def _apply_player_damage(self, msg):
        """Client applies player damage from host"""
        player_id = msg.get("player_id")
        if player_id is not None and player_id < len(self.players):
            player = self.players[player_id]
            player.hp = msg.get("hp", player.hp)
            died = msg.get("died", False)

            if died:
                player.alive = False
                player.respawn_timer = PLAYER_RESPAWN_TIME
                # Update position to respawn point
                player.x = msg.get("x", player.x)
                player.y = msg.get("y", player.y)

                # Update killer's kills
                attacker_id = msg.get("attacker_id")
                if attacker_id is not None and attacker_id < len(self.players):
                    killer = self.players[attacker_id]
                    killer.kills += 1
                    if killer.kills >= WIN_KILLS:
                        self.game_over = True
                        self.winner = killer
                        self.winner_id = killer.id

    def _apply_explosion(self, msg):
        """Client applies explosion from host"""
        x = msg.get("x")
        y = msg.get("y")
        self.explosions.append((x, y, 15))

    def _apply_mine_spawn(self, msg):
        """Client applies mine spawn from host"""
        from items import Mine
        mine = Mine(msg.get("x"), msg.get("y"), msg.get("owner_id"))
        self.mines.append(mine)

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
