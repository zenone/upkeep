# Menu Bar App Research

Research into creating a native macOS menu bar app for Upkeep.

---

## Goals

1. **Quick Access**: One-click access to health status and quick actions
2. **Background Monitoring**: Track system health without opening full UI
3. **Notifications**: Alert when maintenance is needed
4. **Minimal Footprint**: Low resource usage

---

## Options Evaluated

### 1. SwiftUI + AppKit (Native)

**Pros:**
- Native look and feel
- Best performance
- Full system integration (notifications, launchd)
- Access to all macOS APIs

**Cons:**
- Requires Xcode and Swift knowledge
- Separate build process from web app
- Code signing for distribution

**Implementation:**
```swift
import SwiftUI
import AppKit

@main
struct UpkeepMenuBarApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    var body: some Scene {
        Settings { }  // Empty - menu bar only
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem!
    var healthScore: Int = 0
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.title = "🔧 --"
        
        // Setup menu
        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "Health: --", action: nil, keyEquivalent: ""))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: "Open Upkeep", action: #selector(openWeb), keyEquivalent: "o"))
        menu.addItem(NSMenuItem(title: "Quick Maintenance", action: #selector(runQuick), keyEquivalent: "m"))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: "Quit", action: #selector(quit), keyEquivalent: "q"))
        statusItem.menu = menu
        
        // Start polling
        Timer.scheduledTimer(withTimeInterval: 300, repeats: true) { _ in
            self.updateHealth()
        }
        updateHealth()
    }
    
    @objc func updateHealth() {
        // Call upkeep API
        URLSession.shared.dataTask(with: URL(string: "http://localhost:8080/api/system/health")!) { data, _, _ in
            // Parse and update
        }.resume()
    }
    
    @objc func openWeb() {
        NSWorkspace.shared.open(URL(string: "http://localhost:8080")!)
    }
    
    @objc func runQuick() {
        // POST to maintenance endpoint
    }
    
    @objc func quit() {
        NSApplication.shared.terminate(nil)
    }
}
```

**Effort:** 2-3 days

---

### 2. Electron + Tray

**Pros:**
- Reuses web codebase
- Cross-platform potential
- Familiar tech stack

**Cons:**
- High memory usage (~100-200MB)
- Not truly native
- Slower startup

**Implementation:**
```javascript
const { app, Tray, Menu, nativeImage } = require('electron');
const path = require('path');

let tray = null;

app.whenReady().then(() => {
    const icon = nativeImage.createFromPath(path.join(__dirname, 'icon.png'));
    tray = new Tray(icon);
    
    const contextMenu = Menu.buildFromTemplate([
        { label: 'Health: --', enabled: false },
        { type: 'separator' },
        { label: 'Open Upkeep', click: () => require('electron').shell.openExternal('http://localhost:8080') },
        { label: 'Quick Maintenance', click: runQuickMaintenance },
        { type: 'separator' },
        { label: 'Quit', click: () => app.quit() }
    ]);
    
    tray.setContextMenu(contextMenu);
    tray.setToolTip('Upkeep');
    
    // Poll health
    setInterval(updateHealth, 300000);
    updateHealth();
});

async function updateHealth() {
    const response = await fetch('http://localhost:8080/api/system/health');
    const data = await response.json();
    tray.setTitle(`🔧 ${data.score}`);
}
```

**Effort:** 1 day

---

### 3. rumps (Python)

**Pros:**
- Python-based (matches backend)
- Simple API
- Lightweight

**Cons:**
- Requires py2app for distribution
- Less polished than native
- Limited customization

**Implementation:**
```python
import rumps
import requests

class UpkeepMenuBarApp(rumps.App):
    def __init__(self):
        super().__init__("🔧 --", quit_button=None)
        self.menu = [
            rumps.MenuItem("Health: --", callback=None),
            None,  # separator
            rumps.MenuItem("Open Upkeep", callback=self.open_web),
            rumps.MenuItem("Quick Maintenance", callback=self.run_quick),
            None,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        self.timer = rumps.Timer(self.update_health, 300)
        self.timer.start()
        self.update_health(None)
    
    def update_health(self, _):
        try:
            r = requests.get("http://localhost:8080/api/system/health", timeout=5)
            data = r.json()
            self.title = f"🔧 {data['score']}"
            self.menu["Health: --"].title = f"Health: {data['score']} ({data['grade']})"
        except:
            self.title = "🔧 ?"
    
    @rumps.clicked("Open Upkeep")
    def open_web(self, _):
        import webbrowser
        webbrowser.open("http://localhost:8080")
    
    @rumps.clicked("Quick Maintenance")
    def run_quick(self, _):
        requests.post("http://localhost:8080/api/maintenance/run", json={"operations": ["recommended"]})

if __name__ == "__main__":
    UpkeepMenuBarApp().run()
```

**Effort:** 0.5 days (MVP)

---

### 4. BitBar/xbar/SwiftBar

**Pros:**
- Zero coding for basic functionality
- Community-driven
- Shell script based

**Cons:**
- Requires separate app installation
- Limited interactivity
- Not self-contained

**Implementation:**
```bash
#!/bin/bash
# upkeep.5m.sh - runs every 5 minutes

HEALTH=$(curl -s http://localhost:8080/api/system/health | jq -r '.score')
GRADE=$(curl -s http://localhost:8080/api/system/health | jq -r '.grade')

echo "🔧 $HEALTH"
echo "---"
echo "Health: $HEALTH ($GRADE)"
echo "---"
echo "Open Upkeep | href=http://localhost:8080"
echo "Quick Maintenance | bash=/usr/bin/curl param1=-X param2=POST param3=http://localhost:8080/api/maintenance/run terminal=false"
```

**Effort:** 15 minutes

---

## Recommendation

### Phase 1: Quick Win (rumps)
Start with rumps for rapid prototyping:
- Fastest to implement
- Python integration with existing backend
- Good enough for personal use

### Phase 2: Production (SwiftUI)
For public distribution:
- Native performance
- Code signing
- Mac App Store potential
- Professional appearance

---

## Feature Matrix

| Feature | SwiftUI | Electron | rumps | xbar |
|---------|---------|----------|-------|------|
| Native look | ✅ | ❌ | ⚠️ | ⚠️ |
| Low memory | ✅ | ❌ | ✅ | ✅ |
| Notifications | ✅ | ✅ | ✅ | ❌ |
| Quick actions | ✅ | ✅ | ✅ | ⚠️ |
| Sparklines | ✅ | ✅ | ❌ | ❌ |
| Auto-update | ⚠️ | ✅ | ❌ | ❌ |
| Distribution | App Store | DMG | py2app | Plugin |

---

## Next Steps

1. **Prototype**: Build rumps MVP (0.5 days)
2. **Test**: Validate UX and API integration
3. **Decide**: Proceed with SwiftUI if warranted
4. **Document**: Add to ROADMAP.md

---

## Resources

- [rumps documentation](https://github.com/jaredks/rumps)
- [SwiftUI menu bar tutorial](https://www.hackingwithswift.com/quick-start/swiftui/how-to-create-a-menu-bar-extra-app)
- [Electron Tray API](https://www.electronjs.org/docs/latest/api/tray)
- [xbar plugin guide](https://xbarapp.com/docs/plugins/plugin-guide.html)

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-14 | Research complete | Evaluated 4 options, recommended rumps → SwiftUI path |
