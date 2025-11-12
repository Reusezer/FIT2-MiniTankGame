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
        Example: peer.send({"type": "input", "x": 10, "y": 20})
        """
        if self.connected:
            self.outbox.put(msg_dict)

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
        self.sock.settimeout(None)  # Blocking mode for accept

        while self.running and not self.connected:
            try:
                conn, addr = self.sock.accept()
                print(f"Client connected from {addr}")
                self.conn = conn
                self.conn.settimeout(1.0)  # Set timeout on the connection socket
                self.connected = True

                # Start send/recv threads
                threading.Thread(target=self._send_loop, daemon=True).start()
                threading.Thread(target=self._recv_loop, daemon=True).start()
                break
            except OSError as e:
                if self.running:  # Only print if we're still supposed to be running
                    print(f"Server error: {e}")
                break

    def _client_loop(self):
        """Client: keep trying to connect"""
        retry_count = 0
        max_retries = 10

        while self.running and retry_count < max_retries:
            try:
                self.sock.connect((self.server_ip, self.port))
                self.conn = self.sock
                self.conn.settimeout(1.0)  # Set timeout on the connection socket
                self.connected = True
                print("Connected to server!")

                # Start send/recv threads
                threading.Thread(target=self._send_loop, daemon=True).start()
                threading.Thread(target=self._recv_loop, daemon=True).start()
                break
            except OSError:
                retry_count += 1
                print(f"Connection attempt {retry_count}/{max_retries}...")
                time.sleep(1)

        if retry_count >= max_retries:
            print("Failed to connect after max retries")

    def _send_loop(self):
        """Background thread: send messages from outbox"""
        while self.running and self.connected:
            try:
                msg = self.outbox.get(timeout=0.1)
                data = (json.dumps(msg) + "\n").encode("utf-8")
                self.conn.sendall(data)
            except queue.Empty:
                continue
            except OSError:
                print("Connection lost (send)")
                self.connected = False
                break

    def _recv_loop(self):
        """Background thread: receive messages into inbox"""
        buffer = b""

        while self.running and self.connected:
            try:
                chunk = self.conn.recv(4096)
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
                            print(f"Invalid JSON: {line}")
            except socket.timeout:
                # Timeout is expected, just continue
                continue
            except OSError as e:
                print(f"Connection lost (recv): {e}")
                self.connected = False
                break


class GameNetworkManager:
    """
    High-level wrapper for Tank Tank game networking
    Handles player state sync, lobby, etc.
    """

    def __init__(self, is_server, server_ip=None):
        self.peer = NetworkPeer(is_server, server_ip)
        self.is_server = is_server
        self.my_player_id = 0 if is_server else 1
        self.other_player_id = 1 if is_server else 0

        # Game state
        self.player_states = {}  # {player_id: {x, y, direction, hp, ...}}
        self.player_inputs = {}  # {player_id: {keys_pressed}}

    def send_player_state(self, player_data):
        """
        Send my player state to opponent
        player_data = {x, y, direction, hp, kills, alive}
        """
        self.peer.send({
            "type": "player_state",
            "player_id": self.my_player_id,
            "data": player_data
        })

    def send_input(self, input_data):
        """
        Send input (lighter than full state)
        input_data = {dx, dy, shoot, place_mine}
        """
        self.peer.send({
            "type": "input",
            "player_id": self.my_player_id,
            "data": input_data
        })

    def send_game_event(self, event_type, event_data):
        """
        Send game events (bullet fired, player hit, etc.)
        """
        self.peer.send({
            "type": "game_event",
            "event": event_type,
            "data": event_data
        })

    def update(self):
        """Call this in Pyxel update() to process network messages"""
        msg = self.peer.recv_latest()

        if msg:
            msg_type = msg.get("type")

            if msg_type == "player_state":
                player_id = msg.get("player_id")
                data = msg.get("data")
                self.player_states[player_id] = data

            elif msg_type == "input":
                player_id = msg.get("player_id")
                data = msg.get("data")
                self.player_inputs[player_id] = data

            elif msg_type == "game_event":
                # Handle game events
                event = msg.get("event")
                data = msg.get("data")
                # Process event (to be implemented)

        return msg

    def get_other_player_state(self):
        """Get opponent's latest state"""
        return self.player_states.get(self.other_player_id)

    def is_connected(self):
        """Check if connected"""
        return self.peer.is_connected()

    def stop(self):
        """Cleanup"""
        self.peer.stop()


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

        # Create TCP peer
        self.peer = None

        if is_host:
            try:
                self.peer = NetworkPeer(is_server=True)
                self.connection_established = True
                self.my_ip = self.peer.my_ip
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
        """Update network state"""
        if self.peer:
            # Check connection status
            if self.peer.is_connected():
                if self.is_host and not self.clients:
                    # Client connected
                    self.clients = {("client", NETWORK_PORT): 1}
                    print(f"[NetworkManager] Host: Client connected, clients dict: {self.clients}")
                elif not self.is_host and not self.my_player_id:
                    # Connected to host
                    self.my_player_id = 1
                    print(f"[NetworkManager] Client: Connected to host, player_id: {self.my_player_id}")

    def stop(self):
        """Stop networking"""
        self.running = False
        if self.peer:
            self.peer.stop()

    def join_game(self):
        """Join game (auto-handled by TCP connection)"""
        return self.peer and self.peer.is_connected()
