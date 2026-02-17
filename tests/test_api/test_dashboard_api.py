"""Tests for Dashboard and Operations functionality."""

import pytest

from upkeep.api.maintenance import MaintenanceAPI


class TestOperationsMetadata:
    """Tests for operations metadata and categorization."""

    @pytest.fixture
    def api(self):
        """Create MaintenanceAPI instance."""
        return MaintenanceAPI()

    def test_all_44_operations_present(self, api):
        """Test that all 44 operations are present."""
        operations = api.get_operations()
        assert len(operations) == 44, f"Expected 44 operations, got {len(operations)}"

    def test_all_operations_have_category(self, api):
        """Test that all operations have a category."""
        operations = api.get_operations()
        for op in operations:
            assert "category" in op, f"Operation {op.get('id')} missing category"
            assert op["category"] is not None

    def test_all_operations_have_guidance(self, api):
        """Test that all operations have guidance/description."""
        operations = api.get_operations()
        for op in operations:
            assert "description" in op or "guidance" in op, \
                f"Operation {op.get('id')} missing description/guidance"

    def test_recommended_operations_exist(self, api):
        """Test that recommended operations are properly flagged."""
        operations = api.get_operations()
        recommended = [op for op in operations if op.get("recommended", False)]
        
        # Should have 4 recommended operations
        assert len(recommended) == 4, f"Expected 4 recommended operations, got {len(recommended)}"

    def test_category_distribution(self, api):
        """Test that operations are distributed across categories."""
        operations = api.get_operations()
        
        # Group by category
        categories = {}
        for op in operations:
            cat = op.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        # Should have multiple categories
        assert len(categories) >= 4, "Should have at least 4 categories"
        
        # Sum should equal total
        assert sum(categories.values()) == len(operations)


class TestOperationSafety:
    """Tests for operation safety classifications."""

    @pytest.fixture
    def api(self):
        """Create MaintenanceAPI instance."""
        return MaintenanceAPI()

    def test_safe_operations_flagged(self, api):
        """Test that safe operations are properly flagged."""
        operations = api.get_operations()
        
        for op in operations:
            assert "safe" in op, f"Operation {op.get('id')} missing safe flag"
            assert isinstance(op["safe"], bool)

    def test_reports_are_safe(self, api):
        """Test that report operations are marked as safe."""
        operations = api.get_operations()
        reports = [op for op in operations if "report" in op.get("id", "").lower()]
        
        for op in reports:
            assert op.get("safe", False), f"Report operation {op.get('id')} should be safe"


class TestOperationIDs:
    """Tests for operation ID consistency."""

    @pytest.fixture
    def api(self):
        """Create MaintenanceAPI instance."""
        return MaintenanceAPI()

    def test_all_operations_have_unique_ids(self, api):
        """Test that all operation IDs are unique."""
        operations = api.get_operations()
        ids = [op.get("id") for op in operations]
        
        assert len(ids) == len(set(ids)), "Operation IDs must be unique"

    def test_operation_ids_are_kebab_case(self, api):
        """Test that operation IDs follow kebab-case convention."""
        operations = api.get_operations()
        
        for op in operations:
            op_id = op.get("id", "")
            # Should not have spaces or underscores
            assert " " not in op_id, f"Operation ID '{op_id}' contains spaces"
            # Should be lowercase
            assert op_id == op_id.lower(), f"Operation ID '{op_id}' not lowercase"
