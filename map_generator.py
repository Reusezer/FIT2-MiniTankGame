import random
import pyxel
from constants import *

class MapGenerator:
    @staticmethod
    def generate():
        """Generate a playable map with walls and mirrors"""
        # Initialize empty map
        game_map = [[TILE_EMPTY for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

        # Add border walls
        for x in range(MAP_WIDTH):
            game_map[0][x] = TILE_WALL
            game_map[MAP_HEIGHT - 1][x] = TILE_WALL

        for y in range(MAP_HEIGHT):
            game_map[y][0] = TILE_WALL
            game_map[y][MAP_WIDTH - 1] = TILE_WALL

        # Add random walls and mirrors
        num_obstacles = 50

        for _ in range(num_obstacles):
            x = random.randint(2, MAP_WIDTH - 3)
            y = random.randint(2, MAP_HEIGHT - 3)

            # Random obstacle type
            obstacle_type = random.choice([
                TILE_WALL,
                TILE_WALL,
                TILE_WALL,  # More walls than mirrors
                TILE_MIRROR_H,
                TILE_MIRROR_V,
                TILE_MIRROR_DIAG_1,
                TILE_MIRROR_DIAG_2
            ])

            # Create small obstacle clusters
            cluster_size = random.randint(1, 3)
            for cx in range(cluster_size):
                for cy in range(cluster_size):
                    nx = x + cx
                    ny = y + cy
                    if 1 < nx < MAP_WIDTH - 1 and 1 < ny < MAP_HEIGHT - 1:
                        game_map[ny][nx] = obstacle_type

        # Ensure spawn points are clear (corners)
        spawn_points = [
            (4, 4), (MAP_WIDTH - 5, 4),
            (4, MAP_HEIGHT - 5), (MAP_WIDTH - 5, MAP_HEIGHT - 5)
        ]

        for sx, sy in spawn_points:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    x = sx + dx
                    y = sy + dy
                    if 0 < x < MAP_WIDTH - 1 and 0 < y < MAP_HEIGHT - 1:
                        game_map[y][x] = TILE_EMPTY

        return game_map

    @staticmethod
    def get_spawn_positions():
        """Get spawn positions in tile coordinates"""
        return [
            (4 * TILE_SIZE + TILE_SIZE // 2, 4 * TILE_SIZE + TILE_SIZE // 2),
            ((MAP_WIDTH - 5) * TILE_SIZE + TILE_SIZE // 2, 4 * TILE_SIZE + TILE_SIZE // 2),
            (4 * TILE_SIZE + TILE_SIZE // 2, (MAP_HEIGHT - 5) * TILE_SIZE + TILE_SIZE // 2),
            ((MAP_WIDTH - 5) * TILE_SIZE + TILE_SIZE // 2, (MAP_HEIGHT - 5) * TILE_SIZE + TILE_SIZE // 2)
        ]

    @staticmethod
    def draw_map(game_map):
        """Draw the map tiles"""
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                tile = game_map[y][x]
                px = x * TILE_SIZE
                py = y * TILE_SIZE

                if tile == TILE_WALL:
                    pyxel.rect(px, py, TILE_SIZE, TILE_SIZE, COLOR_WALL)
                elif tile == TILE_MIRROR_H:
                    pyxel.rect(px, py, TILE_SIZE, TILE_SIZE, COLOR_MIRROR)
                    pyxel.line(px, py + TILE_SIZE // 2, px + TILE_SIZE, py + TILE_SIZE // 2, COLOR_UI)
                elif tile == TILE_MIRROR_V:
                    pyxel.rect(px, py, TILE_SIZE, TILE_SIZE, COLOR_MIRROR)
                    pyxel.line(px + TILE_SIZE // 2, py, px + TILE_SIZE // 2, py + TILE_SIZE, COLOR_UI)
                elif tile == TILE_MIRROR_DIAG_1:
                    pyxel.rect(px, py, TILE_SIZE, TILE_SIZE, COLOR_MIRROR)
                    pyxel.line(px, py, px + TILE_SIZE, py + TILE_SIZE, COLOR_UI)
                elif tile == TILE_MIRROR_DIAG_2:
                    pyxel.rect(px, py, TILE_SIZE, TILE_SIZE, COLOR_MIRROR)
                    pyxel.line(px + TILE_SIZE, py, px, py + TILE_SIZE, COLOR_UI)
