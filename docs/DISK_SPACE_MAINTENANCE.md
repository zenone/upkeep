# Disk Space Maintenance (Safe Defaults)

This guide documents **safe, high-signal disk space recovery steps** for macOS.

Upkeep's philosophy is **safe by default**. These actions are chosen because they are generally low-risk and reversible (or re-creatable), and they avoid deleting user content.

---

## Quick Reference: The Drill-Down Method

**Step 1: Baseline**
```bash
df -h /
```

**Step 2: Find what's big (top-level)**
```bash
sudo du -xhd 1 "$HOME" 2>/dev/null | sort -h | tail -20
```

**Step 3: Drill into Library (usually the culprit)**
```bash
sudo du -xhd 1 "$HOME/Library" 2>/dev/null | sort -h | tail -25
```

**Step 4: Drill into Application Support**
```bash
sudo du -xhd 1 "$HOME/Library/Application Support" 2>/dev/null | sort -h | tail -20
```

**Step 5: Drill into Caches**
```bash
sudo du -xhd 1 "$HOME/Library/Caches" 2>/dev/null | sort -h | tail -20
```

**Step 6: Verify results**
```bash
df -h /
```

---

## Safe Cleanup Checklist (Lowest Regret)

### 1. Empty Trash
Via Finder, or:
```bash
rm -rf "$HOME/.Trash"/*
```

### 2. Review Downloads
Sort by size; remove old DMGs/ZIPs/installers:
```bash
ls -lhS "$HOME/Downloads" | head -30
```

### 3. Homebrew cleanup
```bash
brew cleanup -s
rm -rf "$HOME/Library/Caches/Homebrew"/*
```

### 4. Package manager caches (re-creatable)
```bash
rm -rf "$HOME/Library/Caches/pip"
rm -rf "$HOME/Library/Caches/pnpm"
rm -rf "$HOME/.npm/_cacache"
rm -rf "$HOME/Library/Caches/Yarn"
rm -rf "$HOME/Library/Caches/node-gyp"
```

### 5. Xcode DerivedData (if you use Xcode)
```bash
rm -rf "$HOME/Library/Developer/Xcode/DerivedData"/*
```
**Typical size**: 5-50GB for active iOS developers

### 6. Xcode iOS Device Support (optional, will re-download)
```bash
rm -rf "$HOME/Library/Developer/Xcode/iOS DeviceSupport"/*
```
**Typical size**: 5-30GB

### 7. Messages caches (not chat history)
```bash
rm -rf "$HOME/Library/Messages/Caches"
```
**Typical size**: 1-10GB

### 8. macOS Aerial wallpapers
If you don't need offline Apple TV-style Aerial videos:
```bash
rm -rf "$HOME/Library/Application Support/com.apple.wallpaper/aerials/videos"
```
**Typical size**: 10-40GB (yes, really!)

### 9. General user caches
```bash
rm -rf "$HOME/Library/Caches"/*
```
**Note**: Apps will rebuild caches as needed. This is safe but some apps may feel slower briefly.

### 10. Old logs
```bash
find "$HOME/Library/Logs" -type f -mtime +30 -delete
```

### 11. Time Machine local snapshots
```bash
# List snapshots
tmutil listlocalsnapshots /

# Thin to target (e.g., 30GB)
sudo tmutil thinlocalsnapshots / 30000000000 4
```
**Typical size**: 5-50GB

---

## Common Large Offenders (Inspect Before Deleting)

| Location | Typical Size | Safe to Delete? |
|----------|-------------|-----------------|
| `~/Library/Caches` | 2-10GB | ✅ Yes (regenerates) |
| `~/Library/Messages/Caches` | 1-10GB | ✅ Yes (not chat history) |
| `~/Library/Developer/Xcode/DerivedData` | 5-50GB | ✅ Yes (build cache) |
| `~/Library/Application Support/com.apple.wallpaper/aerials/videos` | 10-40GB | ✅ Yes (re-downloads) |
| `~/Library/Application Support/MobileSync/Backup` | 10-100GB | ⚠️ Use Finder to manage |
| `~/Library/Messages/Attachments` | 5-50GB | ⚠️ Personal data — report only |
| `~/Library/Mail` | 5-50GB | ⚠️ Use Mail.app to manage |
| `~/Library/CloudStorage` | 50-500GB | ❌ NEVER delete directly |
| `~/VirtualBox VMs` | 5-100GB | ⚠️ Use VirtualBox UI |
| `~/Library/Application Support` (general) | 50-200GB | ⚠️ Varies — inspect first |

---

## DO NOT Delete Blindly

### `~/Library/CloudStorage`
This is managed by cloud providers (Dropbox, iCloud, Google Drive). Deleting files here can cause sync issues or data loss.

**Instead**: Use provider settings to make folders "online-only" or move cold data to external storage.

### `~/Library/Messages/Attachments`
This contains your actual message attachments. Deleting may lose photos/files from conversations.

**Instead**: Use the Messages app to manage, or accept the space usage.

### `~/Library/Mail`
Contains your email data. Deleting can cause Mail.app to re-download or lose local-only mail.

**Instead**: Use Mail.app to delete old emails, remove large attachments, or archive old mailboxes.

### `~/Library/Application Support/MobileSync/Backup`
Contains iPhone/iPad backups. Deleting the wrong backup loses restore points.

**Instead**: Use Finder → iPhone → Manage Backups… to delete specific backups.

---

## Docker Users

Docker can consume 20-100GB in images, containers, and volumes:
```bash
# See usage
docker system df

# Prune unused (keeps running containers)
docker system prune -a --volumes
```

---

## Developer Artifacts

For active developers, these accumulate across projects:
```bash
# Find node_modules (can be huge)
find "$HOME" -name "node_modules" -type d -prune 2>/dev/null | head -20

# Find Python venvs
find "$HOME" -name ".venv" -type d -prune 2>/dev/null | head -20
```

**Cleanup**: Delete only from projects you're not actively working on.

---

## Verification

Always run `df -h /` before and after cleanup to confirm space was freed.

Example session:
```bash
# Before
$ df -h /
Filesystem   Size   Used  Avail  Use%
/dev/disk1  500G   450G    50G   90%

# After cleanup
$ df -h /
Filesystem   Size   Used  Avail  Use%
/dev/disk1  500G   380G   120G   76%
```
