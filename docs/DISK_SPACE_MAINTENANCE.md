# Disk Space Maintenance (Safe Defaults)

This guide documents **safe, high-signal disk space recovery steps** for macOS.

Upkeep’s philosophy is **safe by default**. These actions are chosen because they are generally low-risk and reversible (or re-creatable), and they avoid deleting user content.

## Quick checklist (lowest regret)

1. **Empty Trash** (Finder)
2. **Review Downloads** (Finder)
   - Sort by size; remove old DMGs/ZIPs/installers.
3. **Homebrew cleanup**
   ```bash
   brew cleanup -s
   rm -rf ~/Library/Caches/Homebrew/*
   ```
4. **Package manager caches** (re-creatable)
   ```bash
   rm -rf ~/Library/Caches/pip
   rm -rf ~/Library/Caches/pnpm
   rm -rf ~/.npm/_cacache
   rm -rf ~/Library/Caches/Yarn
   rm -rf ~/Library/Caches/node-gyp
   ```
5. **Xcode DerivedData** (if you use Xcode)
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData/*
   ```
6. **Messages caches** (often huge)
   ```bash
   rm -rf ~/Library/Messages/Caches
   ```

7. **macOS Aerial wallpapers** (can be tens of GB)

   If you don’t need offline Apple TV-style Aerial videos:

   ```bash
   rm -rf "~/Library/Application Support/com.apple.wallpaper/aerials/videos"
   ```

8. **Time Machine local snapshots** (often a big win)
   ```bash
   tmutil listlocalsnapshots /
   sudo tmutil thinlocalsnapshots / 30000000000 4
   ```

## How to find what’s actually big (recommended)

Run:

```bash
# Overall free space
DF_OUTPUT=$(df -h / | sed -n '1,2p'); echo "$DF_OUTPUT"

# Largest top-level directories in your home folder
sudo du -xhd 1 ~ 2>/dev/null | sort -h | tail -20
```

Then drill into the biggest directories:

```bash
sudo du -xhd 1 ~/Library 2>/dev/null | sort -h | tail -20
```

## Notes / guardrails

- Avoid deleting things you can’t easily recreate.
- Prefer deleting **caches** and **derived build artifacts** first.
- If you need to delete application data, use the app’s own UI when possible.
- If you keep large “cold storage” media, consider moving it to an external drive.
