import pyxel
import math
from constants import *

class Player:
    def __init__(self, player_id, x, y, color):
        self.id = player_id
        self.x = x
        self.y = y
        self.color = color
        self.direction = 0  # 0=up, 1=right, 2=down, 3=left
        self.hp = PLAYER_MAX_HP
        self.speed = PLAYER_SPEED
        self.kills = 0
        self.alive = True
        self.respawn_timer = 0

        # Active items
        self.has_triple_shot = False
        self.has_shield = False
        self.has_speed_boost = False
        self.has_full_vision = False
        self.triple_shot_timer = 0
        self.speed_boost_timer = 0
        self.full_vision_timer = 0

        # Track trail
        self.track_trail = []
        self.track_cooldown = 0

        # Shooting cooldown
        self.shoot_cooldown = 0

        # Mine limit
        self.mines_remaining = MINE_LIMIT

    def update(self, game_map):
        # Handle respawn
        if not self.alive:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawn()
            return

        # Update timers
        if self.triple_shot_timer > 0:
            self.triple_shot_timer -= 1
            if self.triple_shot_timer <= 0:
                self.has_triple_shot = False

        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.has_speed_boost = False
                self.speed = PLAYER_SPEED

        if self.full_vision_timer > 0:
            self.full_vision_timer -= 1
            if self.full_vision_timer <= 0:
                self.has_full_vision = False

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.track_cooldown > 0:
            self.track_cooldown -= 1

        # Decay track trail
        self.track_trail = [(tx, ty, alpha - 1) for tx, ty, alpha in self.track_trail if alpha > 1]

    def move(self, dx, dy, game_map):
        if not self.alive:
            return

        # Determine direction
        if dx < 0:
            self.direction = 3  # left
        elif dx > 0:
            self.direction = 1  # right
        elif dy < 0:
            self.direction = 0  # up
        elif dy > 0:
            self.direction = 2  # down

        # Apply speed
        current_speed = self.speed * (1.5 if self.has_speed_boost else 1.0)
        new_x = self.x + dx * current_speed
        new_y = self.y + dy * current_speed

        # Check collision with walls
        if not self._check_collision(new_x, new_y, game_map):
            self.x = new_x
            self.y = new_y

            # Add track trail
            if self.track_cooldown <= 0:
                self.track_trail.append((int(self.x), int(self.y), 30))
                self.track_cooldown = 3

    def _check_collision(self, x, y, game_map):
        # Check all corners of the player
        half_size = PLAYER_SIZE // 2
        corners = [
            (x - half_size, y - half_size),
            (x + half_size, y - half_size),
            (x - half_size, y + half_size),
            (x + half_size, y + half_size)
        ]

        for cx, cy in corners:
            tile_x = int(cx // TILE_SIZE)
            tile_y = int(cy // TILE_SIZE)

            if 0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT:
                tile = game_map[tile_y][tile_x]
                if tile == TILE_WALL or tile >= TILE_MIRROR_H:
                    return True
        return False

    def shoot(self):
        if not self.alive or self.shoot_cooldown > 0:
            return []

        from bullet import Bullet
        bullets = []

        # Calculate bullet spawn position (in front of tank)
        offset = PLAYER_SIZE
        spawn_x = self.x
        spawn_y = self.y

        if self.direction == 0:  # up
            spawn_y -= offset
        elif self.direction == 1:  # right
            spawn_x += offset
        elif self.direction == 2:  # down
            spawn_y += offset
        elif self.direction == 3:  # left
            spawn_x -= offset

        if self.has_triple_shot:
            # Three bullets in a spread
            angles = [-15, 0, 15]  # degrees relative to direction
            for angle_offset in angles:
                bullet = self._create_bullet(spawn_x, spawn_y, angle_offset)
                bullets.append(bullet)
        else:
            # Single bullet
            bullet = self._create_bullet(spawn_x, spawn_y, 0)
            bullets.append(bullet)

        self.shoot_cooldown = 20  # ~0.67 seconds
        return bullets

    def _create_bullet(self, x, y, angle_offset):
        from bullet import Bullet

        # Base angle from direction
        base_angle = self.direction * 90
        angle = base_angle + angle_offset

        # Convert to radians
        rad = math.radians(angle)
        vx = math.sin(rad) * BULLET_SPEED
        vy = -math.cos(rad) * BULLET_SPEED

        return Bullet(x, y, vx, vy, self.id)

    def take_damage(self):
        if not self.alive:
            return False

        if self.has_shield:
            self.has_shield = False
            return False

        self.hp -= 1
        if self.hp <= 0:
            self.die()
            return True
        return False

    def die(self):
        self.alive = False
        self.hp = 0
        self.respawn_timer = PLAYER_RESPAWN_TIME

    def respawn(self):
        self.alive = True
        self.hp = PLAYER_MAX_HP
        self.has_triple_shot = False
        self.has_shield = False
        self.has_speed_boost = False
        self.has_full_vision = False
        self.speed = PLAYER_SPEED
        # Position is set by game logic

    def activate_item(self, item_type):
        if item_type == ITEM_TRIPLE_SHOT:
            self.has_triple_shot = True
            self.triple_shot_timer = ITEM_DURATION
        elif item_type == ITEM_SHIELD:
            self.has_shield = True
        elif item_type == ITEM_SPEED:
            self.has_speed_boost = True
            self.speed_boost_timer = ITEM_DURATION
            self.speed = PLAYER_SPEED * 1.5
        elif item_type == ITEM_VISION:
            self.has_full_vision = True
            self.full_vision_timer = ITEM_DURATION

    def draw(self):
        # Draw track trail first
        for tx, ty, alpha in self.track_trail:
            intensity = min(15, max(0, int(alpha / 2)))
            pyxel.pset(tx, ty, COLOR_TRACK if intensity > 0 else COLOR_BG)

        if not self.alive:
            return

        # Draw tank body (rectangle)
        half_size = PLAYER_SIZE // 2
        pyxel.rect(
            self.x - half_size,
            self.y - half_size,
            PLAYER_SIZE,
            PLAYER_SIZE,
            self.color
        )

        # Draw barrel direction indicator
        barrel_length = 4
        barrel_x = self.x
        barrel_y = self.y

        if self.direction == 0:  # up
            barrel_y -= barrel_length
        elif self.direction == 1:  # right
            barrel_x += barrel_length
        elif self.direction == 2:  # down
            barrel_y += barrel_length
        elif self.direction == 3:  # left
            barrel_x -= barrel_length

        pyxel.line(self.x, self.y, barrel_x, barrel_y, COLOR_UI)

        # Draw HP indicator
        for i in range(self.hp):
            pyxel.pset(self.x - half_size + i * 2, self.y - half_size - 2, COLOR_UI)

        # Draw item indicators
        if self.has_shield:
            pyxel.circ(self.x, self.y, PLAYER_SIZE, COLOR_PLAYER_2)

        if self.has_triple_shot:
            pyxel.pset(self.x - 2, self.y + half_size + 2, COLOR_ITEM)
            pyxel.pset(self.x, self.y + half_size + 2, COLOR_ITEM)
            pyxel.pset(self.x + 2, self.y + half_size + 2, COLOR_ITEM)
