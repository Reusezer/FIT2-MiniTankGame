#!/usr/bin/env python3
"""
Test script for TCP networking
Run this in two separate terminals to test connection
"""

import sys
import time
from network_tcp import NetworkPeer

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Terminal 1 (Server): python3 test_network_tcp.py server")
        print("  Terminal 2 (Client): python3 test_network_tcp.py client <server_ip>")
        print("\nExample:")
        print("  Terminal 1: python3 test_network_tcp.py server")
        print("  Terminal 2: python3 test_network_tcp.py client 192.168.1.100")
        return

    mode = sys.argv[1]

    if mode == "server":
        print("=== Starting as SERVER ===")
        peer = NetworkPeer(is_server=True, port=9999)
        print(f"Server started on {peer.my_ip}:9999")
        print("Waiting for client to connect...")

        # Wait for connection
        while not peer.is_connected():
            time.sleep(0.5)

        print("✓ Client connected!")
        print("\nSending test messages...")

        # Send messages
        for i in range(5):
            peer.send({"type": "test", "message": f"Server message {i}", "count": i})
            time.sleep(1)

            # Check for replies
            msg = peer.recv_latest()
            if msg:
                print(f"Received: {msg}")

        print("\nTest complete!")
        peer.stop()

    elif mode == "client":
        if len(sys.argv) < 3:
            print("Error: Please provide server IP")
            print("Example: python3 test_network_tcp.py client 192.168.1.100")
            return

        server_ip = sys.argv[2]
        print(f"=== Starting as CLIENT (connecting to {server_ip}) ===")
        peer = NetworkPeer(is_server=False, server_ip=server_ip, port=9999)

        print("Connecting...")
        timeout = 10
        while not peer.is_connected() and timeout > 0:
            time.sleep(0.5)
            timeout -= 0.5

        if not peer.is_connected():
            print("✗ Connection failed!")
            return

        print("✓ Connected to server!")
        print("\nListening for messages...")

        # Receive and reply
        for i in range(5):
            msg = peer.recv_latest()
            if msg:
                print(f"Received: {msg}")
                peer.send({"type": "reply", "message": f"Client reply {i}"})
            time.sleep(1)

        print("\nTest complete!")
        peer.stop()

    else:
        print(f"Unknown mode: {mode}")
        print("Use 'server' or 'client'")


if __name__ == "__main__":
    main()
