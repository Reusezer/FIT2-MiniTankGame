# Tank Tank

A retro-style 2D tank battle game built with Python and Pyxel. Battle your friends locally or over LAN in intense tank combat with reflective bullets, power-ups, and strategic gameplay.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pyxel](https://img.shields.io/badge/Pyxel-1.9+-green.svg)

## Features

- **Local Multiplayer**: 2 players on the same device
- **LAN Multiplayer**: Play over local network with direct IP connection
- **Reflective Bullets**: Bullets bounce off mirror surfaces for strategic shots
- **Power-ups**: Triple shot, shield, speed boost, full vision, and mines
- **Procedurally Generated Maps**: Every game has a unique battlefield
- **Retro Pixel Art**: Classic 16-color aesthetic

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Quick Install

```bash
# Navigate to the project directory
cd Mini-Project

# Install Pyxel
pip install pyxel

# Run the game
python3 main.py
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pyxel   | 1.9+    | Game engine and graphics |

## How to Play

### Starting the Game

```bash
python3 main.py
```

### Game Modes

#### Local Multiplayer
1. Select "LOCAL MULTIPLAYER" from the menu
2. Two players share the same keyboard
3. First to 5 kills wins!

#### Network Multiplayer (LAN)

**Hosting a Game:**
1. Select "HOST NETWORK GAME"
2. Enter your player name
3. Share the displayed IP address with your friend
4. Wait for them to connect
5. Press Enter to start

**Joining a Game:**
1. Select "JOIN BY IP ADDRESS"
2. Enter your player name
3. Enter the host's IP address (e.g., `192.168.1.100`)
4. Wait for host to start the game

### Controls

#### Network Game (Both Players)
| Key | Action |
|-----|--------|
| W / Up Arrow | Move up |
| S / Down Arrow | Move down |
| A / Left Arrow | Move left |
| D / Right Arrow | Move right |
| Space | Shoot |
| E | Place mine |

#### Local Multiplayer

**Player 1:**
| Key | Action |
|-----|--------|
| W / Up Arrow | Move up |
| S / Down Arrow | Move down |
| A / Left Arrow | Move left |
| D / Right Arrow | Move right |
| Space | Shoot |
| E | Place mine |

**Player 2:**
| Key | Action |
|-----|--------|
| I | Move up |
| K | Move down |
| J | Move left |
| L | Move right |
| H | Shoot |

#### General Controls
| Key | Action |
|-----|--------|
| Q | Quit game |
| R | Restart (when game over) |
| B | Go back (in menus) |
| Enter | Confirm selection |

## Gameplay Mechanics

### Combat
- Each tank has **3 HP**
- Getting hit reduces HP by 1
- At 0 HP, the tank respawns at its starting position
- First player to score **5 kills** wins

### Bullet Reflection
Bullets bounce off mirror surfaces:
- **Horizontal mirrors (-)**: Reflect bullets vertically
- **Vertical mirrors (|)**: Reflect bullets horizontally
- **Diagonal mirrors (/ \\)**: Reflect bullets at 45-degree angles
- Bullets can bounce up to **3 times** before disappearing

### Power-ups

| Item | Duration | Effect |
|------|----------|--------|
| Triple Shot | 10 sec | Shoot 3 bullets in a spread pattern |
| Shield | Until hit | Blocks the next damage |
| Speed Boost | 10 sec | 1.5x movement speed |
| Full Vision | 10 sec | See the entire map |
| Mine | 20 sec | Place a trap that damages enemies |

## Project Structure

```
Mini-Project/
├── main.py           # Entry point
├── app.py            # Main application with menu integration
├── game.py           # Core game logic
├── player.py         # Tank/player class
├── bullet.py         # Bullet physics and reflection
├── items.py          # Power-ups and mines
├── map_generator.py  # Procedural map generation
├── menu.py           # Menu system and UI
├── network_tcp.py    # TCP networking for multiplayer
├── network.py        # Legacy UDP networking (unused)
├── constants.py      # Game configuration
├── Docs/
│   ├── DESIGN.md     # Detailed design document
│   └── PROJECT_STRUCTURE.txt
└── README.md         # This file
```

## Technical Details

### Architecture

The game follows a modular architecture:

- **TankTankApp**: Main application controller handling menu and game states
- **GameInstance**: Manages game loop, players, bullets, and items
- **NetworkManager**: Handles TCP connections for LAN multiplayer
- **Menu**: State machine for all menu screens

### Network Protocol

LAN multiplayer uses TCP with JSON messages separated by newlines.

#### Architecture: Host-Authoritative Model

The game uses a **host-authoritative** network model where the host (server) is the source of truth for all game state:

```
┌─────────────────┐                    ┌─────────────────┐
│      HOST       │                    │     CLIENT      │
│   (Player 0)    │                    │   (Player 1)    │
├─────────────────┤                    ├─────────────────┤
│ • Generates map │  ───map_data───►   │ • Receives map  │
│ • Spawns items  │  ──item_spawn──►   │ • Renders items │
│ • Spawns bullets│  ─bullet_spawn─►   │ • Renders bullets│
│ • Calculates    │  ─player_damage►   │ • Updates HP/   │
│   damage/HP     │                    │   kills display │
│ • Detects wins  │  ──game_state──►   │ • Syncs state   │
├─────────────────┤                    ├─────────────────┤
│ • Handles own   │  ◄─player_input─   │ • Sends input   │
│   input locally │                    │   to host       │
└─────────────────┘                    └─────────────────┘
```

#### Message Types

**Lobby Messages:**
```json
// Player join request (client → host)
{"type": "player_join", "player_id": 1, "name": "Player2"}

// Player list update (host → client)
{"type": "player_list", "players": {"0": "Host", "1": "Client"}}

// Game start signal (host → client)
{"type": "start_game", "num_players": 2}
```

**Game State Messages (Host → Client):**
```json
// Initial map data (sent once at game start)
{"type": "map_data", "map": [0,0,1,1,...], "width": 32, "height": 32}

// Periodic full state sync (every ~1 second)
{"type": "game_state", "players": [...], "items": [...], "game_over": false}

// Bullet spawn
{"type": "bullet_spawn", "x": 100, "y": 100, "vx": 2.5, "vy": 0, "owner_id": 0}

// Item spawn
{"type": "item_spawn", "x": 120, "y": 80, "item_type": 1}

// Item pickup
{"type": "item_pickup", "x": 120, "y": 80, "player_id": 0}

// Player damage
{"type": "player_damage", "player_id": 1, "hp": 2, "died": false, "attacker_id": 0}

// Explosion effect
{"type": "explosion", "x": 100, "y": 100}

// Mine placement
{"type": "mine_spawn", "x": 50, "y": 50, "owner_id": 0}
```

**Input Messages (Client → Host, Host → Client for position sync):**
```json
// Player input with position (sent when moving/shooting)
{"type": "player_input", "player_id": 1, "dx": 1, "dy": 0, "shoot": false,
 "place_mine": false, "x": 100.5, "y": 50.0, "direction": 1}

// Position sync (sent periodically when idle)
{"type": "position_sync", "player_id": 1, "x": 100.5, "y": 50.0, "direction": 1}
```

#### Client-Side Interpolation

To ensure smooth movement despite network latency, the client uses **interpolation**:

1. When receiving remote player positions, they are stored as **targets**
2. Each frame, remote players smoothly move toward their target position
3. If the distance is >50 pixels (teleport/respawn), snap immediately
4. Interpolation speed is 0.3 (30% of distance per frame)

```python
# Interpolation logic
distance = sqrt(dx² + dy²)
if distance > 50:
    player.position = target  # Snap for teleports
elif distance > 0.5:
    player.position += (target - position) * 0.3  # Smooth interpolation
```

#### Threading Model

```text
┌──────────────────────────────────────────────────────────┐
│                    Main Thread (Pyxel)                    │
│  • Game loop (update/draw at 30 FPS)                     │
│  • Reads from inbox queue (non-blocking)                 │
│  • Writes to outbox queue (non-blocking)                 │
└──────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   Send Thread       │       │   Receive Thread    │
│ • Polls outbox      │       │ • Polls socket      │
│ • Batches messages  │       │ • Parses JSON       │
│ • Sends via TCP     │       │ • Puts in inbox     │
└─────────────────────┘       └─────────────────────┘
```

#### Optimizations

- **Message Batching**: Up to 5 messages batched per send syscall
- **Conditional Sending**: Only send input when there's actual movement/action
- **Position Sync**: Send position every 15 frames (~0.5s) when idle
- **TCP_NODELAY**: Disabled Nagle's algorithm for lower latency
- **SO_KEEPALIVE**: Connection health monitoring

### Performance

- **Resolution**: 256x256 pixels
- **Frame Rate**: 30 FPS
- **Map Size**: 32x32 tiles
- **Network**: TCP with SO_KEEPALIVE and TCP_NODELAY for low latency

## Troubleshooting

### Game won't start
```bash
# Make sure Pyxel is installed
pip install pyxel

# Try running with Python 3 explicitly
python3 main.py
```

### Network connection fails
- Ensure both players are on the same local network
- Check that port **9999** is not blocked by firewall
- Verify the IP address is entered correctly (numbers and dots only)
- Both players should be able to ping each other

### Controls not working
- Make sure the game window is focused
- For local multiplayer, each player uses their designated keys

### Connection drops during game
- Check your network stability
- Try moving closer to the WiFi router
- Ensure no other applications are using high bandwidth

## Development

### Running Tests

```bash
# Test network connectivity
python3 test_network_tcp.py

# Test menu system
python3 test_menu.py
```

### Quick Start Local Game

```bash
# Skip menu and start local multiplayer directly
python3 main.py --quick-local
```

### File Descriptions

| File | Description |
|------|-------------|
| `main.py` | Entry point, handles CLI arguments |
| `app.py` | Main application with menu/game state management |
| `game.py` | Core game class with update/draw loops |
| `player.py` | Tank class with movement, shooting, HP |
| `bullet.py` | Bullet physics and mirror reflection |
| `items.py` | Power-up items and mine system |
| `map_generator.py` | Procedural map generation |
| `menu.py` | Menu UI and state machine |
| `network_tcp.py` | TCP networking for LAN play |
| `constants.py` | All game configuration values |

## Game Design

### Map Tiles
- **Empty**: Tanks can move through
- **Wall**: Solid obstacle, blocks bullets
- **Mirror (H)**: Reflects bullets vertically
- **Mirror (V)**: Reflects bullets horizontally
- **Mirror (/)**: Reflects bullets diagonally
- **Mirror (\\)**: Reflects bullets diagonally (opposite)

### Spawn Points
- 4 corners of the map are kept clear for spawning
- Players respawn at their original spawn point

### Victory Condition
- First player to reach **5 kills** wins the match
- Press R to restart or B to return to menu

## Credits

- **Game Engine**: [Pyxel](https://github.com/kitao/pyxel) by Takashi Kitao
- **Inspiration**: Battle City (1985), Tank Trouble

## License

This project is created for educational purposes as part of the FIT2 course at Keio University.

---

**Enjoy the game! May the best tank commander win!**
