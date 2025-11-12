# Network Multiplayer Guide - Tank Tank

## Quick Start

### Playing Over Internet with Direct IP

**Host:**
1. Run `python3 main.py`
2. Select "HOST NETWORK GAME"
3. Enter your name
4. Your IP address will show in the lobby: `Your IP: 192.168.x.x:9999`
5. Share this IP with your friend
6. Wait for them to join, then press Enter to start

**Client:**
1. Run `python3 main.py`
2. Select "JOIN BY IP ADDRESS"
3. Type the host's IP (e.g., `192.168.1.100`)
4. Press Enter
5. Enter your name
6. Wait for host to start the game

## Finding Your IP Address

**When hosting**, the game automatically shows your local IP in the lobby.

For internet play over different networks:
- **Public IP**: Visit https://whatismyipaddress.com
- **Local IP** (for same WiFi): Check the lobby screen when hosting

## Port Forwarding (For Internet Play)

If you want friends on different networks to join, the host needs to:

1. Access router settings (usually `192.168.1.1`)
2. Find "Port Forwarding" section
3. Forward **UDP port 9999** to your computer's local IP
4. Share your **public IP** with friends

## Troubleshooting

**"Connection timeout"**
- Check the IP address is correct
- Make sure port 9999 is not blocked by firewall
- For internet play: host must forward port 9999

**"Failed to bind port"**
- Port 9999 is already in use
- Close other game instances
- Try restarting your computer

**Lag issues**
- Use wired connection instead of WiFi
- Play with friends on same network or nearby
- Close bandwidth-heavy apps

## Network Modes

The game now supports:

1. **Local Multiplayer** - 2 players on same device, no network needed
2. **LAN (Same WiFi)** - Players on same network can auto-discover (not fully implemented)
3. **Direct IP** - Enter host's IP address to connect (works over internet)

## Tips

- Test locally first (same WiFi) before trying internet play
- Lower ping = smoother gameplay
- UDP protocol on port 9999
- Close unnecessary programs to reduce lag
