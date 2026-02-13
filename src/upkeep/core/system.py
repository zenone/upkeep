"""
System information and utilities.

This module provides functions for gathering system information on macOS.
"""

import os
import platform
import subprocess


def get_macos_version() -> str:
    """
    Get the macOS version string.

    Returns:
        Version string (e.g., "26.2.0")

    Raises:
        RuntimeError: If not running on macOS or version cannot be determined
    """
    if platform.system() != "Darwin":
        raise RuntimeError("This function only works on macOS")

    try:
        result = subprocess.run(
            ["sw_vers", "-productVersion"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise RuntimeError(f"Could not determine macOS version: {e}")


def get_macos_build() -> str:
    """
    Get the macOS build string.

    Returns:
        Build string (e.g., "25C56")

    Raises:
        RuntimeError: If not running on macOS or build cannot be determined
    """
    if platform.system() != "Darwin":
        raise RuntimeError("This function only works on macOS")

    try:
        result = subprocess.run(
            ["sw_vers", "-buildVersion"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise RuntimeError(f"Could not determine macOS build: {e}")


def get_username() -> str:
    """
    Get the current username.

    Returns:
        Username string (e.g., "szenone")
    """
    # Try environment variables first
    username = os.environ.get("USER") or os.environ.get("LOGNAME")

    # Fallback to whoami command
    if not username:
        try:
            result = subprocess.run(
                ["whoami"],
                capture_output=True,
                text=True,
                check=True,
            )
            username = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            username = "unknown"

    return username


def get_system_info() -> dict[str, str]:
    """
    Get comprehensive system information.

    Returns:
        Dictionary with system information:
        - platform: OS name (should be "Darwin")
        - version: macOS version string
        - build: macOS build string
        - hostname: System hostname
        - architecture: CPU architecture
        - username: Current username

    Raises:
        RuntimeError: If not running on macOS
    """
    if platform.system() != "Darwin":
        raise RuntimeError("This function only works on macOS")

    return {
        "platform": platform.system(),
        "version": get_macos_version(),
        "build": get_macos_build(),
        "hostname": platform.node(),
        "architecture": platform.machine(),
        "username": get_username(),
    }


def check_command_exists(command: str) -> bool:
    """
    Check if a command exists in the system PATH.

    Args:
        command: Command name to check

    Returns:
        True if command exists, False otherwise
    """
    try:
        subprocess.run(
            ["command", "-v", command],
            capture_output=True,
            check=True,
            shell=False,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
