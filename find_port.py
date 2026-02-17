#!/usr/bin/env python3
"""Find available port for web server.

Standalone script for use by shell scripts.
Returns first available port in range 8080-8089, or exits with error.
"""

import socket
import sys


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        return False
    finally:
        try:
            sock.close()
        except:
            pass


def main():
    """Find and print first available port in range 8080-8089."""
    for port in range(8080, 8090):
        if is_port_available(port):
            print(port)
            sys.exit(0)

    # No available ports
    print("ERROR: No available ports in range 8080-8089", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
