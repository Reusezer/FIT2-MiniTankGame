#!/usr/bin/env python3
"""
Tank Tank - Local Wi-Fi 2D Tank Battle Game

A retro-style tank battle game built with Pyxel.
Play locally or over Wi-Fi with friends!

Controls:
  Menu Navigation:
    - W/S or Up/Down: Navigate menu
    - Space/Enter: Select option
    - ESC: Go back
    - Type your name when prompted

  In-Game:
    Player 1:
      - WASD or Arrow Keys: Move
      - Space: Shoot
      - E: Place mine

    Player 2 (local multiplayer):
      - IJKL: Move
      - H: Shoot

    General:
      - Q: Quit
      - R: Restart (when game over)
      - ESC: Return to menu (when game over)

Usage:
  Standard (with menu):
    python main.py

  Quick start options:
    python main.py --quick-local    (skip menu, start local game)
"""

import sys


def main():
    # Parse command line arguments
    if len(sys.argv) > 1:
        if '--help' in sys.argv or '-h' in sys.argv:
            print(__doc__)
            return
        elif '--quick-local' in sys.argv:
            # Quick start local multiplayer without menu
            from game import Game
            print("Starting Tank Tank - Local Multiplayer")
            print("\nControls:")
            print("  Player 1: WASD/Arrows + Space to shoot")
            print("  Player 2: IJKL + H to shoot")
            print("  Q to quit, R to restart\n")
            Game(num_players=2, use_network=False, is_host=False)
            return
        else:
            print("Unknown argument. Use --help for usage information.")
            return

    # Start app with menu
    from app import TankTankApp
    print("Starting Tank Tank...")
    print("Use the menu to select game mode.\n")
    TankTankApp()


if __name__ == '__main__':
    main()
