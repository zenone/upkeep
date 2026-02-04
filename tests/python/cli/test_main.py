"""
Tests for CLI main module.
"""

import pytest
from click.testing import CliRunner
from upkeep.cli.main import main


class TestCLIMain:
    """Test main CLI entry point."""

    def test_cli_help(self) -> None:
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "macOS Maintenance Toolkit" in result.output
        assert "Michelin Star Quality" in result.output

    def test_cli_version(self) -> None:
        """Test CLI version output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "3.0.0" in result.output

    def test_cli_has_commands(self) -> None:
        """Test that CLI has expected commands."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert "tui" in result.output
        assert "status" in result.output
        assert "analyze" in result.output


class TestStatusCommand:
    """Test status command."""

    def test_status_command(self) -> None:
        """Test status command runs."""
        runner = CliRunner()
        result = runner.invoke(main, ["status"])

        # Should complete successfully
        assert result.exit_code == 0

        # Should show expected information
        assert "System Status" in result.output
        assert "Disk Usage" in result.output
        assert "System:" in result.output or "macOS" in result.output


class TestAnalyzeCommand:
    """Test analyze command."""

    def test_analyze_help(self) -> None:
        """Test analyze command help."""
        runner = CliRunner()
        result = runner.invoke(main, ["analyze", "--help"])

        assert result.exit_code == 0
        assert "Analyze storage" in result.output

    def test_analyze_current_directory(self, tmp_path) -> None:
        """Test analyzing a directory."""
        runner = CliRunner()

        # Create some test files
        (tmp_path / "file1.txt").write_text("test content 1")
        (tmp_path / "file2.txt").write_text("test content 2")

        result = runner.invoke(main, ["analyze", str(tmp_path)])

        # Should complete successfully
        assert result.exit_code == 0

        # Should show analysis results
        assert "Storage Analysis" in result.output
        assert "Total:" in result.output


class TestTUICommand:
    """Test TUI command."""

    def test_tui_help(self) -> None:
        """Test TUI command help."""
        runner = CliRunner()
        result = runner.invoke(main, ["tui", "--help"])

        assert result.exit_code == 0
        assert "Terminal User Interface" in result.output or "TUI" in result.output
