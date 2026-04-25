#!/usr/bin/env python3
"""
Simple UDP sender script that sends byte payloads from base64 encoded strings.
"""

import socket
import sys
import base64


def send_udp(host, port, message, source_ip=None, source_port=0):
    """
    Send a UDP packet with the specified message.

    Args:
        host: Target hostname or IP address
        port: Target port number
        message: Message to send (bytes or string)
        source_ip: Source IP address to bind to (optional)
        source_port: Source port to bind to (optional, 0 = auto)
    """
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # Bind to specific source IP/port if specified
        if source_ip:
            sock.bind((source_ip, source_port))
            print(f"Bound to source: {source_ip}:{source_port}")

        # Convert string to bytes if necessary
        if isinstance(message, str):
            message = message.encode('utf-8')

        # Send the message
        sock.sendto(message, (host, port))
        print(f"Sent {len(message)} bytes to {host}:{port}")
        print(f"Data: {message}")

    finally:
        sock.close()


if __name__ == "__main__":
    # Default values
    target_host = "224.0.1.129"
    target_port = 319
    source_ip = "127.0.0.1"
    source_port = 319

    # Decode base64 payload to bytes
    try:
        message = base64.b64decode("DwIA0AAAAAAAAAAAAAAAAAAAAAAsz2f//mPvJAABAAAFAAAAAAAAADR4KUQDKpBOB8g4hCV5YGLU+1QporfN/T6kBrusQtbguv8kvSm1CzB9Q7WjvRUFkRBZurMRh7BPLLcK2PnguLPg3HEJkXw6D8Dvsn0Etw4VEcjIIk94cXsve1MoWwvcO+hNRXnJf4iJbjoGcvIUhwPcTyUsyJan9xH7IGwG/KjuAAAAAciBCMzdnIk8km2UI49X+1J90MykR6ohxocITRL+toYqAAAAAA==")
    except Exception as e:
        print(f"Error decoding base64: {e}")
        sys.exit(1)

    print(f"UDP Sender")
    print(f"Target: {target_host}:{target_port}")
    print("-" * 40)

    send_udp(target_host, target_port, message, source_ip, source_port)
