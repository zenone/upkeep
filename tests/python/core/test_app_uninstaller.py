import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from upkeep.core.app_uninstaller import AppUninstaller, UninstallResult
from upkeep.core.app_finder import AppScanResult, AppArtifact

def test_init():
    uninstaller = AppUninstaller()
    assert uninstaller.dry_run is True

def test_init_force():
    uninstaller = AppUninstaller(dry_run=False)
    assert uninstaller.dry_run is False

def test_uninstall_dry_run_returns_result_no_deletion():
    uninstaller = AppUninstaller(dry_run=True)
    
    app_path = Path("/Applications/TestApp.app")
    
    # Mock AppScanResult
    artifact1 = AppArtifact(
        path=app_path,
        kind="app",
        size_bytes=100,
        reason="App bundle"
    )
    
    artifact2 = AppArtifact(
        path=Path("/Library/Preferences/com.example.TestApp.plist"),
        kind="preferences",
        size_bytes=50,
        reason="Bundle ID match"
    )
    
    mock_result = AppScanResult(
        app_info={"path": str(app_path), "name": "TestApp"},
        artifacts=[artifact1, artifact2],
        total_size_bytes=150
    )
    
    # Mock exists() on paths
    with patch('pathlib.Path.exists', return_value=True):
        with patch('upkeep.core.app_uninstaller.shutil') as mock_shutil:
            result = uninstaller.uninstall(mock_result)
            
            # Verify result structure
            assert isinstance(result, UninstallResult)
            assert result.success is True
            assert len(result.deleted_paths) == 2
            assert result.bytes_recovered == 150
            
            # Verify no deletion calls (move)
            mock_shutil.move.assert_not_called()

def test_uninstall_wet_run_deletes_files():
    uninstaller = AppUninstaller(dry_run=False)
    
    app_path = Path("/Applications/TestApp.app")
    
    artifact1 = AppArtifact(
        path=app_path,
        kind="app",
        size_bytes=100,
        reason="App bundle"
    )
    
    mock_result = AppScanResult(
        app_info={"path": str(app_path), "name": "TestApp"},
        artifacts=[artifact1],
        total_size_bytes=100
    )
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.is_dir', return_value=True), \
         patch('pathlib.Path.is_symlink', return_value=False), \
         patch('upkeep.core.app_uninstaller.shutil') as mock_shutil:
            
        result = uninstaller.uninstall(mock_result)
        
        assert result.success is True
        assert len(result.deleted_paths) == 1
        
        # Verify move called
        mock_shutil.move.assert_called()
        # Check args
        args, _ = mock_shutil.move.call_args
        assert args[0] == str(app_path)
        assert ".Trash" in args[1]
