# Historical Trend Tracking Design

Track health score and disk usage over time to visualize system maintenance patterns.

---

## Goals

1. **Track**: Record health metrics at regular intervals
2. **Visualize**: Display trends as line charts in the Web UI
3. **Alert**: Detect negative trends (disk filling up, health declining)
4. **Retention**: Keep data compact while preserving long-term insights

---

## Data Model

### TrendDataPoint

```typescript
interface TrendDataPoint {
  timestamp: string;       // ISO 8601, UTC
  healthScore: number;     // 0-100 (from health gauge)
  diskUsed: number;        // bytes
  diskTotal: number;       // bytes
  diskFreePercent: number; // 0-100
  cacheSize: number;       // bytes (Application Support, Caches, Containers)
  trashSize: number;       // bytes
  logSize: number;         // bytes
}
```

### Storage Schema (SQLite)

```sql
CREATE TABLE IF NOT EXISTS trends (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,       -- ISO 8601 UTC
  health_score REAL NOT NULL,    -- 0-100
  disk_used INTEGER NOT NULL,    -- bytes
  disk_total INTEGER NOT NULL,   -- bytes
  disk_free_percent REAL NOT NULL,
  cache_size INTEGER NOT NULL,
  trash_size INTEGER NOT NULL,
  log_size INTEGER NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trends_timestamp ON trends(timestamp);
```

---

## Retention Policy

### Recording Schedule

| Resolution | Frequency | Retention |
|------------|-----------|-----------|
| High       | Every 4 hours | 7 days |
| Daily      | 1x/day (midnight) | 90 days |
| Weekly     | 1x/week (Sunday) | 1 year |
| Monthly    | 1x/month (1st) | Forever |

### Compaction Strategy

```
Day 1-7:    Keep all high-res (42 points max)
Day 8-90:   Keep daily summaries (83 points max)
Day 91-365: Keep weekly summaries (39 points max)
Year 2+:    Keep monthly summaries (12/year)
```

**Total storage**: ~200-300 points per year after year 1. Minimal disk footprint.

### Compaction Logic

```python
def compact_old_data():
    """Run weekly to downsample older data."""
    now = datetime.utcnow()
    
    # Remove high-res older than 7 days (keep daily)
    cutoff_7d = now - timedelta(days=7)
    
    # Remove daily older than 90 days (keep weekly)
    cutoff_90d = now - timedelta(days=90)
    
    # Remove weekly older than 365 days (keep monthly)
    cutoff_365d = now - timedelta(days=365)
```

---

## Backend Implementation

### TrendRecorder Class

```python
# src/upkeep/core/trend_recorder.py

class TrendRecorder:
    """Record and retrieve historical trend data."""
    
    def __init__(self, db_path: Path | None = None):
        """Initialize with optional custom DB path."""
        self.db_path = db_path or self._default_db_path()
        self._init_db()
    
    @staticmethod
    def _default_db_path() -> Path:
        """~/.upkeep/trends.db"""
        return Path.home() / ".upkeep" / "trends.db"
    
    def record_snapshot(self) -> TrendDataPoint:
        """Capture current system state and store it."""
        pass
    
    def get_range(
        self, 
        start: datetime, 
        end: datetime,
        resolution: Literal["all", "daily", "weekly", "monthly"] = "all"
    ) -> list[TrendDataPoint]:
        """Retrieve data points in time range."""
        pass
    
    def get_latest(self, count: int = 30) -> list[TrendDataPoint]:
        """Get most recent N data points."""
        pass
    
    def compact(self) -> int:
        """Run compaction. Returns number of rows removed."""
        pass
    
    def stats(self) -> dict:
        """Return DB statistics (row count, date range, size)."""
        pass
```

### Integration with Health Gauge

```python
def record_snapshot(self) -> TrendDataPoint:
    """Capture current system state."""
    # Re-use existing health calculation
    from upkeep.core.health_score import calculate_health_score
    from upkeep.core.disk_scanner import DiskScanner
    
    health = calculate_health_score()
    disk = DiskScanner().get_root_usage()
    
    # Calculate cache/trash/log sizes
    cache_size = sum_directory(Path.home() / "Library" / "Caches")
    trash_size = sum_directory(Path.home() / ".Trash")
    log_size = sum_directory(Path.home() / "Library" / "Logs")
    
    point = TrendDataPoint(
        timestamp=datetime.utcnow().isoformat() + "Z",
        healthScore=health.score,
        diskUsed=disk.used,
        diskTotal=disk.total,
        diskFreePercent=disk.free_percent,
        cacheSize=cache_size,
        trashSize=trash_size,
        logSize=log_size
    )
    
    self._store(point)
    return point
```

---

## REST API

### Endpoints

```
GET /api/trends
  Query params:
    - days: int (default: 30) — days of history
    - resolution: "all"|"daily"|"weekly"|"monthly" (default: auto)
  Response: { points: TrendDataPoint[], stats: { count, oldest, newest } }

POST /api/trends/record
  Description: Manually trigger a snapshot
  Response: { point: TrendDataPoint, message: "Recorded" }

POST /api/trends/compact
  Description: Run compaction
  Response: { removed: int, remaining: int }

GET /api/trends/stats
  Response: { rowCount, oldestDate, newestDate, dbSizeBytes }
```

### Auto-Recording

The Web UI server should auto-record a snapshot when started (if >4 hours since last).

```python
@app.on_event("startup")
async def startup_record():
    recorder = TrendRecorder()
    last = recorder.get_latest(1)
    if not last or (datetime.utcnow() - last[0].timestamp) > timedelta(hours=4):
        recorder.record_snapshot()
```

---

## Frontend Implementation

### Chart Component

Use Chart.js (already available for potential use) or lightweight alternative.

```typescript
// web/src/components/TrendsChart.tsx

interface TrendsChartProps {
  days: number;
  metric: "health" | "disk" | "cache";
}

function TrendsChart({ days, metric }: TrendsChartProps) {
  const { data, loading } = useFetch(`/api/trends?days=${days}`);
  
  // Map metric to data series
  const series = useMemo(() => {
    if (!data) return [];
    return data.points.map(p => ({
      x: new Date(p.timestamp),
      y: metric === "health" ? p.healthScore 
         : metric === "disk" ? p.diskFreePercent
         : p.cacheSize / 1e9  // GB
    }));
  }, [data, metric]);
  
  return (
    <LineChart 
      data={series}
      yLabel={metric === "health" ? "Score" : "GB"}
      color={metric === "health" ? "#22c55e" : "#3b82f6"}
    />
  );
}
```

### UI Location

Add "Trends" tab in the web UI sidebar, after "Disk" tab:

```
📊 Dashboard
💾 Disk
🗑️ Uninstaller
📈 Trends        <-- NEW
🔧 Settings
```

### Trend Alerts

When rendering, detect concerning patterns:

```typescript
function detectTrend(points: TrendDataPoint[]): "stable" | "improving" | "declining" {
  if (points.length < 7) return "stable";
  
  const recent = points.slice(-7);
  const older = points.slice(-14, -7);
  
  const recentAvg = average(recent.map(p => p.healthScore));
  const olderAvg = average(older.map(p => p.healthScore));
  
  const delta = recentAvg - olderAvg;
  if (delta > 5) return "improving";
  if (delta < -5) return "declining";
  return "stable";
}
```

Display trend indicator next to chart:
- 📈 Improving (green)
- ➡️ Stable (gray)
- 📉 Declining (orange/red)

---

## Testing Strategy

### Unit Tests

```python
# tests/test_trend_recorder.py

def test_record_snapshot(tmp_path):
    """Recording creates valid data point."""
    recorder = TrendRecorder(db_path=tmp_path / "test.db")
    point = recorder.record_snapshot()
    
    assert 0 <= point.healthScore <= 100
    assert point.diskTotal > 0
    assert point.timestamp.endswith("Z")

def test_get_range(tmp_path):
    """Range queries return correct data."""
    recorder = TrendRecorder(db_path=tmp_path / "test.db")
    # Insert test data
    # Query and verify

def test_compaction(tmp_path):
    """Compaction removes old high-res data."""
    recorder = TrendRecorder(db_path=tmp_path / "test.db")
    # Insert data spanning multiple periods
    # Run compact
    # Verify correct data retained
```

### Integration Tests

```python
def test_trends_api_endpoint(client):
    """API returns trend data."""
    response = client.get("/api/trends?days=7")
    assert response.status_code == 200
    data = response.json()
    assert "points" in data
    assert "stats" in data
```

---

## Implementation Plan

| Slice | Task | Tests |
|-------|------|-------|
| 1 | Design doc (this file) | — |
| 2 | `TrendRecorder` class (record, get_latest, get_range) | 8-10 |
| 3 | Compaction logic | 4-5 |
| 4 | REST API endpoints | 4-5 |
| 5 | Chart.js integration | Manual |
| 6 | Trends tab UI | Manual |
| 7 | Auto-recording on server start | 1-2 |

**Estimated total: 7 slices**

---

## Constraints

- **Privacy**: All data stays local (~/.upkeep/trends.db)
- **Performance**: Recording should complete in <5 seconds
- **Footprint**: DB should stay under 1MB even after years of data
- **Compatibility**: SQLite 3.x (ships with macOS)

---

## Open Questions

1. Should we also track per-operation history (when each cleanup ran)?
   - *Decision*: Defer to v3.2. Focus on aggregate metrics first.

2. Should compaction run automatically or require user action?
   - *Decision*: Auto-compact on first startup of each week.

3. Export trends to CSV?
   - *Decision*: Nice-to-have. Add to roadmap after basic implementation.
