# Tank Tank - Local Wi-Fi 2D Tank Battle Game

A retro-style 2D tank battle game built with Pyxel, supporting local network multiplayer.

## Features

- **Interactive Menu System** - Easy navigation with network connection testing
- **2D top-down tank combat** - Retro pixel art style
- **Local Wi-Fi multiplayer** (2-4 players) - Host or join games on same network
- **Bullet reflection mechanics** - 4 types of mirror surfaces
- **Power-up items** - Triple shot, shield, mine, speed boost, full vision
- **Tank track trails** - Visual feedback for movement
- **Player name input** - Customize your identity in multiplayer
- **Lobby system** - Wait for players before starting
- **First to 5 kills wins**

## Requirements

```bash
pip install pyxel
```

## How to Play

### With Menu (Recommended)

```bash
python main.py
```

This will show a menu where you can:

- Start local multiplayer (2 players on same device)
- Host a network game (wait for players to join)
- Join a network game (search for available hosts)

### Quick Start (Skip Menu)

```bash
python main.py --quick-local
```

Immediately starts a 2-player local game.

## Controls

### Menu Navigation

- W/S or Up/Down: Navigate options
- Space/Enter: Select option
- ESC: Go back
- Type your name when prompted

### In-Game

- Arrow Keys / WASD: Move tank (Player 1)
- IJKL: Move tank (Player 2 in local multiplayer)
- Space: Shoot (Player 1)
- H: Shoot (Player 2)
- E: Place mine (Player 1)
- Q: Quit
- R: Restart (when game over)
- ESC: Return to menu (when game over)

## Game Rules

- Each tank has 3 HP
- Getting hit 3 times causes respawn
- Items spawn randomly and activate on pickup
- First player to reach 5 kills wins

## Project Structure

```text
Mini-Project/
├── main.py              # Entry point with CLI args
├── app.py               # Main application with menu integration
├── menu.py              # Menu and lobby UI system
├── game.py              # Original game class (for quick-start)
├── player.py            # Player/Tank class
├── bullet.py            # Bullet physics and reflection
├── map_generator.py     # Procedural map generation
├── items.py             # Power-up items and mines
├── network.py           # UDP networking with discovery
├── constants.py         # Game constants and configuration
├── README.md            # This file
├── QUICKSTART.md        # Quick start guide
├── DESIGN.md            # Design document
└── requirements.txt     # Python dependencies
```
