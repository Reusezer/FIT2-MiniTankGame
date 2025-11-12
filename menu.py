import pyxel
from constants import *

class MenuState:
    MAIN_MENU = 0
    ENTER_NAME = 1
    ENTER_IP = 2
    NETWORK_SETUP = 3
    LOBBY = 4
    CONNECTING = 5


class Menu:
    def __init__(self):
        self.state = MenuState.MAIN_MENU
        self.selected_option = 0
        self.player_name = ""
        self.host_ip = ""
        self.is_host = False
        self.network_status = "Not connected"
        self.lobby_players = []
        self.connecting_timer = 0
        self.error_message = ""
        self.cursor_blink = 0
        self.network_manager = None  # Store reference for drawing

        # Main menu options
        self.main_menu_options = [
            "LOCAL MULTIPLAYER",
            "HOST NETWORK GAME",
            "JOIN BY IP ADDRESS",
            "QUIT"
        ]

    def update(self, network_manager=None):
        self.cursor_blink = (self.cursor_blink + 1) % 60
        self.network_manager = network_manager  # Store for drawing

        if self.state == MenuState.MAIN_MENU:
            return self._update_main_menu()
        elif self.state == MenuState.ENTER_NAME:
            return self._update_name_input()
        elif self.state == MenuState.ENTER_IP:
            return self._update_ip_input()
        elif self.state == MenuState.NETWORK_SETUP:
            return self._update_network_setup(network_manager)
        elif self.state == MenuState.CONNECTING:
            return self._update_connecting(network_manager)
        elif self.state == MenuState.LOBBY:
            return self._update_lobby(network_manager)

        return None

    def _update_main_menu(self):
        # Navigate menu
        if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.KEY_W):
            self.selected_option = (self.selected_option - 1) % len(self.main_menu_options)
        if pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.KEY_S):
            self.selected_option = (self.selected_option + 1) % len(self.main_menu_options)

        # Select option
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            if self.selected_option == 0:  # Local multiplayer
                return "start_local"
            elif self.selected_option == 1:  # Host
                self.is_host = True
                self.state = MenuState.ENTER_NAME
            elif self.selected_option == 2:  # Join by IP
                self.is_host = False
                self.state = MenuState.ENTER_IP
            elif self.selected_option == 3:  # Quit
                return "quit"

        return None

    def _update_name_input(self):
        # Handle text input
        for key in range(pyxel.KEY_A, pyxel.KEY_Z + 1):
            if pyxel.btnp(key):
                if len(self.player_name) < 10:
                    char = chr(ord('A') + (key - pyxel.KEY_A))
                    if pyxel.btn(pyxel.KEY_SHIFT):
                        self.player_name += char
                    else:
                        self.player_name += char.lower()

        # Backspace
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.player_name = self.player_name[:-1]

        # Space
        if pyxel.btnp(pyxel.KEY_SPACE):
            if len(self.player_name) < 10:
                self.player_name += " "

        # Confirm name
        if pyxel.btnp(pyxel.KEY_RETURN):
            if len(self.player_name.strip()) > 0:
                self.state = MenuState.NETWORK_SETUP
                return "setup_network"
            else:
                self.error_message = "Name cannot be empty!"

        # Go back
        if pyxel.btnp(pyxel.KEY_B):
            self.state = MenuState.MAIN_MENU
            self.player_name = ""
            self.error_message = ""

        return None

    def _update_ip_input(self):
        """Handle IP address input"""
        # Handle text input for IP
        for key in range(pyxel.KEY_0, pyxel.KEY_9 + 1):
            if pyxel.btnp(key):
                if len(self.host_ip) < 15:  # Max IP length
                    self.host_ip += str(key - pyxel.KEY_0)

        # Period/dot
        if pyxel.btnp(pyxel.KEY_PERIOD):
            if len(self.host_ip) < 15:
                self.host_ip += "."

        # Backspace
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.host_ip = self.host_ip[:-1]

        # Confirm IP
        if pyxel.btnp(pyxel.KEY_RETURN):
            # Validate IP format
            parts = self.host_ip.split('.')
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts if p):
                self.state = MenuState.ENTER_NAME
                return None
            else:
                self.error_message = "Invalid IP format!"

        # Go back
        if pyxel.btnp(pyxel.KEY_B):
            self.state = MenuState.MAIN_MENU
            self.host_ip = ""
            self.error_message = ""

        return None

    def _update_network_setup(self, network_manager):
        # This state is handled by the main game
        # Just wait for network to be initialized
        if network_manager and network_manager.running:
            self.state = MenuState.CONNECTING

        if pyxel.btnp(pyxel.KEY_B):
            self.state = MenuState.MAIN_MENU
            return "cancel_network"

        return None

    def _update_connecting(self, network_manager):
        if network_manager:
            if self.is_host:
                # Host: check if clients connected
                if len(network_manager.clients) > 0:
                    self.state = MenuState.LOBBY
                    self.network_status = f"Connected ({len(network_manager.clients) + 1}/4)"
                    return None
            else:
                # Client: check if found host
                if network_manager.host_address:
                    self.state = MenuState.LOBBY
                    self.network_status = "Connected to host"
                    return "join_lobby"

        # Allow cancel with B key (wait indefinitely otherwise)
        if pyxel.btnp(pyxel.KEY_B):
            self.state = MenuState.MAIN_MENU
            self.error_message = "Connection cancelled"
            return "cancel_network"

        return None

    def _update_lobby(self, network_manager):
        # Update player list
        if network_manager:
            if self.is_host:
                self.lobby_players = [self.player_name] + [f"Player {i+2}" for i in range(len(network_manager.clients))]
                self.network_status = f"Players: {len(self.lobby_players)}/4"
            else:
                self.lobby_players = [self.player_name]
                self.network_status = "Waiting for host..."

        # Start game (host only)
        if self.is_host and pyxel.btnp(pyxel.KEY_RETURN):
            if len(self.lobby_players) >= 2:
                return "start_network"
            else:
                self.error_message = "Need at least 2 players!"

        # Go back
        if pyxel.btnp(pyxel.KEY_B):
            self.state = MenuState.MAIN_MENU
            return "cancel_network"

        return None

    def draw(self):
        pyxel.cls(COLOR_BG)

        if self.state == MenuState.MAIN_MENU:
            self._draw_main_menu()
        elif self.state == MenuState.ENTER_NAME:
            self._draw_name_input()
        elif self.state == MenuState.ENTER_IP:
            self._draw_ip_input()
        elif self.state == MenuState.NETWORK_SETUP:
            self._draw_network_setup()
        elif self.state == MenuState.CONNECTING:
            self._draw_connecting()
        elif self.state == MenuState.LOBBY:
            self._draw_lobby()

    def _draw_main_menu(self):
        # Title
        title = "TANK TANK"
        title_x = SCREEN_WIDTH // 2 - len(title) * 2
        pyxel.text(title_x, 30, title, COLOR_PLAYER_1)

        # Subtitle
        subtitle = "Local Wi-Fi Battle Game"
        subtitle_x = SCREEN_WIDTH // 2 - len(subtitle) * 2
        pyxel.text(subtitle_x, 45, subtitle, COLOR_UI)

        # Menu options
        start_y = 80
        for i, option in enumerate(self.main_menu_options):
            y = start_y + i * 15
            x = SCREEN_WIDTH // 2 - len(option) * 2

            color = COLOR_ITEM if i == self.selected_option else COLOR_UI
            pyxel.text(x, y, option, color)

            # Cursor
            if i == self.selected_option:
                pyxel.text(x - 10, y, ">", COLOR_PLAYER_1)

        # Error message
        if self.error_message:
            msg_x = SCREEN_WIDTH // 2 - len(self.error_message) * 2
            pyxel.text(msg_x, 170, self.error_message, COLOR_EXPLOSION)

        # Controls hint
        hint = "Use W/S or Arrows, Space to select"
        hint_x = SCREEN_WIDTH // 2 - len(hint) * 2
        pyxel.text(hint_x, 220, hint, COLOR_WALL)

        # Version
        version = "v1.0"
        pyxel.text(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 8, version, COLOR_WALL)

    def _draw_name_input(self):
        # Title
        title = "ENTER YOUR NAME"
        title_x = SCREEN_WIDTH // 2 - len(title) * 2
        pyxel.text(title_x, 60, title, COLOR_UI)

        # Input box
        box_x = 50
        box_y = 100
        box_w = SCREEN_WIDTH - 100
        box_h = 20

        pyxel.rect(box_x, box_y, box_w, box_h, COLOR_WALL)
        pyxel.rectb(box_x, box_y, box_w, box_h, COLOR_UI)

        # Player name
        name_display = self.player_name if self.player_name else "..."
        text_x = box_x + 5
        text_y = box_y + 7
        pyxel.text(text_x, text_y, name_display, COLOR_UI)

        # Cursor blink
        if self.cursor_blink < 30:
            cursor_x = text_x + len(self.player_name) * 4
            pyxel.line(cursor_x, text_y, cursor_x, text_y + 5, COLOR_ITEM)

        # Instructions
        inst1 = "Type your name (max 10 chars)"
        inst1_x = SCREEN_WIDTH // 2 - len(inst1) * 2
        pyxel.text(inst1_x, 140, inst1, COLOR_WALL)

        inst2 = "Press ENTER to continue"
        inst2_x = SCREEN_WIDTH // 2 - len(inst2) * 2
        pyxel.text(inst2_x, 155, inst2, COLOR_WALL)

        inst3 = "Press B to go back"
        inst3_x = SCREEN_WIDTH // 2 - len(inst3) * 2
        pyxel.text(inst3_x, 170, inst3, COLOR_WALL)

        # Error message
        if self.error_message:
            msg_x = SCREEN_WIDTH // 2 - len(self.error_message) * 2
            pyxel.text(msg_x, 195, self.error_message, COLOR_EXPLOSION)

    def _draw_ip_input(self):
        # Title
        title = "ENTER HOST IP ADDRESS"
        title_x = SCREEN_WIDTH // 2 - len(title) * 2
        pyxel.text(title_x, 60, title, COLOR_UI)

        # Input box
        box_x = 50
        box_y = 100
        box_w = SCREEN_WIDTH - 100
        box_h = 20

        pyxel.rect(box_x, box_y, box_w, box_h, COLOR_WALL)
        pyxel.rectb(box_x, box_y, box_w, box_h, COLOR_UI)

        # IP address
        ip_display = self.host_ip if self.host_ip else "0.0.0.0"
        text_x = box_x + 5
        text_y = box_y + 7
        pyxel.text(text_x, text_y, ip_display, COLOR_UI)

        # Cursor blink
        if self.cursor_blink < 30:
            cursor_x = text_x + len(self.host_ip) * 4
            pyxel.line(cursor_x, text_y, cursor_x, text_y + 5, COLOR_ITEM)

        # Instructions
        inst1 = "Type IP address (e.g. 192.168.1.100)"
        inst1_x = SCREEN_WIDTH // 2 - len(inst1) * 2
        pyxel.text(inst1_x, 140, inst1, COLOR_WALL)

        inst2 = "Use numbers and period (.)"
        inst2_x = SCREEN_WIDTH // 2 - len(inst2) * 2
        pyxel.text(inst2_x, 155, inst2, COLOR_WALL)

        inst3 = "Press ENTER to continue"
        inst3_x = SCREEN_WIDTH // 2 - len(inst3) * 2
        pyxel.text(inst3_x, 170, inst3, COLOR_WALL)

        inst4 = "Press B to go back"
        inst4_x = SCREEN_WIDTH // 2 - len(inst4) * 2
        pyxel.text(inst4_x, 185, inst4, COLOR_WALL)

        # Error message
        if self.error_message:
            msg_x = SCREEN_WIDTH // 2 - len(self.error_message) * 2
            pyxel.text(msg_x, 210, self.error_message, COLOR_EXPLOSION)

    def _draw_network_setup(self):
        title = "SETTING UP NETWORK..."
        title_x = SCREEN_WIDTH // 2 - len(title) * 2
        pyxel.text(title_x, SCREEN_HEIGHT // 2 - 10, title, COLOR_UI)

        # Spinner
        spinner_chars = ["|", "/", "-", "\\"]
        spinner = spinner_chars[(pyxel.frame_count // 10) % 4]
        pyxel.text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10, spinner, COLOR_ITEM)

    def _draw_connecting(self):
        # Title
        if self.is_host:
            title = "WAITING FOR PLAYERS..."
        else:
            title = "CONNECTING TO HOST..."

        title_x = SCREEN_WIDTH // 2 - len(title) * 2
        pyxel.text(title_x, 50, title, COLOR_UI)

        # Show server IP if hosting
        if self.is_host and self.network_manager:
            # Draw highlighted box for IP
            box_y = 75
            box_h = 38
            box_w = 180
            box_x = SCREEN_WIDTH // 2 - box_w // 2

            pyxel.rect(box_x, box_y, box_w, box_h, COLOR_WALL)
            pyxel.rectb(box_x, box_y, box_w, box_h, COLOR_ITEM)

            # Label
            label = "Share this IP:"
            label_x = SCREEN_WIDTH // 2 - len(label) * 2
            pyxel.text(label_x, box_y + 8, label, COLOR_UI)

            # IP address in bright yellow
            my_ip = self.network_manager.my_ip
            ip_text = f"{my_ip}:{NETWORK_PORT}"
            ip_x = SCREEN_WIDTH // 2 - len(ip_text) * 2
            pyxel.text(ip_x, box_y + 22, ip_text, COLOR_ITEM)

        # Animated spinner (no progress bar, just wait)
        spinner_chars = ["|", "/", "-", "\\"]
        spinner = spinner_chars[(pyxel.frame_count // 10) % 4]

        # Center the spinner
        spinner_y = 135 if self.is_host else 100
        pyxel.text(SCREEN_WIDTH // 2 - 2, spinner_y, spinner, COLOR_ITEM)

        # Waiting message with dots
        dots_chars = ["   ", ".  ", ".. ", "..."]
        dots = dots_chars[(pyxel.frame_count // 15) % 4]
        wait_msg = f"Please wait{dots}"
        wait_x = SCREEN_WIDTH // 2 - len(wait_msg) * 2
        wait_y = spinner_y + 25
        pyxel.text(wait_x, wait_y, wait_msg, COLOR_WALL)

        # Cancel instruction
        cancel = "Press B to cancel"
        cancel_x = SCREEN_WIDTH // 2 - len(cancel) * 2
        pyxel.text(cancel_x, 200, cancel, COLOR_WALL)

    def _draw_lobby(self):
        # Title
        title = "LOBBY"
        title_x = SCREEN_WIDTH // 2 - len(title) * 2
        pyxel.text(title_x, 30, title, COLOR_UI)

        # Status
        status_x = SCREEN_WIDTH // 2 - len(self.network_status) * 2
        pyxel.text(status_x, 50, self.network_status, COLOR_PLAYER_3)

        # Show IP if host (prominently with box)
        if self.is_host:
            import socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                my_ip = s.getsockname()[0]
                s.close()

                # Draw highlighted box
                box_y = 60
                box_h = 28
                pyxel.rect(40, box_y, SCREEN_WIDTH - 80, box_h, COLOR_WALL)
                pyxel.rectb(40, box_y, SCREEN_WIDTH - 80, box_h, COLOR_ITEM)

                # Label
                label = "Share this IP:"
                label_x = SCREEN_WIDTH // 2 - len(label) * 2
                pyxel.text(label_x, box_y + 5, label, COLOR_UI)

                # IP address in bright yellow
                ip_text = f"{my_ip}:{NETWORK_PORT}"
                ip_x = SCREEN_WIDTH // 2 - len(ip_text) * 2
                pyxel.text(ip_x, box_y + 15, ip_text, COLOR_ITEM)
            except:
                # Fallback
                error_text = "IP: Detection failed"
                error_x = SCREEN_WIDTH // 2 - len(error_text) * 2
                pyxel.text(error_x, 65, error_text, COLOR_EXPLOSION)

        # Player list (moved down to avoid overlap)
        list_y = 95 if self.is_host else 70
        list_title = "PLAYERS:"
        pyxel.text(60, list_y, list_title, COLOR_UI)

        for i, player in enumerate(self.lobby_players):
            y = list_y + 15 + i * 15
            color = [COLOR_PLAYER_1, COLOR_PLAYER_2, COLOR_PLAYER_3, COLOR_PLAYER_4][i % 4]

            # Color indicator
            pyxel.rect(65, y, 6, 6, color)

            # Player name
            pyxel.text(75, y, player, COLOR_UI)

        # Instructions
        if self.is_host:
            inst = "Press ENTER to start (min 2 players)"
            inst_x = SCREEN_WIDTH // 2 - len(inst) * 2
            pyxel.text(inst_x, 190, inst, COLOR_ITEM)
        else:
            inst = "Waiting for host to start..."
            inst_x = SCREEN_WIDTH // 2 - len(inst) * 2
            pyxel.text(inst_x, 190, inst, COLOR_WALL)

        cancel = "Press B to leave"
        cancel_x = SCREEN_WIDTH // 2 - len(cancel) * 2
        pyxel.text(cancel_x, 210, cancel, COLOR_WALL)

        # Error message
        if self.error_message:
            msg_x = SCREEN_WIDTH // 2 - len(self.error_message) * 2
            pyxel.text(msg_x, 230, self.error_message, COLOR_EXPLOSION)
