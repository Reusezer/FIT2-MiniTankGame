# Changelog - Tank Tank

## Version 1.1 - Menu System Update (Current)

### Fixed
- **Menu selection now works properly** - Fixed issue where "LOCAL MULTIPLAYER" selection wasn't starting the game
  - The `menu.update()` method now correctly returns actions from sub-update methods
  - All menu options (Local, Host, Join, Quit) now function as expected

### Added
- **Interactive menu system** with visual feedback
- **Player name input screen** for network multiplayer
- **Connection testing** before starting network games
- **Lobby/waiting room** showing connected players
- **Network status indicators** with progress bars and error messages
- **Quick start option** via `--quick-local` flag
- **Test script** (`test_menu.py`) to verify menu logic

### Changed
- Default behavior now shows menu instead of starting directly
- Network games require name input before connecting
- Port binding errors are now caught and displayed to user
- ESC key returns to menu when game is over (instead of just quitting)

### Technical Changes
- Created `app.py` - Main application controller
- Created `menu.py` - Menu and UI system (350+ lines)
- Updated `main.py` - Entry point with menu integration
- Updated `network.py` - Added connection testing and periodic discovery
- Updated `README.md` and `QUICKSTART.md` - New menu instructions

## Version 1.0 - Initial Release

### Features
- 2D top-down tank combat
- Local 2-player support
- Bullet reflection mechanics (4 mirror types)
- 5 power-up items (triple shot, shield, speed, vision, mine)
- Tank track trails
- Procedural map generation
- Basic network multiplayer framework
- First to 5 kills wins

### Components
- Player movement and shooting
- Bullet physics with reflection
- Item spawning system
- Map generation with obstacles
- HP and respawn system
- Game state management
- UDP networking (basic)

---

## How to Update

If you have an older version, simply replace the files:

```bash
# The game will now start with a menu by default
python3 main.py

# Or use quick-start for immediate local play
python3 main.py --quick-local
```

## Migration Notes

- Old command line args (`--host`, `--join`) have been replaced with menu system
- For quick testing, use `--quick-local` instead
- Network games now require entering a player name
