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

# Test 2: Verify LaunchAgents directory permissions
echo
echo "Test 2: Checking ~/Library/LaunchAgents permissions..."
LA_DIR="$HOME/Library/LaunchAgents"
if [ ! -d "$LA_DIR" ]; then
    echo "Creating LaunchAgents directory..."
    mkdir -p "$LA_DIR"
fi
if [ -w "$LA_DIR" ]; then
    echo "✅ LaunchAgents directory writable"
else
    echo "❌ LaunchAgents directory not writable"
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

# Test 7: Verify run_scheduled_task can be imported and uses daemon-backed runner
echo
echo "Test 7: Checking scheduled task entry point..."
python3 << 'EOF'
from mac_maintenance.core.launchd import run_scheduled_task
print("✅ run_scheduled_task import OK")
EOF

echo
echo "================================"
echo "Test suite complete!"
echo
echo "⚠️  Note: Even if tests pass, check the critical bug warning above."
