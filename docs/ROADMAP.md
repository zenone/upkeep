# Upkeep Roadmap (Operator-Focused)

This is a living backlog of high-value maintenance capabilities to add.

## Recently added (implemented)

- **messages-cache**: Clear Messages cache/preview files (not chat history)
- **wallpaper-aerials**: Remove downloaded macOS Aerial wallpaper videos

## Next high-value operations (proposed)

### Disk space (safe-by-default)

1) **ios-backups-report** (read-only)
   - Detect and size `~/Library/Application Support/MobileSync/Backup`
   - Output: top backups by size + last modified
   - Deletion should remain manual via Finder “Manage Backups…”

2) **application-support-report** (read-only)
   - Size top-level folders under `~/Library/Application Support`
   - Highlight common large buckets (DAWs, browsers, chat apps)
   - Provide “ask-first” warnings for likely user data (sample libraries, project caches)

3) **messages-attachments-report** (read-only)
   - Size `~/Library/Messages/Attachments`
   - Show largest subfolders
   - Deletion is sensitive; keep as report-only unless explicitly requested

4) **mail-size-report** (read-only)
   - Size `~/Library/Mail` and major subfolders
   - Pair with existing `mail-optimize`

5) **cloudstorage-report** (read-only)
   - Size `~/Library/CloudStorage` and major providers
   - Explicitly warn: do not delete provider-managed storage directly

6) **disk-triage** (read-only)
   - One command that runs `df -h` + `du` drill-downs for:
     - `~/Library`
     - `~/Library/Application Support`
     - `~/Library/Caches`
     - `~/Library/Messages`
     - `~/Library/Mail`
   - Output a concise “top offenders” summary

### Safety / UX improvements

- Add UI affordances for **preview-only** / **dry-run** for cleanup ops.
- Add typed-confirmation gates for large deletions (already done for several ops; expand consistently).
- Add an “ask-first” classification so the UI can warn when an operation may touch user content.
