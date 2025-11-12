# Game Constants

# Screen settings
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 256
FPS = 30

# Tile settings
TILE_SIZE = 8
MAP_WIDTH = SCREEN_WIDTH // TILE_SIZE  # 32 tiles
MAP_HEIGHT = SCREEN_HEIGHT // TILE_SIZE  # 32 tiles

# Tile types
TILE_EMPTY = 0
TILE_WALL = 1
TILE_MIRROR_H = 2  # Horizontal mirror (reflects vertical)
TILE_MIRROR_V = 3  # Vertical mirror (reflects horizontal)
TILE_MIRROR_DIAG_1 = 4  # Diagonal \ mirror
TILE_MIRROR_DIAG_2 = 5  # Diagonal / mirror

# Player settings
PLAYER_SIZE = 6
PLAYER_SPEED = 1.0
PLAYER_MAX_HP = 3
PLAYER_RESPAWN_TIME = 60  # frames

# Bullet settings
BULLET_SPEED = 2.5
BULLET_SIZE = 2
BULLET_MAX_BOUNCES = 3
BULLET_LIFETIME = 180  # frames (6 seconds at 30fps)

# Item settings
ITEM_SIZE = 6
ITEM_SPAWN_INTERVAL = 300  # frames (10 seconds)
ITEM_DURATION = 300  # frames (10 seconds for timed items)

# Item types
ITEM_TRIPLE_SHOT = 1
ITEM_SHIELD = 2
ITEM_MINE = 3
ITEM_SPEED = 4
ITEM_VISION = 5

# Game settings
WIN_KILLS = 5
VISION_RADIUS = 80  # pixels
VISION_FULL_RADIUS = 200  # with vision item

# Network settings
NETWORK_PORT = 9999
TICK_RATE = 20  # Hz
BROADCAST_INTERVAL = 1.0  # seconds

# Colors (Pyxel 16-color palette)
COLOR_BG = 0  # Black
COLOR_WALL = 5  # Dark gray
COLOR_MIRROR = 12  # Light blue
COLOR_PLAYER_1 = 8  # Red
COLOR_PLAYER_2 = 11  # Blue
COLOR_PLAYER_3 = 3  # Green
COLOR_PLAYER_4 = 9  # Orange
COLOR_BULLET = 7  # White
COLOR_ITEM = 10  # Yellow
COLOR_EXPLOSION = 8  # Red
COLOR_UI = 7  # White
COLOR_TRACK = 13  # Very dark gray
