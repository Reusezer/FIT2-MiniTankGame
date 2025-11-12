# Tank Tank - Design Document

## Game Concept

Tank Tank is a retro-style 2D tank battle game inspired by classic games like Battle City and Tank Trouble. Players control tanks in a top-down view, shooting bullets that reflect off mirror surfaces and navigating through destructible walls.

## Core Mechanics

### Movement
- Tank moves at slow speed (1.0 pixels/frame by default)
- Can move in 4 directions: up, down, left, right
- Movement leaves tank track trails that fade over time
- Collision detection with walls and mirrors

### Combat
- Tanks shoot bullets that travel in straight lines
- Bullets reflect off mirror walls (angle of incidence = angle of reflection)
- Bullets bounce up to 3 times before disappearing
- Each tank has 3 HP
- Getting hit 3 times causes respawn
- Shooting has a cooldown to prevent spam

### Vision System
- Default vision radius: 80 pixels
- With Vision power-up: 200 pixels (full map)
- Vignette effect darkens areas outside vision range

## Map Design

### Tile Types
1. Empty tiles - tanks can move through
2. Walls - solid obstacles that bullets destroy
3. Horizontal mirrors - reflect bullets vertically
4. Vertical mirrors - reflect bullets horizontally
5. Diagonal mirrors (\ and /) - reflect bullets diagonally

### Map Generation
- 32x32 tile map (256x256 pixels)
- Border walls around the edge
- Random obstacle clusters (walls and mirrors)
- 4 spawn points in corners kept clear

## Power-up Items

### Triple Shot
- Duration: 10 seconds
- Effect: Shoot 3 bullets in a spread pattern
- Visual: 3 dots icon

### Shield
- Duration: Until hit once
- Effect: Blocks next damage
- Visual: Blue circle around tank

### Speed Boost
- Duration: 10 seconds
- Effect: 1.5x movement speed
- Visual: Green arrow icon

### Full Vision
- Duration: 10 seconds
- Effect: See entire map
- Visual: Eye icon

### Mine (Placeable)
- Duration: 20 seconds or until triggered
- Effect: Damages nearby enemies
- Trigger radius: 12 pixels
- Visual: Red circle with danger marker

## Game Modes

### Local Multiplayer (Implemented)
- 2-4 players on same device
- Player 1: WASD/Arrows + Space
- Player 2: IJKL + H
- First to 5 kills wins

### Network Multiplayer (Basic Implementation)
- UDP-based local network play
- Host/client model
- Automatic lobby discovery via broadcast
- 20Hz tick rate for smooth gameplay

## Technical Architecture

### Classes

#### Player
- Position, direction, HP
- Active power-ups and timers
- Shooting logic
- Movement with collision detection
- Tank track trail system

#### Bullet
- Position and velocity
- Reflection logic for mirrors
- Collision detection with players
- Limited lifetime and bounce count

#### MapGenerator
- Procedural map generation
- Spawn point management
- Map rendering

#### Item & ItemSpawner
- Power-up item management
- Random spawning every 10 seconds
- Pickup detection

#### Mine
- Placeable trap system
- Proximity detection
- Owner identification

#### NetworkManager
- UDP socket management
- Lobby discovery
- Player synchronization
- Game state broadcasting

### Constants
- All game parameters centralized
- Easy balancing and tweaking
- Color palette definitions

## Art Style

### Visual Design
- Retro pixel art aesthetic
- 16-color Pyxel palette
- Minimalist UI
- Clear visual feedback

### Effects
- Tank track trails
- Bullet trails
- Explosion animations
- Pulsing item pickups
- Vignette for vision system

## Future Enhancements

### Gameplay
- Destructible walls (partially implemented)
- More power-ups (laser, rapid fire, etc.)
- Different tank types with unique abilities
- Team battles (2v2)

### Maps
- Multiple pre-designed maps
- Better procedural generation with paths
- Interactive map elements (teleporters, etc.)

### Network
- More robust synchronization
- Lag compensation
- Reconnection support
- Matchmaking system

### Polish
- Sound effects and music
- Particle effects
- Screen shake
- Better UI/menus
- Replay system

## Controls Reference

### Player 1
- W/Up Arrow: Move up
- S/Down Arrow: Move down
- A/Left Arrow: Move left
- D/Right Arrow: Move right
- Space: Shoot
- E: Place mine

### Player 2
- I: Move up
- K: Move down
- J: Move left
- L: Move right
- H: Shoot

### General
- Q: Quit game
- R: Restart (when game over)

## Performance Considerations

- 30 FPS target
- 256x256 resolution keeps rendering lightweight
- Efficient collision detection using tile-based system
- Limited number of active bullets and items
- Network tick rate at 20Hz to reduce bandwidth

## Testing Checklist

- [x] Player movement and collision
- [x] Bullet shooting and reflection
- [x] Item pickup and effects
- [x] HP and respawn system
- [x] Win condition (5 kills)
- [x] UI display (scores, HP)
- [ ] Network multiplayer
- [ ] Mine placement and triggering
- [ ] All power-up combinations
- [ ] Map edge cases
