"""
Bullet Module - 弾丸クラス

This module handles bullet physics including movement and mirror reflection.
弾丸の移動とミラー反射を処理するモジュール。
"""

# =============================================================================
# IMPORTS - インポート
# =============================================================================

import pyxel  # Pyxel game engine - ゲームエンジン（描画に使用）
import math   # Math functions - 数学関数（sqrt で距離計算に使用）

# Import all constants from constants.py
# constants.py から全ての定数をインポート
# - TILE_SIZE: タイルのサイズ（8ピクセル）
# - MAP_WIDTH, MAP_HEIGHT: マップの幅と高さ（32タイル）
# - SCREEN_WIDTH, SCREEN_HEIGHT: 画面サイズ（256ピクセル）
# - TILE_WALL, TILE_MIRROR_H, etc.: タイルの種類
# - BULLET_LIFETIME: 弾の生存時間（180フレーム = 6秒）
# - BULLET_MAX_BOUNCES: 最大反射回数（3回）
# - BULLET_SIZE: 弾のサイズ（2ピクセル）
# - PLAYER_SIZE: プレイヤーサイズ（当たり判定に使用）
# - COLOR_BULLET, COLOR_UI: 描画色
from constants import *


# =============================================================================
# BULLET CLASS - 弾丸クラス
# =============================================================================

class Bullet:
    """
    Bullet class - handles movement, reflection, and collision.
    弾丸クラス - 移動、反射、衝突判定を処理。

    弾丸はプレイヤーが発射し、壁に当たると消滅、ミラーに当たると反射する。
    最大3回まで反射可能。6秒経過すると自動的に消滅。
    """

    def __init__(self, x, y, vx, vy, owner_id):
        """
        Initialize bullet at position with velocity.
        弾丸を初期位置と速度で初期化。

        Args:
            x (float): Initial X position - 初期X座標
            y (float): Initial Y position - 初期Y座標
            vx (float): X velocity (speed in X direction) - X方向の速度
            vy (float): Y velocity (speed in Y direction) - Y方向の速度
            owner_id (int): Player ID who shot this bullet - 発射したプレイヤーのID
        """
        # =================================================================
        # POSITION VARIABLES - 位置変数
        # =================================================================
        self.x = x  # Current X position - 現在のX座標
        self.y = y  # Current Y position - 現在のY座標

        # =================================================================
        # VELOCITY VARIABLES - 速度変数
        # =================================================================
        self.vx = vx  # X velocity (pixels per frame) - X方向の速度（フレームあたりピクセル）
        self.vy = vy  # Y velocity (pixels per frame) - Y方向の速度（フレームあたりピクセル）

        # =================================================================
        # STATE VARIABLES - 状態変数
        # =================================================================
        self.owner_id = owner_id  # Who shot this (0 or 1) - 誰が撃ったか（自分には当たらない）
        self.bounces = 0          # How many times reflected - 反射した回数
        self.lifetime = BULLET_LIFETIME  # Frames until despawn (180) - 消滅までのフレーム数
        self.active = True        # Is bullet still alive - 弾が生きているか

    def update(self, game_map):
        """
        Update bullet position and check collisions.
        弾丸の位置を更新し、衝突をチェック。

        Called every frame (30 times per second).
        毎フレーム呼ばれる（1秒に30回）。

        Args:
            game_map (list[list[int]]): 2D array of tile types - タイルの2次元配列
        """
        # Skip if bullet is already dead
        # 弾が既に死んでいたらスキップ
        if not self.active:
            return

        # Decrease lifetime counter
        # 生存時間を減らす
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False  # Bullet expires - 弾が期限切れ
            return

        # =================================================================
        # MOVEMENT - 移動処理
        # =================================================================
        # Calculate new position
        # 新しい位置を計算
        new_x = self.x + self.vx
        new_y = self.y + self.vy

        # =================================================================
        # BOUNDARY CHECK - 境界チェック
        # =================================================================
        # Check if bullet left the screen
        # 弾が画面外に出たかチェック
        if new_x < 0 or new_x >= SCREEN_WIDTH or new_y < 0 or new_y >= SCREEN_HEIGHT:
            self.active = False  # Bullet dies at screen edge - 画面端で消滅
            return

        # =================================================================
        # TILE COLLISION - タイル衝突判定
        # =================================================================
        # Convert pixel position to tile coordinates
        # ピクセル座標をタイル座標に変換
        tile_x = int(new_x // TILE_SIZE)  # Divide by 8 to get tile X - 8で割ってタイルX取得
        tile_y = int(new_y // TILE_SIZE)  # Divide by 8 to get tile Y - 8で割ってタイルY取得

        # Check if tile is within map bounds
        # タイルがマップ内かチェック
        if 0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT:
            tile = game_map[tile_y][tile_x]  # Get tile type - タイルの種類を取得

            if tile == TILE_WALL:
                # Hit solid wall - bullet dies
                # 壁に当たった - 弾は消滅
                self.active = False
                return

            elif tile >= TILE_MIRROR_H:
                # Hit a mirror - reflect the bullet
                # ミラーに当たった - 弾を反射
                self._reflect(tile)
                self.bounces += 1

                # Check if max bounces reached
                # 最大反射回数に達したかチェック
                if self.bounces >= BULLET_MAX_BOUNCES:
                    self.active = False  # Too many bounces - 反射しすぎ
                    return

        # Apply new position
        # 新しい位置を適用
        self.x = new_x
        self.y = new_y

    def _reflect(self, tile_type):
        """
        Reflect bullet based on mirror type.
        ミラーの種類に応じて弾を反射。

        Different mirrors reflect bullets in different ways:
        異なるミラーは異なる方法で弾を反射する：

        - MIRROR_H (-): Flips vertical velocity (vy = -vy)
          水平ミラー：垂直速度を反転

        - MIRROR_V (|): Flips horizontal velocity (vx = -vx)
          垂直ミラー：水平速度を反転

        - MIRROR_DIAG_1 (\): Swaps vx and vy
          対角線ミラー1：vxとvyを交換

        - MIRROR_DIAG_2 (/): Swaps and negates vx and vy
          対角線ミラー2：vxとvyを交換して反転

        Args:
            tile_type (int): Type of mirror tile - ミラータイルの種類
        """
        if tile_type == TILE_MIRROR_H:
            # Horizontal mirror (─) - reflects vertical component
            # 水平ミラー - 垂直成分を反射
            # Example: Bullet going down bounces up
            # 例：下に行く弾が上に跳ね返る
            self.vy = -self.vy

        elif tile_type == TILE_MIRROR_V:
            # Vertical mirror (│) - reflects horizontal component
            # 垂直ミラー - 水平成分を反射
            # Example: Bullet going right bounces left
            # 例：右に行く弾が左に跳ね返る
            self.vx = -self.vx

        elif tile_type == TILE_MIRROR_DIAG_1:
            # Diagonal mirror (\) - swaps velocity components
            # 対角線ミラー - 速度成分を交換
            # Example: Bullet going right becomes going down
            # 例：右に行く弾が下に行く
            self.vx, self.vy = self.vy, self.vx

        elif tile_type == TILE_MIRROR_DIAG_2:
            # Diagonal mirror (/) - swaps and negates
            # 対角線ミラー - 交換して反転
            # Example: Bullet going right becomes going up
            # 例：右に行く弾が上に行く
            self.vx, self.vy = -self.vy, -self.vx

    def check_player_collision(self, player):
        """
        Check if bullet hits a player.
        弾がプレイヤーに当たったかチェック。

        Uses circle collision detection (distance between centers).
        円形の衝突判定を使用（中心間の距離）。

        Args:
            player (Player): Player to check collision with - 衝突チェック対象のプレイヤー

        Returns:
            bool: True if collision detected - 衝突したらTrue
        """
        # Skip if bullet is dead or player is dead
        # 弾が死んでいるかプレイヤーが死んでいたらスキップ
        if not self.active or not player.alive:
            return False

        # Don't hit the player who shot this bullet (friendly fire off)
        # 撃った本人には当たらない（フレンドリーファイアなし）
        if self.owner_id == player.id:
            return False

        # =================================================================
        # CIRCLE COLLISION DETECTION - 円形衝突判定
        # =================================================================
        # Calculate distance between bullet and player centers
        # 弾とプレイヤーの中心間の距離を計算
        dx = self.x - player.x  # X difference - X差分
        dy = self.y - player.y  # Y difference - Y差分
        dist = math.sqrt(dx ** 2 + dy ** 2)  # Pythagorean theorem - ピタゴラスの定理

        # Collision if distance < sum of radii
        # 距離が半径の合計より小さければ衝突
        collision_radius = PLAYER_SIZE // 2 + BULLET_SIZE  # 3 + 2 = 5 pixels
        return dist < collision_radius

    def draw(self):
        """
        Draw the bullet on screen.
        画面に弾を描画。

        Draws:
        - A white circle for the bullet
        - A short line trail behind it

        描画内容：
        - 弾本体（白い円）
        - 後ろに短い軌跡線
        """
        if self.active:
            # Draw bullet as circle
            # 弾を円として描画
            pyxel.circ(self.x, self.y, BULLET_SIZE, COLOR_BULLET)

            # Draw trail (short line behind bullet)
            # 軌跡を描画（弾の後ろに短い線）
            trail_x = self.x - self.vx * 0.5  # Half a frame behind - 0.5フレーム後ろ
            trail_y = self.y - self.vy * 0.5
            pyxel.line(self.x, self.y, trail_x, trail_y, COLOR_UI)
