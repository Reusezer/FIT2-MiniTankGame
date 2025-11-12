# Quick Start Guide - Tank Tank

## Installation

### 1. Install Python 3.8 or higher
Make sure you have Python 3.8+ installed on your system.

### 2. Install Pyxel
```bash
pip install pyxel
# or
pip3 install pyxel
```

### 3. Navigate to the game directory
```bash
cd Mini-Project
```

## Running the Game

### With Interactive Menu (Recommended)
```bash
python3 main.py
```

This launches the game with an interactive menu. Use the menu to:
1. Select "LOCAL MULTIPLAYER" for 2-player game on same device
2. Select "HOST NETWORK GAME" to host for other players
3. Select "JOIN NETWORK GAME" to find and join a host

**Menu Controls:**
- W/S or Up/Down arrows: Navigate menu
- Space or Enter: Select option
- ESC: Go back
- Type your name when prompted (for network games)

### Quick Start (Skip Menu)
```bash
python3 main.py --quick-local
```

Instantly starts a 2-player local game without showing the menu.

**Game Controls:**
- **Player 1 (Red):** WASD or Arrow Keys to move, Space to shoot, E for mine
- **Player 2 (Blue):** IJKL to move, H to shoot

## How to Play

### Objective
Be the first player to get 5 kills!

### Gameplay
1. Move your tank around the map
2. Shoot bullets at opponents
3. Collect power-up items that spawn randomly
4. Avoid enemy bullets and mines
5. Each tank has 3 HP - getting hit 3 times causes respawn

### Map Elements
- **Dark Gray Blocks:** Solid walls (bullets are destroyed)
- **Light Blue Blocks:** Mirror walls (bullets reflect!)
  - Horizontal mirrors: reflect bullets up/down
  - Vertical mirrors: reflect bullets left/right
  - Diagonal mirrors: reflect at angles

### Power-ups (Yellow circles)
Items spawn randomly every 10 seconds. Pick them up for temporary boosts:

1. **Triple Shot** (3 dots) - Shoot 3 bullets at once for 10 seconds
2. **Shield** (blue circle) - Block the next hit
3. **Speed Boost** (green arrow) - Move 50% faster for 10 seconds
4. **Full Vision** (eye) - See the entire map for 10 seconds

### Advanced Tactics
- Use mirrors to shoot around corners
- Place mines (press E) to control areas
- Tank tracks show where players have been
- Combine power-ups for powerful combinations
- Shield timing is crucial - save it for important moments

## Tips for New Players

1. **Learn the mirrors:** Spend time learning how bullets reflect. The mirror lines show the reflection direction.

2. **Use walls for cover:** Don't stay in open areas - use walls to block enemy fire.

3. **Collect power-ups quickly:** They disappear if not picked up and a new one spawns elsewhere.

4. **Watch your HP:** The hearts above your tank show your health. Retreat when low!

5. **Predict enemy movement:** Lead your shots - bullets travel slower than you might expect.

6. **Control the center:** The middle of the map usually has good access to power-ups.

## Troubleshooting

### Game won't start
- Make sure Pyxel is installed: `pip3 list | grep pyxel`
- Check Python version: `python3 --version` (needs 3.8+)

### Performance issues
- Close other applications
- The game runs at 30 FPS by default

### Network multiplayer not working
- Ensure both computers are on the same Wi-Fi network
- Check firewall settings (port 9999 UDP)
- Currently basic implementation - may have connection issues

## Customization

Want to modify the game? Check out [constants.py](constants.py) where you can change:
- Movement speed
- Bullet speed and bounce count
- Item spawn rates
- Win condition (kills needed)
- Screen size
- And more!

Example: To make the game faster, edit `constants.py`:
```python
PLAYER_SPEED = 2.0  # Default is 1.0
BULLET_SPEED = 4.0  # Default is 2.5
```

## Next Steps

Once you're comfortable with the basics:
1. Try all the power-up combinations
2. Experiment with mirror angles
3. Master the mine placement strategy
4. Read the full [DESIGN.md](DESIGN.md) for technical details

Enjoy Tank Tank! 🎮
