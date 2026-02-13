"""Port availability utilities for web server.

Provides reliable port conflict detection and automatic fallback.
"""

import socket


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is available for binding.

    Uses socket binding to atomically test port availability.
    This is race-condition-free as the OS guarantees atomicity.

    Args:
        port: Port number to check
        host: Host address to bind to (default: 127.0.0.1)

    Returns:
        True if port is available, False if in use
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        # Port is in use (EADDRINUSE) or other binding error
        return False
    finally:
        # Ensure socket is closed even if bind() raised an exception
        try:
            sock.close()
        except:
            pass


def find_available_port(
    start_port: int = 8080, end_port: int = 8089, host: str = "127.0.0.1"
) -> int | None:
    """Find the first available port in a range.

    Tries ports sequentially from start_port to end_port (inclusive).

    Args:
        start_port: First port to try (default: 8080)
        end_port: Last port to try (default: 8089)
        host: Host address to bind to (default: 127.0.0.1)

    Returns:
        First available port number, or None if all ports are in use
    """
    for port in range(start_port, end_port + 1):
        if is_port_available(port, host):
            return port

    return None
