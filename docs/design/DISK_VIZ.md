# Disk Visualization Design Doc (v1.0)

**Goal:** Provide a stunning, interactive visualization of disk usage to help users identify space hogs quickly.

**Type:** Zoomable Treemap or Sunburst chart.
**Library:** D3.js (v7) - Industry standard for custom data viz.
**Data Source:** `du` command (optimized).

## Architecture

### 1. Backend (`src/upkeep/core/disk_scanner.py`)

*   **Class**: `DiskScanner`
*   **Method**: `scan(path: str, depth: int = 3) -> Dict`
*   **Command**: `du -k -d 3 <path>` (kilobytes, max depth 3 to start)
*   **Output Format**: Hierarchical JSON (Flare format compatible with D3).

```json
{
  "name": "root",
  "children": [
    { "name": "Applications", "value": 15000000 },
    { "name": "Users", "children": [ ... ] }
  ]
}
```

### 2. API (`src/upkeep/web/routes.py`)

*   **Endpoint**: `GET /api/disk/usage?path=/&depth=3`
*   **Response**: JSON above.
*   **Caching**: Cache results for 5-10 minutes (disk usage doesn't change instantly).

### 3. Frontend (`src/upkeep/web/static/js/viz.js` or similar)

*   **Component**: `DiskTreemap`
*   **Interaction**: Click to zoom in (fetch deeper data if needed).
*   **Color Scale**: Categorical (App, User, System) or Heatmap (Size).
*   **Tooltip**: Path, Size (human readable), Percentage of parent.

## UX Flow

1.  User clicks "Disk Usage" tab.
2.  Loader appears ("Scanning disk structure...").
3.  Treemap renders with top-level folders.
4.  Hovering shows details.
5.  Clicking a box zooms into that folder.

## Technical Constraints

*   **Performance**: `du` can be slow on full disk. Limit depth initially (depth=2 or 3).
*   **Permissions**: Running as user vs root affects visibility. Show warning if permission denied.
*   **Safety**: Read-only visualization first. Deletion via "Reveal in Finder" or specific actions later.

## Implementation Plan

1.  **Backend**: Implement `DiskScanner` with tests.
2.  **API**: Expose scanner via Flask/API.
3.  **Frontend**: Integrate D3.js and build basic Treemap.
4.  **Polish**: Transitions, colors, tooltips.
