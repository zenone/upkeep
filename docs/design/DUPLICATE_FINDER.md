# Duplicate File Finder Design

## Goal
Provide a **safe-by-default** duplicate file finder for macOS that identifies redundant files consuming disk space, with a focus on user control and preventing accidental data loss. The key principle: **identify, never auto-delete**.

## User Stories
1. **Scan**: User initiates a scan of a directory (default: home folder or selected paths).
2. **Review**: User views grouped duplicates, sorted by space savings potential.
3. **Compare**: User can preview/compare duplicate files before deciding.
4. **Select**: User manually selects which copies to remove (never automatic).
5. **Action**: User moves selected files to Trash (safe delete) or excludes from future scans.

## Design Principles
- **Safe by Default**: Never auto-delete. Always require explicit user confirmation.
- **Transparent**: Show exactly why files are considered duplicates (size + hash).
- **Efficient**: Use multi-stage filtering to minimize expensive hash operations.
- **Respectful**: Skip system files, dotfiles (configurable), and protected locations.

## Architecture

### 1. Multi-Stage Filtering Pipeline
The key to efficient duplicate detection is minimizing disk I/O. We use a funnel approach:

```
Stage 1: Size Grouping
    ↓ (files with unique sizes eliminated)
Stage 2: Partial Hash (first 64KB)
    ↓ (files with unique partial hashes eliminated)
Stage 3: Full Hash (SHA-256)
    ↓ (confirmed duplicates)
```

**Why This Works:**
- Stage 1 eliminates ~80-90% of files (most files have unique sizes)
- Stage 2 eliminates another ~5-10% (same size, different content)
- Stage 3 only runs on true candidates (~1-5% of original set)

### 2. `DuplicateScanner` Service
Core scanning logic with progress reporting.

**API Contract:**

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Optional, Callable
from enum import Enum

class HashAlgorithm(Enum):
    SHA256 = "sha256"
    XXHASH = "xxhash64"  # Faster, good for non-cryptographic use

@dataclass
class FileInfo:
    path: Path
    size_bytes: int
    partial_hash: Optional[str] = None  # First 64KB
    full_hash: Optional[str] = None
    mtime: float = 0  # Modification time (for "keep newest" heuristics)

@dataclass
class DuplicateGroup:
    hash: str
    size_bytes: int
    files: List[FileInfo]
    
    @property
    def potential_savings(self) -> int:
        """Space recoverable if all but one copy removed."""
        return self.size_bytes * (len(self.files) - 1)

@dataclass
class ScanConfig:
    paths: List[Path]                    # Directories to scan
    min_size_bytes: int = 1024           # Skip files < 1KB (not worth it)
    max_size_bytes: Optional[int] = None # Optional upper limit
    include_hidden: bool = False         # Skip dotfiles by default
    follow_symlinks: bool = False        # Safety: don't follow symlinks
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "*.app/*",           # Don't scan inside app bundles
        "node_modules/*",    # Common dev bloat (handle separately)
        ".git/*",            # Git internals
        "*.vmdk", "*.iso",   # Large disk images (too slow)
    ])
    hash_algorithm: HashAlgorithm = HashAlgorithm.SHA256

@dataclass
class ScanResult:
    duplicate_groups: List[DuplicateGroup]
    total_files_scanned: int
    total_duplicates: int
    total_wasted_bytes: int
    scan_duration_seconds: float
    errors: List[str]  # Files that couldn't be read

class DuplicateScanner:
    def __init__(self, config: ScanConfig):
        self.config = config
    
    def scan(
        self, 
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> ScanResult:
        """
        Execute full scan pipeline.
        
        progress_callback receives: (stage_name, current, total)
        """
        ...
    
    def scan_incremental(self, previous_result: ScanResult) -> ScanResult:
        """
        Efficient re-scan using cached hashes for unchanged files.
        Compares mtime to detect changes.
        """
        ...
```

### 3. `DuplicateReporter` Service
Generates reports in various formats.

**API Contract:**

```python
class DuplicateReporter:
    def to_json(self, result: ScanResult) -> str:
        """JSON output for API/UI consumption."""
        ...
    
    def to_text(self, result: ScanResult) -> str:
        """Human-readable text report."""
        ...
    
    def to_csv(self, result: ScanResult) -> str:
        """CSV export for spreadsheet analysis."""
        ...
```

### 4. Safety Guardrails

**Protected Paths (Never Include in Deletion Candidates):**
```python
PROTECTED_PATHS = [
    Path.home() / "Library" / "Keychains",
    Path.home() / "Library" / "Mail",
    Path("/System"),
    Path("/usr"),
    Path("/bin"),
    Path("/sbin"),
    Path("/Applications"),  # .app bundles themselves
]
```

**Deletion Safety:**
- Always use Trash (`send2trash`), never `rm`
- Require explicit confirmation for files > 100MB
- Show preview of each file before deletion option
- Never delete the "last copy" — at least one must remain

### 5. REST API

```
GET /api/duplicates/scan
  Query params:
    - paths: comma-separated paths (default: ~)
    - min_size_mb: minimum file size (default: 0.001)
    - include_hidden: boolean (default: false)
  Response: { scan_id: string, status: "started" }

GET /api/duplicates/status/{scan_id}
  Response: { status: "running"|"complete", progress: { stage, current, total } }

GET /api/duplicates/results/{scan_id}
  Response: ScanResult as JSON

POST /api/duplicates/delete
  Body: { scan_id: string, paths: string[] }
  Response: { deleted: string[], errors: string[] }
```

## CLI Interface

```bash
# Basic scan of home directory
upkeep duplicates

# Scan specific paths
upkeep duplicates ~/Documents ~/Downloads

# Output as JSON
upkeep duplicates --json

# Minimum size filter
upkeep duplicates --min-size 1MB

# Include hidden files
upkeep duplicates --include-hidden

# Interactive mode (prompts for each group)
upkeep duplicates --interactive
```

## Web UI

### List View
- Table of duplicate groups, sorted by `potential_savings` (largest first)
- Columns: Preview (icon/thumbnail), Hash, Count, Size Each, Total Wasted
- Click group to expand and see individual files

### Detail View (Expanded Group)
- List of all duplicate files in the group
- For each file: path, modification date, size
- Preview pane (Quick Look integration for images/text)
- Radio buttons or checkboxes to select files to keep/delete
- "Keep Newest" / "Keep Oldest" / "Keep by Path" quick actions

### Action Panel
- "Move to Trash" button (disabled until selection made)
- Confirmation modal: "You are about to move X files (Y MB) to Trash. This can be undone from Trash."
- Progress indicator during deletion

### Settings
- Exclude patterns editor
- Minimum size slider
- Include/exclude hidden files toggle
- Hash algorithm selection (SHA-256 for accuracy, xxHash for speed)

## Implementation Plan (TDD)

### Phase 1: Core Scanner (Backend)
1. Implement `FileInfo` and `DuplicateGroup` dataclasses
2. Implement size-grouping stage with tests
3. Implement partial hash stage with tests
4. Implement full hash stage with tests
5. Integration test with fixture directory

### Phase 2: Reporter (Backend)
1. Implement JSON output
2. Implement text output
3. Implement CSV export

### Phase 3: API (Backend)
1. Implement scan endpoint (async with progress)
2. Implement status/results endpoints
3. Implement delete endpoint with safety checks

### Phase 4: CLI
1. Add `duplicates` subcommand
2. Implement argument parsing
3. Add interactive mode

### Phase 5: Web UI
1. Create DuplicateFinder tab/component
2. Implement scan trigger and progress UI
3. Implement results table with expandable groups
4. Implement selection and deletion flow

## Performance Considerations

**For Large Directories (100K+ files):**
- Use `os.scandir()` instead of `os.walk()` for memory efficiency
- Stream results to UI during scan (don't wait for completion)
- Consider SQLite for caching hashes between scans
- xxHash (~10x faster) for initial comparison, SHA-256 for final verification

**Memory Management:**
- Don't load file contents into memory; hash in chunks
- Limit concurrent file handles
- Use generators for file iteration

## Future Enhancements (P2+)

1. **Smart Grouping**: Group duplicates by location (e.g., "all in Downloads")
2. **Duplicate Watch**: Background daemon that alerts when new duplicates appear
3. **Similar Files**: Fuzzy matching for images (perceptual hash) and documents
4. **Scheduled Scans**: Cron integration for weekly duplicate reports
5. **Cloud Integration**: Detect files that exist both locally and in iCloud/Dropbox
