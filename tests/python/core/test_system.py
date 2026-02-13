"""
Tests for core.system module.
"""

import platform

import pytest

from upkeep.core import system


class TestMacOSVersion:
    """Tests for macOS version detection."""

    def test_get_macos_version(self) -> None:
        """Test that we can get macOS version."""
        if platform.system() != "Darwin":
            pytest.skip("Only runs on macOS")

        version = system.get_macos_version()
        assert isinstance(version, str)
        assert len(version) > 0
        # Should be in format like "26.2" or "26.2.0"
        parts = version.split(".")
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts)

    def test_get_macos_build(self) -> None:
        """Test that we can get macOS build."""
        if platform.system() != "Darwin":
            pytest.skip("Only runs on macOS")

        build = system.get_macos_build()
        assert isinstance(build, str)
        assert len(build) > 0


class TestSystemInfo:
    """Tests for system information gathering."""

    def test_get_system_info(self) -> None:
        """Test comprehensive system info gathering."""
        if platform.system() != "Darwin":
            pytest.skip("Only runs on macOS")

        info = system.get_system_info()

        # Verify structure
        assert isinstance(info, dict)
        required_keys = {"platform", "version", "build", "hostname", "architecture"}
        assert required_keys.issubset(info.keys())

        # Verify values
        assert info["platform"] == "Darwin"
        assert len(info["version"]) > 0
        assert len(info["build"]) > 0
        assert len(info["hostname"]) > 0
        assert info["architecture"] in ("arm64", "x86_64")


class TestCommandExists:
    """Tests for command existence checking."""

    def test_check_command_exists_true(self) -> None:
        """Test checking for a command that exists."""
        # ls should always exist on macOS
        assert system.check_command_exists("ls") is True

    def test_check_command_exists_false(self) -> None:
        """Test checking for a command that doesn't exist."""
        # This command should never exist
        assert system.check_command_exists("this_command_does_not_exist_12345") is False

    @pytest.mark.parametrize(
        "command",
        [
            "ls",
            "cat",
            "echo",
            "pwd",
            "which",
        ],
    )
    def test_check_common_commands(self, command: str) -> None:
        """Test that common Unix commands exist."""
        assert system.check_command_exists(command) is True
