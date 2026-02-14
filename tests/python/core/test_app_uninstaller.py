import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from upkeep.core.app_uninstaller import AppUninstaller
from upkeep.core.app_finder import AppFinder

@pytest.fixture
def mock_app_finder():
    with patch('upkeep.core.app_uninstaller.AppFinder') as MockFinder:
        finder_instance = MockFinder.return_value
        yield finder_instance

@pytest.fixture
def uninstaller(mock_app_finder):
    return AppUninstaller()

def test_init():
    uninstaller = AppUninstaller()
    assert uninstaller.dry_run is True

def test_init_force():
    uninstaller = AppUninstaller(dry_run=False)
    assert uninstaller.dry_run is False

def test_plan_uninstall_calls_finder(uninstaller, mock_app_finder):
    app_path = "/Applications/TestApp.app"
    
    # Mock AppScanResult and Artifacts
    mock_result = MagicMock()
    mock_result.app_info = {"path": app_path}
    
    artifact1 = MagicMock()
    artifact1.path = Path("/Library/Preferences/com.example.TestApp.plist")
    
    artifact2 = MagicMock()
    artifact2.path = Path("/Library/Application Support/TestApp")
    
    mock_result.artifacts = [artifact1, artifact2]
    
    mock_app_finder.scan.return_value = mock_result

    plan = uninstaller.plan_uninstall(app_path)
    
    mock_app_finder.scan.assert_called_once_with(app_path)
    assert plan["app"] == Path(app_path)
    assert len(plan["related"]) == 2
    assert Path("/Library/Preferences/com.example.TestApp.plist") in plan["related"]

def test_uninstall_dry_run_returns_plan_no_deletion(uninstaller, mock_app_finder):
    app_path = "/Applications/TestApp.app"
    related_files = [
        Path("/Library/Preferences/com.example.TestApp.plist"),
        Path("/Library/Application Support/TestApp")
    ]
    
    # Mock AppScanResult
    mock_result = MagicMock()
    mock_result.app_info = {"path": app_path}
    
    artifact1 = MagicMock()
    artifact1.path = related_files[0]
    
    artifact2 = MagicMock()
    artifact2.path = related_files[1]
    
    mock_result.artifacts = [artifact1, artifact2]
    
    mock_app_finder.scan.return_value = mock_result

    with patch('upkeep.core.app_uninstaller.shutil') as mock_shutil, \
         patch('upkeep.core.app_uninstaller.os') as mock_os:
        
        result = uninstaller.uninstall(app_path)
        
        # Verify dry run behavior
        assert result["dry_run"] is True
        assert result["status"] == "planned"
        # The result items include related files plus the app itself
        assert len(result["items"]) == 3
        assert Path(app_path) in result["items"]
        
        # Verify no deletion calls
        mock_shutil.rmtree.assert_not_called()
        mock_os.remove.assert_not_called()
