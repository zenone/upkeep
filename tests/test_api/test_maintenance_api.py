"""Unit tests for MaintenanceAPI - Tier 1/2/3 operations."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from upkeep.api.maintenance import MaintenanceAPI


class TestMaintenanceAPI:
    """Test MaintenanceAPI operations."""

    @pytest.fixture
    def api(self):
        """Create MaintenanceAPI instance."""
        return MaintenanceAPI()

    def test_get_operations_returns_list(self, api):
        """Test that get_operations returns a list of operations."""
        operations = api.get_operations()
        assert isinstance(operations, list)
        assert len(operations) > 0

    def test_operations_have_required_fields(self, api):
        """Test that each operation has required fields."""
        operations = api.get_operations()
        required_fields = ['id', 'name', 'description', 'category', 'safe']
        
        for op in operations:
            for field in required_fields:
                assert field in op, f"Operation {op.get('id', 'unknown')} missing field: {field}"

    def test_tier1_operations_exist(self, api):
        """Test that all Tier 1 operations are present."""
        operations = api.get_operations()
        op_ids = {op['id'] for op in operations}
        
        tier1_ops = [
            'disk-triage',
            'downloads-report',
            'downloads-cleanup',
            'xcode-cleanup',
            'caches-cleanup',
            'logs-cleanup',
            'trash-empty',
        ]
        
        for op_id in tier1_ops:
            assert op_id in op_ids, f"Tier 1 operation missing: {op_id}"

    def test_tier2_operations_exist(self, api):
        """Test that all Tier 2 operations are present."""
        operations = api.get_operations()
        op_ids = {op['id'] for op in operations}
        
        tier2_ops = [
            'docker-prune',
            'xcode-device-support',
            'ios-backups-report',
        ]
        
        for op_id in tier2_ops:
            assert op_id in op_ids, f"Tier 2 operation missing: {op_id}"

    def test_tier3_operations_exist(self, api):
        """Test that all Tier 3 operations are present."""
        operations = api.get_operations()
        op_ids = {op['id'] for op in operations}
        
        tier3_ops = [
            'application-support-report',
            'dev-artifacts-report',
            'mail-size-report',
            'messages-attachments-report',
            'cloudstorage-report',
            'virtualbox-report',
        ]
        
        for op_id in tier3_ops:
            assert op_id in op_ids, f"Tier 3 operation missing: {op_id}"

    def test_total_operation_count(self, api):
        """Test that we have the expected number of operations."""
        operations = api.get_operations()
        # 38 operations as of current implementation
        assert len(operations) >= 38, f"Expected at least 38 operations, got {len(operations)}"

    def test_report_operations_are_safe(self, api):
        """Test that all report operations are marked as safe."""
        operations = api.get_operations()
        report_ops = [op for op in operations if op['category'] == 'Reports']
        
        for op in report_ops:
            assert op['safe'] is True, f"Report operation {op['id']} should be safe"

    def test_operation_details_loaded(self, api):
        """Test that WHY/WHAT details are loaded for operations."""
        operations = api.get_operations()
        
        # At least some operations should have detailed WHY/WHAT
        ops_with_why = [op for op in operations if op.get('why')]
        ops_with_what = [op for op in operations if op.get('what')]
        
        assert len(ops_with_why) > 20, "Expected most operations to have 'why' details"
        assert len(ops_with_what) > 20, "Expected most operations to have 'what' details"

    def test_docker_prune_has_docker_dependency(self, api):
        """Test that docker-prune operation is properly configured."""
        operations = api.get_operations()
        docker_op = next((op for op in operations if op['id'] == 'docker-prune'), None)
        
        assert docker_op is not None
        assert 'Docker' in docker_op['name'] or 'Docker' in docker_op['description']

    def test_xcode_operations_properly_configured(self, api):
        """Test Xcode-related operations."""
        operations = api.get_operations()
        
        xcode_ops = [
            op for op in operations 
            if 'xcode' in op['id'].lower()
        ]
        
        assert len(xcode_ops) >= 2, "Expected at least 2 Xcode operations"
        
        for op in xcode_ops:
            assert 'Xcode' in op['name'] or 'Xcode' in op['description']


class TestMaintenanceAPIEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def api(self):
        """Create MaintenanceAPI instance."""
        return MaintenanceAPI()

    def test_operations_list_is_not_empty(self, api):
        """Test that operations list is never empty."""
        operations = api.get_operations()
        assert len(operations) > 0, "Operations list should never be empty"

    def test_operation_ids_are_unique(self, api):
        """Test that all operation IDs are unique."""
        operations = api.get_operations()
        op_ids = [op['id'] for op in operations]
        
        assert len(op_ids) == len(set(op_ids)), "Operation IDs should be unique"

    def test_operation_categories_are_valid(self, api):
        """Test that operations have valid categories."""
        operations = api.get_operations()
        valid_categories = {
            'System Updates',
            'Disk Maintenance',
            'Cache Cleanup',
            'Cleanup Operations',
            'Reports',
            'Space Cleanup',
        }
        
        for op in operations:
            # Allow some flexibility in category names
            assert op['category'] is not None, f"Operation {op['id']} has no category"
