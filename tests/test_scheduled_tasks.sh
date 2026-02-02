#!/bin/bash
# Test script for scheduled tasks system
# Run this to verify scheduling will work before creating real schedules

set -e

echo "🧪 Scheduled Tasks Test Suite"
echo "================================"
echo

# Test 1: Check if run_schedule.py exists and is executable
echo "Test 1: Checking run_schedule.py..."
if [ -f "src/mac_maintenance/scripts/run_schedule.py" ]; then
    echo "✅ run_schedule.py found"
else
    echo "❌ run_schedule.py missing"
    exit 1
fi

# Test 2: Verify LaunchDaemons directory permissions
echo
echo "Test 2: Checking /Library/LaunchDaemons permissions..."
if [ -d "/Library/LaunchDaemons" ] && [ -w "/Library/LaunchDaemons" ]; then
    echo "✅ LaunchDaemons directory writable"
elif [ -d "/Library/LaunchDaemons" ]; then
    echo "⚠️  LaunchDaemons exists but not writable (need sudo)"
else
    echo "❌ LaunchDaemons directory doesn't exist"
    exit 1
fi

# Test 3: Check log directory
echo
echo "Test 3: Checking log directory..."
LOG_DIR="$HOME/.mac-maintenance/logs"
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory..."
    mkdir -p "$LOG_DIR"
fi
if [ -w "$LOG_DIR" ]; then
    echo "✅ Log directory writable"
else
    echo "❌ Log directory not writable"
    exit 1
fi

# Test 4: Verify Python can import required modules
echo
echo "Test 4: Testing Python imports..."
python3 << 'EOF'
try:
    from mac_maintenance.api.schedule import ScheduleAPI
    from mac_maintenance.api.maintenance import MaintenanceAPI
    from mac_maintenance.core.launchd import LaunchdGenerator
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)
EOF

# Test 5: Test schedule creation (in-memory only)
echo
echo "Test 5: Testing schedule creation..."
python3 << 'EOF'
from mac_maintenance.api.schedule import ScheduleAPI
from datetime import time

api = ScheduleAPI()
result = api.create_schedule({
    "name": "Test Schedule",
    "description": "Test only",
    "operations": ["brew-update"],
    "frequency": "daily",
    "time_of_day": time(2, 0),
    "enabled": False  # Disabled so it won't actually run
})

if result.success:
    print(f"✅ Schedule created: {result.schedule.id}")
    # Clean up
    api.delete_schedule(result.schedule.id)
    print("✅ Schedule deleted")
else:
    print(f"❌ Schedule creation failed: {result.error}")
    exit(1)
EOF

# Test 6: Test plist generation
echo
echo "Test 6: Testing plist generation..."
python3 << 'EOF'
from mac_maintenance.core.launchd import LaunchdGenerator
from mac_maintenance.api.models.schedule import ScheduleConfig, ScheduleFrequency
from datetime import time

gen = LaunchdGenerator()
schedule = ScheduleConfig(
    id="schedule-test123",
    name="Test",
    description="Test",
    operations=["brew-update"],
    frequency=ScheduleFrequency.DAILY,
    time_of_day=time(2, 0),
    enabled=False
)

plist = gen.generate_plist(schedule)
if "Label" in plist and "ProgramArguments" in plist:
    print("✅ Plist generation successful")
    print(f"   Label: {plist['Label']}")
else:
    print("❌ Plist generation failed")
    exit(1)
EOF

# Test 7: CRITICAL - Check for execute_operation method bug
echo
echo "Test 7: Checking for known bug (execute_operation)..."
python3 << 'EOF'
from mac_maintenance.api.maintenance import MaintenanceAPI

api = MaintenanceAPI()
if hasattr(api, 'execute_operation'):
    print("✅ execute_operation method exists")
else:
    print("❌ CRITICAL BUG: execute_operation method missing!")
    print("   Scheduled tasks will FAIL to execute!")
    print("   This needs to be fixed before using schedules.")
    exit(1)
EOF

echo
echo "================================"
echo "Test suite complete!"
echo
echo "⚠️  Note: Even if tests pass, check the critical bug warning above."
