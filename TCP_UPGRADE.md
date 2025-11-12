# TCP Network Upgrade - Tank Tank

## What Changed?

Switched from **UDP** to **TCP** networking with **threading** for reliable, non-blocking multiplayer.

### Why TCP?

1. **Reliable delivery** - No dropped packets
2. **Connection state** - Know when player disconnects
3. **Easier to debug** - Messages arrive in order
4. **Better for turn-based/state sync** - Perfect for our game

### Why Threading?

1. **No freezing** - Network I/O happens in background
2. **Non-blocking** - Pyxel update() stays smooth
3. **Queue-based** - Thread-safe message passing

## New Architecture

```
┌─────────────────────────────────────┐
│  Pyxel Game (Main Thread)           │
│  update() / draw()                  │
│     │                               │
│     ├─> send(msg)      [Outbox]    │
│     └─> recv_latest()  [Inbox]     │
└─────────────────────────────────────┘
           ↕️  (queues)
┌─────────────────────────────────────┐
│  Network Threads (Background)        │
│  - Accept/Connect Thread            │
│  - Send Thread (outbox → socket)    │
│  - Recv Thread (socket → inbox)     │
└─────────────────────────────────────┘
           ↕️  (TCP socket)
┌─────────────────────────────────────┐
│  Other Player                        │
└─────────────────────────────────────┘
```

## Files

### New Files

- [network_tcp.py](network_tcp.py) - New TCP implementation
- [test_network_tcp.py](test_network_tcp.py) - Test script
- [TCP_UPGRADE.md](TCP_UPGRADE.md) - This file

### Modified Files

- [app.py](app.py) - Now imports `network_tcp` instead of `network`

### Old Files (kept for reference)

- [network.py](network.py) - Old UDP version (not used)

## How to Test Network

### Terminal Test (Before Running Game)

**Terminal 1 (Server):**
```bash
python3 test_network_tcp.py server
```
You'll see: `Server started on 192.168.x.x:9999`

**Terminal 2 (Client):**
```bash
python3 test_network_tcp.py client 192.168.x.x
```
Replace `192.168.x.x` with the IP shown by server.

If you see messages exchanged → TCP works! ✓

### Game Test

**Mac 1 (Host):**
```bash
python3 main.py
→ Select "HOST NETWORK GAME"
→ Enter name
→ Note the IP shown: "Your IP: 192.168.x.x:9999"
→ Share this IP with friend
```

**Mac 2 (Client):**
```bash
python3 main.py
→ Select "JOIN BY IP ADDRESS"
→ Type host's IP
→ Enter name
→ Should connect automatically
```

## Advantages of New System

### Old (UDP)
- ❌ Messages can be lost
- ❌ No connection state
- ❌ Broadcast doesn't work across routers
- ❌ Hard to debug
- ❌ Manual retry logic needed

### New (TCP)
- ✅ Guaranteed delivery
- ✅ Knows when connected/disconnected
- ✅ Direct IP connection
- ✅ Easy to debug (messages in order)
- ✅ Automatic retry in background

## Key Changes

### 1. Connection Handling

**Old (UDP):**
```python
# Had to manually discover and join
self.socket.sendto(b"DISCOVER", ('<broadcast>', 9999))
# Wait for response...
```

**New (TCP):**
```python
# Just connect, thread handles it
peer = NetworkPeer(is_server=False, server_ip="192.168.1.100")
# Connection happens in background
```

### 2. Message Sending

**Old (UDP):**
```python
# Had to manage addresses
self.socket.sendto(data, address)
```

**New (TCP):**
```python
# Just send, thread handles it
peer.send({"type": "move", "x": 10, "y": 20})
```

### 3. Message Receiving

**Old (UDP):**
```python
# Blocking!
data, addr = self.socket.recvfrom(4096)
```

**New (TCP):**
```python
# Non-blocking, latest only
msg = peer.recv_latest()
if msg:
    # Process message
```

## Common Issues & Fixes

### "Connection timeout"
- **Check**: Both Macs on same Wi-Fi?
- **Check**: Firewall blocking port 9999?
- **Check**: Using correct IP (not 127.0.0.1)?

### "Connection refused"
- **Check**: Server started first?
- **Check**: Port 9999 not in use?
- **Try**: Restart both games

### "No IP shown in lobby"
- **Check**: Did you reach the lobby screen?
- **Check**: Selected "HOST NETWORK GAME"?
- **Fallback**: Run `ipconfig` (Windows) or `ifconfig` (Mac)

## Performance Notes

- **Latency**: ~10-50ms on same network
- **Message size**: Keep under 1KB for smooth gameplay
- **Update rate**: Send every frame OK (30 FPS)
- **Bandwidth**: Minimal (~1-2 KB/s per player)

## For Developers

### Adding New Message Types

```python
# Send
peer.send({
    "type": "bullet_fired",
    "x": bullet.x,
    "y": bullet.y,
    "vx": bullet.vx,
    "vy": bullet.vy,
    "owner_id": player.id
})

# Receive in update()
msg = peer.recv_latest()
if msg and msg.get("type") == "bullet_fired":
    bullet = Bullet(msg["x"], msg["y"], msg["vx"], msg["vy"], msg["owner_id"])
    bullets.append(bullet)
```

### Message Format

All messages are JSON dicts with at least:
- `"type"`: Message type string
- Other fields depend on type

Examples:
```python
{"type": "player_state", "x": 100, "y": 50, "hp": 3}
{"type": "input", "dx": 1, "dy": 0, "shoot": True}
{"type": "game_event", "event": "player_hit", "player_id": 1}
```

## Next Steps

Current implementation:
- ✅ TCP connection with threading
- ✅ Non-blocking send/recv
- ✅ Connection state tracking
- ✅ Direct IP input

To fully integrate:
- [ ] Send player positions each frame
- [ ] Sync bullets across network
- [ ] Handle disconnections gracefully
- [ ] Add reconnection support
- [ ] Implement lag compensation

## Testing Checklist

- [ ] Server starts and shows IP
- [ ] Client connects to server
- [ ] Messages sent/received successfully
- [ ] Game doesn't freeze when networking active
- [ ] Disconnection detected properly
- [ ] Works across two different Macs
- [ ] Works with firewall enabled
- [ ] Latency acceptable (<100ms)

---

**Bottom line**: TCP + threading = reliable, smooth multiplayer! 🎮
