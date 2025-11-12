import pyxel
import math
from constants import *

class Bullet:
    def __init__(self, x, y, vx, vy, owner_id):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.owner_id = owner_id
        self.bounces = 0
        self.lifetime = BULLET_LIFETIME
        self.active = True

    def update(self, game_map):
        if not self.active:
            return

        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False
            return

        # Move bullet
        new_x = self.x + self.vx
        new_y = self.y + self.vy

        # Check boundaries
        if new_x < 0 or new_x >= SCREEN_WIDTH or new_y < 0 or new_y >= SCREEN_HEIGHT:
            self.active = False
            return

        # Check tile collision
        tile_x = int(new_x // TILE_SIZE)
        tile_y = int(new_y // TILE_SIZE)

        if 0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT:
            tile = game_map[tile_y][tile_x]

            if tile == TILE_WALL:
                # Hit solid wall
                self.active = False
                return
            elif tile >= TILE_MIRROR_H:
                # Hit mirror, reflect
                self._reflect(tile)
                self.bounces += 1
                if self.bounces >= BULLET_MAX_BOUNCES:
                    self.active = False
                    return

        self.x = new_x
        self.y = new_y

    def _reflect(self, tile_type):
        """Reflect bullet based on mirror type"""
        if tile_type == TILE_MIRROR_H:
            # Horizontal mirror - reflects vertical velocity
            self.vy = -self.vy
        elif tile_type == TILE_MIRROR_V:
            # Vertical mirror - reflects horizontal velocity
            self.vx = -self.vx
        elif tile_type == TILE_MIRROR_DIAG_1:
            # Diagonal \ mirror - swap and negate
            self.vx, self.vy = self.vy, self.vx
        elif tile_type == TILE_MIRROR_DIAG_2:
            # Diagonal / mirror - swap and negate both
            self.vx, self.vy = -self.vy, -self.vx

    def check_player_collision(self, player):
        """Check if bullet hits a player"""
        if not self.active or not player.alive:
            return False

        # Don't hit owner
        if self.owner_id == player.id:
            return False

        # Simple circle collision
        dist = math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2)
        return dist < (PLAYER_SIZE // 2 + BULLET_SIZE)

    def draw(self):
        if self.active:
            pyxel.circ(self.x, self.y, BULLET_SIZE, COLOR_BULLET)
            # Draw trail
            trail_x = self.x - self.vx * 0.5
            trail_y = self.y - self.vy * 0.5
            pyxel.line(self.x, self.y, trail_x, trail_y, COLOR_UI)
