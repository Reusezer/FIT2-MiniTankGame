"""
Clean TCP-based networking for Tank Tank
Based on proven pattern: threading + queues + no blocking in update()
"""

import socket
import threading
import queue
import json
import time
from constants import NETWORK_PORT


class NetworkPeer:
    """
    Non-blocking TCP network peer for Pyxel games
    - Server: listens for one client connection
    - Client: connects to server IP
    - Messages: JSON dicts separated by newlines
    - Thread-safe: uses queues, never blocks in game loop
    """

    def __init__(self, is_server, server_ip=None, port=NETWORK_PORT):
        self.is_server = is_server
        self.port = port
        self.server_ip = server_ip

        # Thread-safe communication
        self.inbox = queue.Queue()
        self.outbox = queue.Queue()

        # Connection state
        self.conn = None
        self.connected = False
        self.running = True

        # Create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Get local IP
        self.my_ip = self._get_local_ip()

        # Start appropriate thread
        if is_server:
            print(f"Starting server on {self.my_ip}:{port}")
            self.sock.bind(('', port))
            self.sock.listen(1)
            threading.Thread(target=self._server_loop, daemon=True).start()
        else:
            print(f"Connecting to {server_ip}:{port}")
            threading.Thread(target=self._client_loop, daemon=True).start()

    def _get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ===== Public API (call from Pyxel update/draw) =====

    def send(self, msg_dict):
        """
        Send a message (dict). Non-blocking, safe to call from update().
        """
        if self.connected:
            self.outbox.put(msg_dict)

    def recv_all(self):
        """
        Get ALL pending messages as a list. Call from update().
        Returns: list of dicts (may be empty)
        """
        messages = []
        while not self.inbox.empty():
            try:
                messages.append(self.inbox.get_nowait())
            except queue.Empty:
                break
        return messages

    def recv_latest(self):
        """
        Get most recent message (or None). Call from update().
        Returns: dict or None
        """
        last_msg = None
        while not self.inbox.empty():
            try:
                last_msg = self.inbox.get_nowait()
            except queue.Empty:
                break
        return last_msg

    def is_connected(self):
        """Check if connection is active"""
        return self.connected

    def stop(self):
        """Cleanly shut down networking"""
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

    # ===== Internal threading logic =====

    def _server_loop(self):
        """Server: wait for client connection"""
        print("Waiting for client...")

        while self.running and not self.connected:
            try:
                self.sock.settimeout(1.0)
                conn, addr = self.sock.accept()
                print(f"Client connected from {addr}")
                self.conn = conn
                self.conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.connected = True

                # Start send/recv threads
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
        """Client: keep trying to connect"""
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

                # Start send/recv threads
                threading.Thread(target=self._send_loop, daemon=True).start()
                threading.Thread(target=self._recv_loop, daemon=True).start()
                break
            except (socket.timeout, OSError) as e:
                retry_count += 1
                print(f"Connection attempt {retry_count}/{max_retries}... ({e})")
                time.sleep(0.5)

        if retry_count >= max_retries:
            print("Failed to connect after max retries")

    def _send_loop(self):
        """Background thread: send messages from outbox"""
        while self.running and self.connected:
            try:
                # Batch multiple messages if available (reduces syscalls)
                messages = []
                try:
                    # Get first message (blocking)
                    messages.append(self.outbox.get(timeout=0.033))  # ~30fps
                    # Get any additional pending messages (non-blocking)
                    while len(messages) < 5:  # Batch up to 5 messages
                        messages.append(self.outbox.get_nowait())
                except queue.Empty:
                    pass

                if messages:
                    # Send all messages in one syscall
                    data = "".join(json.dumps(msg) + "\n" for msg in messages).encode("utf-8")
                    self.conn.sendall(data)
            except queue.Empty:
                continue
            except OSError as e:
                if self.running:
                    print(f"Connection lost (send): {e}")
                self.connected = False
                break

    def _recv_loop(self):
        """Background thread: receive messages into inbox"""
        buffer = b""
        self.conn.settimeout(0.033)  # ~30fps polling (matches game fps)

        while self.running and self.connected:
            try:
                chunk = self.conn.recv(8192)  # Larger buffer for efficiency
                if not chunk:
                    print("Connection closed by peer")
                    self.connected = False
                    break

                buffer += chunk

                # Process complete messages (newline-separated)
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


# For backward compatibility with old code
class NetworkManager:
    """Wrapper to make it compatible with existing menu/app code"""

    def __init__(self, is_host=False, direct_ip=None):
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
        # Map data received from host (for client)
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
                self.my_player_id = 0  # Host is player 0
            except Exception as e:
                print(f"Failed to start server: {e}")
                self.connection_established = False
        else:
            if direct_ip:
                self.peer = NetworkPeer(is_server=False, server_ip=direct_ip)
                self.host_address = (direct_ip, NETWORK_PORT)

    def start(self):
        """Start networking"""
        self.running = True

    def update(self):
        """Update network state and return game messages"""
        if not self.peer:
            return []

        # Check connection status
        if self.peer.is_connected():
            if self.is_host and not self.clients:
                self.clients = {("client", NETWORK_PORT): 1}
                print(f"[NetworkManager] Host: Client connected")
            elif not self.is_host and self.my_player_id is None:
                self.my_player_id = 1
                print(f"[NetworkManager] Client: Connected, player_id=1")

        # Process incoming messages
        game_messages = []
        messages = self.peer.recv_all()
        for msg in messages:
            msg_type = msg.get("type")
            # Handle lobby/system messages internally
            if msg_type in ("player_join", "player_list", "start_game"):
                self._handle_message(msg)
            else:
                # Return game messages (like player_input) to the caller
                game_messages.append(msg)

        return game_messages

    def _handle_message(self, msg):
        """Handle incoming network messages"""
        msg_type = msg.get("type")

        if msg_type == "player_join":
            player_id = msg.get("player_id", 1)
            player_name = msg.get("name", f"Player {player_id}")
            self.player_names[player_id] = player_name
            print(f"[NetworkManager] Player joined: {player_name} (ID: {player_id})")
            if self.is_host:
                self.send_player_list()

        elif msg_type == "player_list":
            self.player_names = msg.get("players", {})
            print(f"[NetworkManager] Received player list: {self.player_names}")

        elif msg_type == "start_game":
            print(f"[NetworkManager] Received start_game signal")
            self.game_starting = True
            # Store map data for GameInstance creation
            self.shared_map_data = msg.get("map")
            self.map_width = msg.get("map_width")
            self.map_height = msg.get("map_height")

    def stop(self):
        """Stop networking"""
        self.running = False
        if self.peer:
            self.peer.stop()

    def join_game(self, player_name=""):
        """Join game and send player name"""
        if self.peer and self.peer.is_connected():
            self.my_player_name = player_name
            self.peer.send({
                "type": "player_join",
                "player_id": 1,
                "name": player_name
            })
            print(f"[NetworkManager] Sent join request: {player_name}")
            return True
        return False

    def send_player_list(self):
        """Host sends current player list to all clients"""
        if self.is_host and self.peer and self.peer.is_connected():
            self.peer.send({
                "type": "player_list",
                "players": self.player_names
            })

    def broadcast_start_game(self, game_map=None):
        """Host broadcasts game start to all clients with map data"""
        if self.is_host and self.peer and self.peer.is_connected():
            msg = {
                "type": "start_game",
                "num_players": len(self.player_names)
            }
            # Include map data if provided
            if game_map is not None:
                from constants import MAP_WIDTH, MAP_HEIGHT
                flat_map = []
                for row in game_map:
                    flat_map.extend(row)
                msg["map"] = flat_map
                msg["map_width"] = MAP_WIDTH
                msg["map_height"] = MAP_HEIGHT
            self.peer.send(msg)
            print(f"[NetworkManager] Broadcasting start_game with map data")
