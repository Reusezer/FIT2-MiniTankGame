# Tank Tank

A retro-style 2D tank battle game built with Python and Pyxel. Battle your friends locally or over LAN in intense tank combat with reflective bullets, power-ups, and strategic gameplay.

## Features

- **Local Multiplayer**: 2 players on the same device
- **LAN Multiplayer**: Play over local network with direct IP connection
- **Reflective Bullets**: Bullets bounce off mirror surfaces for strategic shots
- **Power-ups**: Triple shot, shield, speed boost, full vision, and mines
- **Procedurally Generated Maps**: Every game has a unique battlefield
- **Retro Pixel Art**: Classic 16-color aesthetic

## Installation

```bash
# Install Pyxel
pip install pyxel

# Run the game
python main.py
```

## How to Play

### Controls

**Player 1 (or Network):**
| Key | Action |
|-----|--------|
| W / Up | Move up |
| S / Down | Move down |
| A / Left | Move left |
| D / Right | Move right |
| Space | Shoot |
| E | Place mine |

**Player 2 (Local only):**
| Key | Action |
|-----|--------|
| I | Move up |
| K | Move down |
| J | Move left |
| L | Move right |
| H | Shoot |

**General:**
| Key | Action |
|-----|--------|
| Q | Quit |
| R | Restart (game over) |
| ESC | Return to menu |

---

## File Structure and Descriptions

```
Mini-Project/
├── main.py            # Entry point - starts the game
├── app.py             # Main application (TankTankApp + GameInstance)
├── player.py          # Player/tank class
├── bullet.py          # Bullet physics and reflection
├── items.py           # Items, mines, and spawner
├── map_generator.py   # Random map generation
├── menu.py            # Menu UI and state machine
├── network_tcp.py     # TCP networking for LAN play
├── constants.py       # All game constants
└── Docs/              # Documentation
```

---

## Detailed File Descriptions

### main.py (Entry Point)
**Purpose:** Start the game application.

```python
from app import TankTankApp

def main():
    TankTankApp()  # Creates window and starts game loop

if __name__ == '__main__':
    main()
```

**Flow:** `main.py` → `TankTankApp` → `Menu` or `GameInstance`

---

### app.py (Main Application)
**Purpose:** Manages the overall game state (menu vs game) and handles network integration.

**Contains 2 classes:**

#### TankTankApp
- Initializes Pyxel window (256x256, 30 FPS)
- Creates Menu object
- Handles transitions between menu and game
- Manages NetworkManager lifecycle

#### GameInstance
- Created when a game starts (local or network)
- Contains all game objects: players, bullets, mines, items
- Handles game loop: update() and draw()
- **Network sync methods** (Host sends to Client):
  - `_send_game_state()` - periodic full sync
  - `_send_bullet_spawn()` - when bullets are created
  - `_send_item_pickup()` - when items are collected
  - `_send_player_damage()` - when damage occurs

---

### player.py (Player/Tank Class)
**Purpose:** Represents a tank with movement, shooting, HP, and power-ups.

**Key Variables:**
| Variable | Type | Description |
|----------|------|-------------|
| x, y | float | Position |
| direction | int | 0=up, 1=right, 2=down, 3=left |
| hp | int | Health points (max 3) |
| kills | int | Kill count (5 to win) |
| has_shield | bool | Shield active |
| has_triple_shot | bool | Triple shot active |
| has_speed_boost | bool | Speed boost active |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `move(dx, dy, map)` | Move tank with collision detection |
| `shoot()` | Create bullet(s), returns list |
| `take_damage()` | Reduce HP, returns True if died |
| `activate_item(type)` | Activate power-up effect |
| `draw()` | Draw tank and effects |

---

### bullet.py (Bullet Class)
**Purpose:** Handles bullet movement and mirror reflection.

**Key Variables:**
| Variable | Type | Description |
|----------|------|-------------|
| x, y | float | Position |
| vx, vy | float | Velocity vector |
| owner_id | int | Who shot this bullet |
| bounces | int | Reflection count (max 3) |
| active | bool | Still alive |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `update(map)` | Move and check collisions |
| `_reflect(tile)` | Calculate reflection angle |
| `check_player_collision(player)` | Hit detection |

**Reflection Logic:**
```
Wall         → Bullet destroyed
Mirror (-)   → vy = -vy (vertical flip)
Mirror (|)   → vx = -vx (horizontal flip)
Mirror (/)   → swap and negate vx, vy
Mirror (\)   → swap vx, vy
```

---

### items.py (Items and Mines)
**Purpose:** Power-up items and mine traps.

**Contains 3 classes:**

#### Item
- Power-up that spawns on the map
- Pulse animation
- Types: TRIPLE_SHOT, SHIELD, SPEED, VISION

#### Mine
- Trap placed by players
- Triggers on enemy proximity (12 pixels)
- Lasts 20 seconds

#### ItemSpawner
- Manages item spawning (every 10 seconds)
- Maximum 3 items at once
- Spawns on empty tiles only

---

### map_generator.py (Map Generation)
**Purpose:** Creates random playable maps.

**Generation Algorithm:**
1. Create empty 32x32 grid
2. Add border walls
3. Place 50 random obstacles (walls or mirrors)
4. Clear spawn areas in 4 corners

**Tile Types:**
| Value | Name | Description |
|-------|------|-------------|
| 0 | EMPTY | Passable |
| 1 | WALL | Blocks all |
| 2 | MIRROR_H | Horizontal mirror |
| 3 | MIRROR_V | Vertical mirror |
| 4 | MIRROR_DIAG_1 | Diagonal \ |
| 5 | MIRROR_DIAG_2 | Diagonal / |

---

### menu.py (Menu System)
**Purpose:** Handles all menu screens and user input.

**Menu States:**
| State | Description |
|-------|-------------|
| MAIN_MENU | Main menu with 4 options |
| ENTER_NAME | Player name input |
| ENTER_IP | Host IP input (client) |
| NETWORK_SETUP | Initializing network |
| CONNECTING | Waiting for connection |
| LOBBY | Waiting for players/start |

**Flow:**
```
MAIN_MENU
  ├── LOCAL MULTIPLAYER → Start game
  ├── HOST NETWORK GAME → ENTER_NAME → LOBBY → Start
  ├── JOIN BY IP → ENTER_IP → ENTER_NAME → CONNECTING → LOBBY
  └── QUIT
```

---

### network_tcp.py (Network Module)
**Purpose:** TCP-based networking for LAN multiplayer.

**Contains 2 classes:**

#### NetworkPeer (Low-Level)
Handles raw TCP socket communication with threading.

**Architecture:**
```
┌─────────────────────────────────────────┐
│           Main Thread (Pyxel)            │
│  • Calls send() - adds to outbox queue  │
│  • Calls recv_all() - reads inbox queue │
└─────────────────────────────────────────┘
              │                │
              ▼                ▼
     ┌──────────────┐  ┌──────────────┐
     │ Send Thread  │  │ Recv Thread  │
     │ • Gets from  │  │ • Reads TCP  │
     │   outbox     │  │ • Parses JSON│
     │ • Sends TCP  │  │ • Puts inbox │
     └──────────────┘  └──────────────┘
```

**Key Methods:**
| Method | Thread | Description |
|--------|--------|-------------|
| `send(dict)` | Main | Queue message for sending |
| `recv_all()` | Main | Get all received messages |
| `is_connected()` | Main | Check connection status |
| `_send_loop()` | Send | Background TCP sending |
| `_recv_loop()` | Recv | Background TCP receiving |

#### NetworkManager (High-Level)
Game-specific networking logic.

**Responsibilities:**
- Manage player names and lobby
- Track connection state
- Handle game start signal
- Share map data between host and client

**Message Types:**
```json
// Lobby
{"type": "player_join", "player_id": 1, "name": "Player2"}
{"type": "player_list", "players": {...}}
{"type": "start_game", "map": [...], "map_width": 32, "map_height": 32}

// Game (handled by GameInstance)
{"type": "player_input", "dx": 1, "dy": 0, "x": 100, "y": 50}
{"type": "game_state", "players": [...], "items": [...]}
{"type": "bullet_spawn", "x": 100, "y": 50, "vx": 2.5, "vy": 0}
```

---

### constants.py (Configuration)
**Purpose:** All game constants in one place.

**Screen:**
- `SCREEN_WIDTH = 256`
- `SCREEN_HEIGHT = 256`
- `FPS = 30`

**Map:**
- `TILE_SIZE = 8`
- `MAP_WIDTH = 32`
- `MAP_HEIGHT = 32`

**Player:**
- `PLAYER_SIZE = 6`
- `PLAYER_SPEED = 1.0`
- `PLAYER_MAX_HP = 3`
- `WIN_KILLS = 5`

**Bullet:**
- `BULLET_SPEED = 2.5`
- `BULLET_MAX_BOUNCES = 3`

**Network:**
- `NETWORK_PORT = 9999`

---

## Network Architecture

### Host-Authoritative Model

The **host** is the source of truth for all game state:

```
HOST (Player 0)                    CLIENT (Player 1)
─────────────────                  ─────────────────
• Generates map      ──────►       • Receives map
• Spawns items       ──────►       • Displays items
• Calculates damage  ──────►       • Updates HP display
• Detects collisions ──────►       • Shows explosions
• Sends full state   ──────►       • Syncs everything

• Processes input    ◄──────       • Sends input only
```

### Why Threading?

Pyxel runs at 30 FPS in a single thread. Network I/O could block and cause lag.

**Solution:** Use background threads for networking:
- Main thread never waits for network
- Queues provide thread-safe communication
- Messages are batched for efficiency

---

## Troubleshooting

### Connection Issues
- Both players must be on the same LAN
- Port 9999 must not be blocked by firewall
- Verify IP address is correct (use `ifconfig` or `ipconfig`)

### Game Lag
- Both computers should be close to the router
- Close bandwidth-heavy applications

---

## License

Educational project for FIT2 course at Keio University.
