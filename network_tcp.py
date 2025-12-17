"""
TCP-based Networking Module for Tank Tank

This module provides network communication between two players over TCP.
It uses a threading model to avoid blocking the game loop.

Architecture:
- NetworkPeer: Low-level TCP connection handler (handles actual socket communication)
- NetworkManager: High-level game networking (handles lobby, player sync, game state)

Threading Model:
- Main Thread: Pyxel game loop (update/draw at 30fps)
- Server/Client Thread: Handles initial TCP connection
- Send Thread: Sends messages from outbox queue to socket
- Receive Thread: Receives messages from socket to inbox queue

Message Format:
- JSON dictionaries separated by newlines
- Example: {"type": "player_input", "x": 100, "y": 50}\n
"""

import socket
import threading
import queue
import json
import time
from constants import NETWORK_PORT


class NetworkPeer:
    """
    Low-level TCP connection handler.

    Provides thread-safe, non-blocking message passing over TCP.
    Uses queues to communicate between the game loop and network threads.

    Usage:
        # Server (Host)
        peer = NetworkPeer(is_server=True)

        # Client
        peer = NetworkPeer(is_server=False, server_ip="192.168.1.100")

        # In game loop
        peer.send({"type": "player_input", "x": 100})
        messages = peer.recv_all()
    """

    def __init__(self, is_server, server_ip=None, port=NETWORK_PORT):
        """
        Initialize network peer.

        Args:
            is_server: True for host, False for client
            server_ip: IP address to connect to (client only)
            port: Network port (default: 9999)
        """
        self.is_server = is_server
        self.port = port
        self.server_ip = server_ip

        # Thread-safe message queues
        self.inbox = queue.Queue()   # Messages received from peer
        self.outbox = queue.Queue()  # Messages to send to peer

        # Connection state
        self.conn = None          # Active connection socket
        self.connected = False    # True when connected
        self.running = True       # False when shutting down

        # Create TCP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Get local IP for display
        self.my_ip = self._get_local_ip()

        # Start connection thread
        if is_server:
            print(f"Starting server on {self.my_ip}:{port}")
            self.sock.bind(('', port))
            self.sock.listen(1)
            threading.Thread(target=self._server_loop, daemon=True).start()
        else:
            print(f"Connecting to {server_ip}:{port}")
            threading.Thread(target=self._client_loop, daemon=True).start()

    def _get_local_ip(self):
        """Get local IP address by connecting to external server."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ========== Public API (call from game loop) ==========

    def send(self, msg_dict):
        """
        Send a message to the peer. Non-blocking.

        Args:
            msg_dict: Dictionary to send (will be JSON encoded)
        """
        if self.connected:
            self.outbox.put(msg_dict)

    def recv_all(self):
        """
        Get all pending received messages.

        Returns:
            List of dictionaries (may be empty)
        """
        messages = []
        while not self.inbox.empty():
            try:
                messages.append(self.inbox.get_nowait())
            except queue.Empty:
                break
        return messages

    def is_connected(self):
        """Check if connection is active."""
        return self.connected

    def stop(self):
        """Shut down the network connection."""
        self.running = False
        self.connected = False
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        try:
            self.sock.close()
        except:
            pass

    # ========== Internal Threading Logic ==========

    def _server_loop(self):
        """Server thread: wait for client connection."""
        print("Waiting for client...")

        while self.running and not self.connected:
            try:
                self.sock.settimeout(1.0)
                conn, addr = self.sock.accept()
                print(f"Client connected from {addr}")
                self.conn = conn
                self.conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.connected = True

                # Start send/receive threads
                threading.Thread(target=self._send_loop, daemon=True).start()
                threading.Thread(target=self._recv_loop, daemon=True).start()
                break
            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    print(f"Server error: {e}")
                break

    def _client_loop(self):
        """Client thread: connect to server with retry."""
        retry_count = 0
        max_retries = 30

        while self.running and retry_count < max_retries:
            try:
                self.sock.settimeout(3.0)
                self.sock.connect((self.server_ip, self.port))
                self.conn = self.sock
                self.conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.connected = True
                print("Connected to server!")

                # Start send/receive threads
                threading.Thread(target=self._send_loop, daemon=True).start()
                threading.Thread(target=self._recv_loop, daemon=True).start()
                break
            except (socket.timeout, OSError) as e:
                retry_count += 1
                print(f"Connection attempt {retry_count}/{max_retries}...")
                time.sleep(0.5)

        if retry_count >= max_retries:
            print("Failed to connect after max retries")

    def _send_loop(self):
        """Send thread: send messages from outbox to socket."""
        while self.running and self.connected:
            try:
                # Collect messages to send (batch for efficiency)
                messages = []
                try:
                    messages.append(self.outbox.get(timeout=0.033))
                    while len(messages) < 5:
                        messages.append(self.outbox.get_nowait())
                except queue.Empty:
                    pass

                if messages:
                    # Send all as one TCP packet
                    data = "".join(json.dumps(msg) + "\n" for msg in messages)
                    self.conn.sendall(data.encode("utf-8"))
            except queue.Empty:
                continue
            except OSError as e:
                if self.running:
                    print(f"Connection lost (send): {e}")
                self.connected = False
                break

    def _recv_loop(self):
        """Receive thread: receive messages from socket to inbox."""
        buffer = b""
        self.conn.settimeout(0.033)

        while self.running and self.connected:
            try:
                chunk = self.conn.recv(8192)
                if not chunk:
                    print("Connection closed by peer")
                    self.connected = False
                    break

                buffer += chunk

                # Parse complete JSON messages (newline-separated)
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line.strip():
                        try:
                            msg = json.loads(line.decode("utf-8"))
                            self.inbox.put(msg)
                        except json.JSONDecodeError:
                            pass
            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    print(f"Connection lost (recv): {e}")
                self.connected = False
                break


class NetworkManager:
    """
    High-level game networking manager.

    Handles:
    - Lobby management (player names, game start)
    - Game state synchronization
    - Map data sharing

    Used by app.py and menu.py for network game setup.
    """

    def __init__(self, is_host=False, direct_ip=None):
        """
        Initialize network manager.

        Args:
            is_host: True if hosting the game
            direct_ip: IP address to connect to (client only)
        """
        self.is_host = is_host
        self.direct_ip = direct_ip
        self.running = False
        self.connection_established = False
        self.my_ip = "127.0.0.1"
        self.host_address = None
        self.clients = {}
        self.my_player_id = None
        self.player_names = {}
        self.my_player_name = ""
        self.game_starting = False

        # Map data for synchronization
        self.shared_map_data = None
        self.map_width = None
        self.map_height = None

        # Create TCP peer
        self.peer = None

        if is_host:
            try:
                self.peer = NetworkPeer(is_server=True)
                self.connection_established = True
                self.my_ip = self.peer.my_ip
                self.my_player_id = 0  # Host is always player 0
            except Exception as e:
                print(f"Failed to start server: {e}")
                self.connection_established = False
        else:
            if direct_ip:
                self.peer = NetworkPeer(is_server=False, server_ip=direct_ip)
                self.host_address = (direct_ip, NETWORK_PORT)

    def start(self):
        """Start networking."""
        self.running = True

    def update(self):
        """
        Process network messages. Call this every frame.

        Returns:
            List of game messages (player_input, game_state, etc.)
        """
        if not self.peer:
            return []

        # Update connection status
        if self.peer.is_connected():
            if self.is_host and not self.clients:
                self.clients = {("client", NETWORK_PORT): 1}
                print("[NetworkManager] Host: Client connected")
            elif not self.is_host and self.my_player_id is None:
                self.my_player_id = 1
                print("[NetworkManager] Client: Connected, player_id=1")

        # Process messages
        game_messages = []
        messages = self.peer.recv_all()
        for msg in messages:
            msg_type = msg.get("type")
            # Lobby messages handled internally
            if msg_type in ("player_join", "player_list", "start_game"):
                self._handle_message(msg)
            else:
                # Game messages returned to caller
                game_messages.append(msg)

        return game_messages

    def _handle_message(self, msg):
        """Handle lobby/system messages."""
        msg_type = msg.get("type")

        if msg_type == "player_join":
            player_id = msg.get("player_id", 1)
            player_name = msg.get("name", f"Player {player_id}")
            self.player_names[player_id] = player_name
            print(f"[NetworkManager] Player joined: {player_name}")
            if self.is_host:
                self.send_player_list()

        elif msg_type == "player_list":
            self.player_names = msg.get("players", {})

        elif msg_type == "start_game":
            print("[NetworkManager] Received start_game signal")
            self.game_starting = True
            self.shared_map_data = msg.get("map")
            self.map_width = msg.get("map_width")
            self.map_height = msg.get("map_height")

    def stop(self):
        """Stop networking."""
        self.running = False
        if self.peer:
            self.peer.stop()

    def join_game(self, player_name=""):
        """Client: Send join request to host."""
        if self.peer and self.peer.is_connected():
            self.my_player_name = player_name
            self.peer.send({
                "type": "player_join",
                "player_id": 1,
                "name": player_name
            })
            return True
        return False

    def send_player_list(self):
        """Host: Broadcast player list to clients."""
        if self.is_host and self.peer and self.peer.is_connected():
            self.peer.send({
                "type": "player_list",
                "players": self.player_names
            })

    def broadcast_start_game(self, game_map=None):
        """Host: Broadcast game start signal with map data."""
        if self.is_host and self.peer and self.peer.is_connected():
            msg = {
                "type": "start_game",
                "num_players": len(self.player_names)
            }
            # Include map data
            if game_map is not None:
                from constants import MAP_WIDTH, MAP_HEIGHT
                flat_map = []
                for row in game_map:
                    flat_map.extend(row)
                msg["map"] = flat_map
                msg["map_width"] = MAP_WIDTH
                msg["map_height"] = MAP_HEIGHT
            self.peer.send(msg)
            print("[NetworkManager] Broadcasting start_game with map data")
