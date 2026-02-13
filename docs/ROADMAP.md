# Upkeep Roadmap (Operator-Focused)

This is a living backlog of high-value maintenance capabilities to add.

**Philosophy**: Report operations (read-only visibility) precede cleanup operations (destructive). Safe-by-default. Confirmation gates for anything that deletes user data.

---

## Implemented Operations

| Operation | Type | Description | Added |
|-----------|------|-------------|-------|
| `messages-cache` | CLEANUP | Clear Messages cache/preview files (not chat history) | 2026-02 |
| `wallpaper-aerials` | CLEANUP | Remove downloaded macOS Aerial wallpaper videos | 2026-02 |

---

## Tier 1: High Impact, Low Risk (Implement First)

These are the "golden" operations — high space savings, low regret, work on any Mac.

### 1. `disk-triage` (REPORT)
**WHY**: "What's using my disk?" is the first question. This answers it.
**WHAT**: Runs `df -h` + `du -xhd 1` on `$HOME`, `$HOME/Library`, and key subfolders. Outputs ranked "top offenders" summary.
**WHEN**: Before any cleanup. Weekly health check. After "disk full" alerts.

**Target Paths**:
- `$HOME` (top-level breakdown)
- `$HOME/Library`
- `$HOME/Library/Application Support`
- `$HOME/Library/Caches`
- `$HOME/Library/Messages`
- `$HOME/Library/Mail`

**Output**: Human-readable table, sorted by size descending.

---

### 2. `downloads-report` (REPORT) + `downloads-cleanup` (CLEANUP)
**WHY**: Downloads accumulate installers/archives that are often forgotten.
**WHAT**: 
- Report: Size and age of files in `$HOME/Downloads`, sorted by size
- Cleanup: Remove `.dmg`, `.zip`, `.pkg`, `.iso` files older than N days (default: 30)

**WHEN**: Monthly. After big installs. When disk is tight.

**Safety**: Cleanup requires confirmation. Consider `--dry-run` flag.

---

### 3. `xcode-cleanup` (CLEANUP)
**WHY**: DerivedData is build cache; can grow to 50GB+ on active iOS devs.
**WHAT**: `rm -rf $HOME/Library/Developer/Xcode/DerivedData/*`
**WHEN**: Monthly for devs. Anytime disk is tight. After major Xcode updates.

**Dependencies**: None (gracefully skip if Xcode not installed)
**Typical Size**: 5-50GB

---

### 4. `caches-report` (REPORT) + `caches-cleanup` (CLEANUP)
**WHY**: `~/Library/Caches` is designed to be purgeable by the OS.
**WHAT**:
- Report: List top 20 cache folders by size
- Cleanup: `rm -rf $HOME/Library/Caches/*`

**WHEN**: Monthly. When disk is tight. Safe to run anytime.

**Note**: Some apps may need to rebuild caches on next launch — this is normal and expected.

---

### 5. `logs-cleanup` (CLEANUP)
**WHY**: Log files accumulate indefinitely; rarely needed after a few weeks.
**WHAT**: Remove logs older than 30 days from `$HOME/Library/Logs`
**WHEN**: Monthly maintenance.

**Typical Size**: 0.5-5GB

---

### 6. `trash-empty` (CLEANUP)
**WHY**: Trash can hold GBs of "deleted" files.
**WHAT**: `osascript -e 'tell app "Finder" to empty trash'` or `rm -rf $HOME/.Trash/*`
**WHEN**: Weekly or as part of any cleanup bundle.

---

## Tier 2: High Impact, Medium Risk

These require confirmation gates or have external dependencies.

### 7. `xcode-device-support` (CLEANUP)
**WHY**: iOS DeviceSupport caches old device versions; can be 20-30GB.
**WHAT**: `rm -rf $HOME/Library/Developer/Xcode/iOS\ DeviceSupport/*`
**WHEN**: After upgrading devices. Annually.

**Note**: Will re-download on next device connection. Confirm before deleting.

---

### 8. `timemachine-thin` (CLEANUP)
**WHY**: Local Time Machine snapshots can consume 10-50GB.
**WHAT**: 
```bash
tmutil listlocalsnapshots /
sudo tmutil thinlocalsnapshots / <target_bytes> 4
```
**WHEN**: When disk is critically low. Monthly maintenance.

**Dependencies**: `tmutil`, `sudo` access
**Risk**: Medium — deletes backup snapshots; only thin, don't purge all.

---

### 9. `docker-prune` (CLEANUP)
**WHY**: Docker images, containers, and volumes can consume 20-100GB.
**WHAT**: 
```bash
docker system prune -a --volumes
```
**WHEN**: Monthly for Docker users. When disk is tight.

**Dependencies**: `docker` command available
**Risk**: Medium — removes unused images/volumes; active containers preserved.

---

### 10. `ios-backups-report` (REPORT)
**WHY**: iPhone/iPad backups can be 10-100GB.
**WHAT**: Size `$HOME/Library/Application Support/MobileSync/Backup`, list backups by device and date.
**WHEN**: Quarterly. When disk is tight.

**Cleanup Recommendation**: Use Finder → iPhone → Manage Backups… (not CLI deletion)

---

## Tier 3: Visibility / Specialized

These provide visibility but cleanup should be manual or app-specific.

### 11. `application-support-report` (REPORT)
**WHY**: Application Support can be 50-200GB with app-specific data.
**WHAT**: Size top 20 folders under `$HOME/Library/Application Support`
**WHEN**: Quarterly exploration.

**Note**: DO NOT auto-delete. Many folders contain irreplaceable data (DAW projects, app databases, etc.)

---

### 12. `mail-size-report` (REPORT)
**WHY**: Mail data can grow to 10-50GB.
**WHAT**: Size `$HOME/Library/Mail` and major subfolders.
**WHEN**: Quarterly.

**Cleanup Recommendation**: Use Mail.app to manage mailboxes, delete attachments.

---

### 13. `messages-attachments-report` (REPORT)
**WHY**: Messages attachments can be 5-50GB.
**WHAT**: Size `$HOME/Library/Messages/Attachments`
**WHEN**: Quarterly.

**Note**: Sensitive personal data. Report-only unless user explicitly requests cleanup.

---

### 14. `cloudstorage-report` (REPORT)
**WHY**: CloudStorage (Dropbox, iCloud, Google Drive) can show 50-500GB.
**WHAT**: Size `$HOME/Library/CloudStorage` by provider.
**WHEN**: Informational.

**⚠️ WARNING**: NEVER delete from `~/Library/CloudStorage` directly. Use provider apps to make folders online-only or move data to external storage.

---

### 15. `virtualbox-report` (REPORT)
**WHY**: VirtualBox VMs can be 5-100GB each.
**WHAT**: Size `$HOME/VirtualBox VMs` and list VMs.
**WHEN**: When exploring large home directories.

**Cleanup Recommendation**: Use VirtualBox UI to remove VMs properly.

---

### 16. `dev-artifacts-report` (REPORT)
**WHY**: Development artifacts (node_modules, .venv, build/) pile up across projects.
**WHAT**: Find and size:
- `node_modules` directories
- `.venv` / `venv` directories
- `build` / `dist` / `target` directories

**WHEN**: Quarterly for developers.

**Note**: Manual cleanup recommended — verify project isn't active before deleting.

---

## Implementation Checklist (per operation)

For each new operation, ensure:
- [ ] Uses `$HOME` not hardcoded paths
- [ ] Checks dependencies (`command -v <cmd>` before using)
- [ ] Gracefully skips if target doesn't exist
- [ ] REPORT ops are pure read-only
- [ ] CLEANUP ops have confirmation gate (unless trivially safe)
- [ ] `df -h` verification before/after for CLEANUP ops
- [ ] Added to TEST_MATRIX.md
- [ ] WHY/WHAT/WHEN documented
- [ ] Works on fresh macOS install (no assumptions about installed apps)

---

## Bundle Ideas (Future)

| Bundle | Operations |
|--------|------------|
| `quick-clean` | `trash-empty`, `caches-cleanup`, `messages-cache` |
| `dev-clean` | `xcode-cleanup`, `brew-cleanup`, `package-cache-cleanup` |
| `deep-monthly` | All Tier 1 operations |
| `storage-recovery` | `disk-triage` → interactive cleanup based on findings |

---

## Out of Scope (for now)

- System-level cleanup (requires root, risky)
- Third-party app uninstallers
- Duplicate file finders (complex, many existing tools)
- Cloud backup management (provider-specific)
