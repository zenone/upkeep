"""
Tests for the AppFinder service (Part of App Uninstaller).
Tests discovery of applications and their associated artifacts using TDD.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from upkeep.core.app_finder import AppArtifact, AppFinder, AppScanResult


@pytest.fixture
def mock_fs():
    """Create a temporary file system structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir)
        
        # Create mock applications
        apps_dir = base / "Applications"
        apps_dir.mkdir()
        
        # 1. Slack.app (Standard app with Bundle ID)
        slack_app = apps_dir / "Slack.app"
        slack_app.mkdir()
        (slack_app / "Contents").mkdir()
        info_plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.tinyspeck.slackmacgap</string>
    <key>CFBundleName</key>
    <string>Slack</string>
    <key>CFBundleShortVersionString</key>
    <string>4.36.134</string>
</dict>
</plist>"""
        (slack_app / "Contents" / "Info.plist").write_text(info_plist_content)
        
        # Create associated artifacts for Slack
        user_home = base / "Users" / "testuser"
        library = user_home / "Library"
        library.mkdir(parents=True)
        
        # ~/Library/Application Support/Slack (Name match)
        (library / "Application Support" / "Slack").mkdir(parents=True)
        (library / "Application Support" / "Slack" / "storage.json").write_text("data")
        
        # ~/Library/Caches/com.tinyspeck.slackmacgap (Bundle ID match)
        (library / "Caches" / "com.tinyspeck.slackmacgap").mkdir(parents=True)
        (library / "Caches" / "com.tinyspeck.slackmacgap" / "Cache.db").write_text("cache")
        
        # ~/Library/Preferences/com.tinyspeck.slackmacgap.plist (Bundle ID match)
        (library / "Preferences").mkdir(parents=True)
        (library / "Preferences" / "com.tinyspeck.slackmacgap.plist").write_text("pref")
        
        yield base


def test_find_app_by_path(mock_fs):
    """Test finding an app by its path."""
    finder = AppFinder(root_path=mock_fs)
    app_path = mock_fs / "Applications" / "Slack.app"
    
    result = finder.scan(str(app_path))
    
    assert result is not None
    assert result.app_info["name"] == "Slack"
    assert result.app_info["bundle_id"] == "com.tinyspeck.slackmacgap"
    assert result.app_info["version"] == "4.36.134"


def test_find_app_artifacts(mock_fs):
    """Test finding associated artifacts for an app."""
    finder = AppFinder(root_path=mock_fs)
    app_path = mock_fs / "Applications" / "Slack.app"
    
    # Mock user home to point to our temp dir structure
    with patch("pathlib.Path.home", return_value=mock_fs / "Users" / "testuser"):
        finder = AppFinder(root_path=mock_fs)
        result = finder.scan(str(app_path))
        
        assert result is not None
        
        # Should find Application Support (Name match)
        support_artifact = next((a for a in result.artifacts if "Application Support" in str(a.path)), None)
        assert support_artifact is not None
        assert support_artifact.kind == "support"
        assert support_artifact.reason == "Name match"
        
        # Should find Caches (Bundle ID match)
        cache_artifact = next((a for a in result.artifacts if "Caches" in str(a.path)), None)
        assert cache_artifact is not None
        assert cache_artifact.kind == "cache"
        assert cache_artifact.reason == "Bundle ID match"
        
        # Should find Preferences (Bundle ID match)
        pref_artifact = next((a for a in result.artifacts if "Preferences" in str(a.path)), None)
        assert pref_artifact is not None
        assert pref_artifact.kind == "preferences"
        assert pref_artifact.reason == "Bundle ID match"


def test_scan_non_existent_app(mock_fs):
    """Test scanning a path that doesn't exist."""
    finder = AppFinder(root_path=mock_fs)
    result = finder.scan(str(mock_fs / "Applications" / "Ghost.app"))
    assert result is None


def test_scan_system_app_protection():
    """Test that system apps are flagged or handled safely."""
    # This might be more relevant for the Uninstaller class, but Finder should identify them
    pass 
