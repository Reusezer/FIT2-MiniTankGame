"""
Constants Module - ゲーム定数

All game configuration values are defined here.
全てのゲーム設定値がここで定義されている。

This file is imported by all other modules using:
    from constants import *

このファイルは他の全てのモジュールでインポートされる。
"""

# =============================================================================
# SCREEN SETTINGS - 画面設定
# =============================================================================

SCREEN_WIDTH = 256   # Screen width in pixels - 画面の幅（ピクセル）
SCREEN_HEIGHT = 256  # Screen height in pixels - 画面の高さ（ピクセル）
FPS = 30             # Frames per second - 1秒あたりのフレーム数

# =============================================================================
# TILE SETTINGS - タイル設定
# =============================================================================

TILE_SIZE = 8                           # Size of each tile in pixels - タイルサイズ（ピクセル）
MAP_WIDTH = SCREEN_WIDTH // TILE_SIZE   # Map width in tiles (256/8 = 32) - マップの幅（タイル数）
MAP_HEIGHT = SCREEN_HEIGHT // TILE_SIZE # Map height in tiles (256/8 = 32) - マップの高さ（タイル数）

# =============================================================================
# TILE TYPES - タイルの種類
# These values are stored in the game_map 2D array
# これらの値はgame_mapの2次元配列に格納される
# =============================================================================

TILE_EMPTY = 0        # Empty space - tanks can pass through - 空きスペース（通過可能）
TILE_WALL = 1         # Solid wall - blocks everything - 壁（全てブロック）
TILE_MIRROR_H = 2     # Horizontal mirror (-) - reflects vertical velocity - 水平ミラー（垂直速度を反射）
TILE_MIRROR_V = 3     # Vertical mirror (|) - reflects horizontal velocity - 垂直ミラー（水平速度を反射）
TILE_MIRROR_DIAG_1 = 4  # Diagonal mirror (\) - swaps velocity - 対角線ミラー
TILE_MIRROR_DIAG_2 = 5  # Diagonal mirror (/) - swaps and negates velocity - 対角線ミラー

# =============================================================================
# PLAYER SETTINGS - プレイヤー設定
# =============================================================================

PLAYER_SIZE = 6         # Tank size in pixels - 戦車のサイズ（ピクセル）
PLAYER_SPEED = 1.0      # Base movement speed (pixels per frame) - 基本移動速度
PLAYER_MAX_HP = 3       # Maximum health points - 最大HP
PLAYER_RESPAWN_TIME = 60  # Frames until respawn (60 frames = 2 seconds) - リスポーン時間（フレーム）

# =============================================================================
# BULLET SETTINGS - 弾丸設定
# =============================================================================

BULLET_SPEED = 2.5       # Bullet speed (pixels per frame) - 弾速
BULLET_SIZE = 2          # Bullet radius in pixels - 弾のサイズ（ピクセル）
BULLET_MAX_BOUNCES = 3   # Max reflections before despawn - 最大反射回数
BULLET_LIFETIME = 180    # Frames until despawn (180 frames = 6 seconds) - 生存時間

# =============================================================================
# ITEM SETTINGS - アイテム設定
# =============================================================================

ITEM_SIZE = 6              # Item size in pixels - アイテムサイズ（ピクセル）
ITEM_SPAWN_INTERVAL = 300  # Frames between spawns (300 = 10 seconds) - スポーン間隔
ITEM_DURATION = 300        # Effect duration in frames (300 = 10 seconds) - 効果持続時間

# =============================================================================
# ITEM TYPES - アイテムの種類
# These values identify different power-ups
# これらの値は異なるパワーアップを識別する
# =============================================================================

ITEM_TRIPLE_SHOT = 1  # Shoot 3 bullets at once - 3発同時発射
ITEM_SHIELD = 2       # Block next damage - 次のダメージを無効化
ITEM_MINE = 3         # Place explosive trap - 地雷を設置
ITEM_SPEED = 4        # 1.5x movement speed - 移動速度1.5倍
ITEM_VISION = 5       # Full map visibility - マップ全体が見える

# =============================================================================
# GAME SETTINGS - ゲーム設定
# =============================================================================

WIN_KILLS = 5              # Kills needed to win - 勝利に必要なキル数
MINE_LIMIT = 5             # Max mines per player per game - プレイヤー毎の地雷上限
VISION_RADIUS = 80         # Normal vision radius in pixels - 通常の視界半径
VISION_FULL_RADIUS = 200   # Vision radius with power-up - パワーアップ時の視界半径

# =============================================================================
# NETWORK SETTINGS - ネットワーク設定
# =============================================================================

NETWORK_PORT = 9999       # TCP port for network play - ネットワーク接続ポート
TICK_RATE = 20            # Network updates per second - 1秒あたりのネットワーク更新回数
BROADCAST_INTERVAL = 1.0  # Seconds between full state syncs - 全状態同期の間隔（秒）

# =============================================================================
# COLOR CONSTANTS - 色定数
# Pyxel uses a 16-color palette (0-15)
# Pyxelは16色パレットを使用（0-15）
# =============================================================================

COLOR_BG = 0         # Background color (black) - 背景色（黒）
COLOR_WALL = 5       # Wall color (dark gray) - 壁の色（濃い灰色）
COLOR_MIRROR = 12    # Mirror color (light blue) - ミラーの色（水色）
COLOR_PLAYER_1 = 8   # Player 1 color (red) - プレイヤー1の色（赤）
COLOR_PLAYER_2 = 11  # Player 2 color (blue) - プレイヤー2の色（青）
COLOR_PLAYER_3 = 3   # Player 3 color (green) - プレイヤー3の色（緑）
COLOR_PLAYER_4 = 9   # Player 4 color (orange) - プレイヤー4の色（橙）
COLOR_BULLET = 7     # Bullet color (white) - 弾の色（白）
COLOR_ITEM = 10      # Item color (yellow) - アイテムの色（黄）
COLOR_EXPLOSION = 8  # Explosion color (red) - 爆発の色（赤）
COLOR_UI = 7         # UI text color (white) - UIの色（白）
COLOR_TRACK = 13     # Tank track trail color (dark gray) - キャタピラ跡の色（暗灰）
