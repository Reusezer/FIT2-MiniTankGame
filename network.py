import socket
import json
import threading
import time
from constants import *

class NetworkManager:
    """
    Simple UDP-based networking for local multiplayer
    Supports:
    - Host/client model
    - Lobby discovery via broadcast
    - Player input synchronization
    """

    def __init__(self, is_host=False):
        self.is_host = is_host
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setblocking(False)

        self.host_address = None
        self.clients = {}  # {address: player_id}
        self.running = False
        self.player_inputs = {}  # {player_id: input_data}
        self.my_player_id = None
        self.discovery_timer = 0
        self.connection_established = False

        if is_host:
            try:
                self.socket.bind(('', NETWORK_PORT))
                self.connection_established = True
            except OSError as e:
                print(f"Failed to bind to port {NETWORK_PORT}: {e}")
                self.connection_established = False
        else:
            self.socket.bind(('', 0))

    def start(self):
        """Start networking"""
        self.running = True
        if self.is_host:
            self._start_host()
        else:
            self._start_client()

    def stop(self):
        """Stop networking"""
        self.running = False
        self.socket.close()

    def _start_host(self):
        """Start as host - listen for client connections"""
        print(f"Hosting game on port {NETWORK_PORT}")

    def _start_client(self):
        """Start as client - discover and connect to host"""
        print(f"Searching for game...")
        # Send discovery broadcast
        self._send_discovery()

    def _send_discovery(self):
        """Send broadcast to discover hosts"""
        message = json.dumps({'type': 'DISCOVER', 'version': '1.0'})
        self.socket.sendto(message.encode(), ('<broadcast>', NETWORK_PORT))

    def update(self):
        """Process network messages"""
        if not self.running:
            return

        # Periodically send discovery if client and not connected
        if not self.is_host and not self.host_address:
            self.discovery_timer += 1
            if self.discovery_timer >= 30:  # Every second at 30fps
                self._send_discovery()
                self.discovery_timer = 0

        try:
            while True:
                data, address = self.socket.recvfrom(4096)
                self._handle_message(data, address)
        except BlockingIOError:
            pass

    def _handle_message(self, data, address):
        """Handle received network message"""
        try:
            message = json.loads(data.decode())
            msg_type = message.get('type')

            if msg_type == 'DISCOVER' and self.is_host:
                # Respond to client discovery
                response = json.dumps({
                    'type': 'LOBBY',
                    'players': len(self.clients) + 1,
                    'max_players': 4
                })
                self.socket.sendto(response.encode(), address)

            elif msg_type == 'LOBBY' and not self.is_host:
                # Found a host
                self.host_address = address
                print(f"Found game at {address}")

            elif msg_type == 'JOIN' and self.is_host:
                # Client wants to join
                player_id = len(self.clients) + 1
                self.clients[address] = player_id
                response = json.dumps({
                    'type': 'ACCEPT',
                    'player_id': player_id
                })
                self.socket.sendto(response.encode(), address)
                print(f"Client joined: {address} as Player {player_id}")

            elif msg_type == 'ACCEPT' and not self.is_host:
                # Host accepted join request
                self.my_player_id = message.get('player_id')
                print(f"Joined as Player {self.my_player_id}")

            elif msg_type == 'INPUT':
                # Player input update
                player_id = message.get('player_id')
                input_data = message.get('input')
                self.player_inputs[player_id] = input_data

            elif msg_type == 'STATE' and not self.is_host:
                # Game state update from host
                # This would sync game state for clients
                pass

        except Exception as e:
            print(f"Network error: {e}")

    def send_input(self, player_id, input_data):
        """Send player input to host"""
        if not self.host_address:
            return

        message = json.dumps({
            'type': 'INPUT',
            'player_id': player_id,
            'input': input_data
        })
        self.socket.sendto(message.encode(), self.host_address)

    def broadcast_state(self, game_state):
        """Host broadcasts game state to all clients"""
        if not self.is_host:
            return

        message = json.dumps({
            'type': 'STATE',
            'state': game_state
        })

        for address in self.clients.keys():
            self.socket.sendto(message.encode(), address)

    def join_game(self):
        """Send join request to host"""
        if not self.host_address:
            return False

        message = json.dumps({'type': 'JOIN'})
        self.socket.sendto(message.encode(), self.host_address)
        return True
