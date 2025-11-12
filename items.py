import pyxel
import random
import math
from constants import *

class Item:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.type = item_type
        self.active = True
        self.animation_frame = 0

    def update(self):
        self.animation_frame = (self.animation_frame + 1) % 60

    def check_pickup(self, player):
        """Check if player picks up this item"""
        if not self.active or not player.alive:
            return False

        dist = math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2)
        if dist < (PLAYER_SIZE + ITEM_SIZE) / 2:
            player.activate_item(self.type)
            self.active = False
            return True
        return False

    def draw(self):
        if not self.active:
            return

        # Pulsing animation
        pulse = 1 + math.sin(self.animation_frame * 0.2) * 0.2
        size = int(ITEM_SIZE * pulse)

        # Draw item with color based on type
        color = COLOR_ITEM
        if self.type == ITEM_SHIELD:
            color = COLOR_PLAYER_2
        elif self.type == ITEM_MINE:
            color = COLOR_EXPLOSION
        elif self.type == ITEM_SPEED:
            color = COLOR_PLAYER_3
        elif self.type == ITEM_VISION:
            color = COLOR_UI

        pyxel.circ(self.x, self.y, size // 2, color)

        # Draw icon
        if self.type == ITEM_TRIPLE_SHOT:
            # Three dots
            pyxel.pset(self.x - 2, self.y, COLOR_BG)
            pyxel.pset(self.x, self.y, COLOR_BG)
            pyxel.pset(self.x + 2, self.y, COLOR_BG)
        elif self.type == ITEM_SHIELD:
            # Circle outline
            pyxel.circb(self.x, self.y, 2, COLOR_BG)
        elif self.type == ITEM_MINE:
            # X mark
            pyxel.line(self.x - 1, self.y - 1, self.x + 1, self.y + 1, COLOR_BG)
            pyxel.line(self.x + 1, self.y - 1, self.x - 1, self.y + 1, COLOR_BG)
        elif self.type == ITEM_SPEED:
            # Arrow
            pyxel.line(self.x, self.y - 2, self.x, self.y + 2, COLOR_BG)
            pyxel.pset(self.x - 1, self.y - 1, COLOR_BG)
            pyxel.pset(self.x + 1, self.y - 1, COLOR_BG)
        elif self.type == ITEM_VISION:
            # Eye
            pyxel.pset(self.x, self.y, COLOR_BG)


class Mine:
    def __init__(self, x, y, owner_id):
        self.x = x
        self.y = y
        self.owner_id = owner_id
        self.active = True
        self.lifetime = 600  # 20 seconds
        self.trigger_radius = 12

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False

    def check_trigger(self, player):
        """Check if player triggers the mine"""
        if not self.active or not player.alive:
            return False

        # Don't trigger for owner
        if player.id == self.owner_id:
            return False

        dist = math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2)
        if dist < self.trigger_radius:
            self.active = False
            return True
        return False

    def draw(self):
        if not self.active:
            return

        # Draw mine
        pyxel.circ(self.x, self.y, 3, COLOR_EXPLOSION)
        pyxel.circb(self.x, self.y, self.trigger_radius, COLOR_EXPLOSION)

        # Blinking effect
        if pyxel.frame_count % 30 < 15:
            pyxel.pset(self.x, self.y, COLOR_UI)


class ItemSpawner:
    def __init__(self, game_map):
        self.game_map = game_map
        self.spawn_timer = ITEM_SPAWN_INTERVAL
        self.items = []

    def update(self, players):
        self.spawn_timer -= 1

        # Update existing items
        for item in self.items:
            item.update()

            # Check pickup
            for player in players:
                if item.check_pickup(player):
                    break

        # Remove inactive items
        self.items = [item for item in self.items if item.active]

        # Spawn new item
        if self.spawn_timer <= 0 and len(self.items) < 3:
            self._spawn_item()
            self.spawn_timer = ITEM_SPAWN_INTERVAL

    def _spawn_item(self):
        """Spawn a random item at a random location"""
        # Find empty location
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(2, MAP_WIDTH - 3) * TILE_SIZE + TILE_SIZE // 2
            y = random.randint(2, MAP_HEIGHT - 3) * TILE_SIZE + TILE_SIZE // 2

            tile_x = int(x // TILE_SIZE)
            tile_y = int(y // TILE_SIZE)

            if self.game_map[tile_y][tile_x] == TILE_EMPTY:
                item_type = random.choice([
                    ITEM_TRIPLE_SHOT,
                    ITEM_SHIELD,
                    ITEM_SPEED,
                    ITEM_VISION
                ])
                self.items.append(Item(x, y, item_type))
                break

    def draw(self):
        for item in self.items:
            item.draw()
