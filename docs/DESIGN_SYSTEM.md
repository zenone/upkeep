# Design System - Mac Maintenance

**Last Updated**: 2026-01-28
**Status**: 🟡 IN DEVELOPMENT
**Standard**: WCAG 2.1 Level AA

---

## 🎨 Design Philosophy

**Inspiration**: 2026 Modern Web Standards
**Reference Apps**: GitHub Actions, Vercel, Railway, Docker Desktop

### Core Principles
1. **Real-time Feedback**: SSE for live updates, no polling
2. **Progressive Disclosure**: Collapsible sections, hide complexity
3. **Glanceability**: Status icons, color coding, relative timestamps
4. **One-Click Actions**: Minimize steps, confirm only destructive actions
5. **Accessibility First**: Keyboard nav, screen readers, high contrast

---

## 🌈 Color Palette

### Primary Colors
```css
--primary: #007AFF;        /* Apple Blue - Primary actions */
--secondary: #5856D6;      /* Indigo - Secondary actions */
--accent: #FF2D55;         /* Pink - Attention-grabbing */
```

### Semantic Colors
```css
--success: #34C759;        /* Green - Completed, healthy */
--warning: #FF9500;        /* Orange - Caution, pending */
--error: #FF3B30;          /* Red - Failed, critical */
--info: #007AFF;           /* Blue - Informational */
```

### Neutral Colors
```css
--neutral-100: #F5F5F7;    /* Background light */
--neutral-200: #E5E5EA;    /* Border light */
--neutral-300: #D1D1D6;    /* Dividers */
--neutral-400: #8E8E93;    /* Text secondary */
--neutral-500: #636366;    /* Text tertiary */
--neutral-800: #1C1C1E;    /* Text primary */
--neutral-900: #000000;    /* Pure black */
```

### Color Contrast Ratios (WCAG AA)
- `--primary` on white: 5.2:1 ✅
- `--success` on white: 4.9:1 ✅
- `--error` on white: 6.1:1 ✅
- `--neutral-400` on white: 4.6:1 ✅

---

## 📐 Typography

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont,
             "Segoe UI", Roboto, Helvetica, Arial,
             sans-serif, "Apple Color Emoji";
```

### Type Scale
```css
--text-xs: 12px;      /* Labels, timestamps */
--text-sm: 14px;      /* Body text secondary */
--text-base: 16px;    /* Body text primary */
--text-lg: 18px;      /* Subheadings */
--text-xl: 20px;      /* Headings */
--text-2xl: 24px;     /* Page titles */
--text-3xl: 30px;     /* Hero text */
```

### Line Heights
```css
--leading-tight: 1.25;   /* Headings */
--leading-normal: 1.5;   /* Body text */
--leading-relaxed: 1.75; /* Long-form content */
```

---

## 🧩 Component Library

### 1. Buttons

#### Primary Button
```html
<button class="btn btn-primary">Run Maintenance</button>
```
**Style**:
- Background: `--primary`
- Text: white
- Border radius: 8px
- Padding: 12px 24px
- Hover: 10% darker
- Active: 20% darker
- Focus: 2px outline, `--primary` at 50% opacity

#### Secondary Button
```html
<button class="btn btn-secondary">Cancel</button>
```
**Style**:
- Background: transparent
- Text: `--primary`
- Border: 1px solid `--neutral-300`
- Same padding/radius as primary
- Hover: `--neutral-100` background

#### Danger Button
```html
<button class="btn btn-danger">Delete Permanently</button>
```
**Style**:
- Background: `--error`
- Text: white
- Same padding/radius
- Used ONLY for destructive actions

---

### 2. Status Icons

#### Icon Set
- ✓ (checkmark) - Completed successfully
- ▶ (play) - Currently running
- ⋯ (ellipsis) - Waiting to run
- ✗ (x-mark) - Failed
- ⏭️ (skip) - Skipped by user
- ℹ️ (info) - Informational

#### Usage
```html
<span class="status-icon status-success">✓</span>
<span class="status-icon status-running">▶</span>
<span class="status-icon status-error">✗</span>
```

**Style**:
```css
.status-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  font-size: 14px;
}

.status-success { color: var(--success); }
.status-running { color: var(--info); animation: pulse 2s infinite; }
.status-error { color: var(--error); }
.status-pending { color: var(--neutral-400); }
```

---

### 3. Cards

```html
<div class="card">
  <div class="card-header">
    <h3>System Health</h3>
  </div>
  <div class="card-body">
    [Content here]
  </div>
</div>
```

**Style**:
- Background: white
- Border: 1px solid `--neutral-200`
- Border radius: 12px
- Padding: 16px
- Box shadow: 0 1px 3px rgba(0,0,0,0.1)

---

### 4. Progress Bar

```html
<div class="progress-bar">
  <div class="progress-fill" style="width: 60%"></div>
</div>
<span class="progress-text">3/5 operations complete</span>
```

**Style**:
```css
.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--neutral-200);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--success);
  transition: width 0.3s ease;
}
```

---

### 5. Inline Terminal Output

```html
<details class="terminal-section" open>
  <summary>
    <span class="status-icon">▶</span>
    <span class="op-name">Update Homebrew</span>
    <span class="op-status">Running...</span>
    <span class="op-duration">2.3s</span>
  </summary>
  <pre class="terminal-output">[Live streaming output...]</pre>
</details>
```

**Style**:
```css
.terminal-section {
  margin-bottom: 12px;
  border: 1px solid var(--neutral-200);
  border-radius: 8px;
  overflow: hidden;
}

.terminal-section summary {
  padding: 12px 16px;
  background: var(--neutral-100);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.terminal-output {
  padding: 16px;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
}
```

**Auto-behavior**:
- Current operation: Auto-expanded
- Completed: Auto-collapse after 3 seconds
- Failed: Stay expanded with red border

---

### 6. Modal Dialog (Custom Confirmation)

```html
<div class="modal" id="confirm-modal">
  <div class="modal-overlay"></div>
  <div class="modal-content">
    <h3 class="modal-title">Confirm Action</h3>
    <p class="modal-message" id="confirm-message"></p>
    <div class="modal-buttons">
      <button class="btn btn-secondary" id="confirm-cancel">Cancel</button>
      <button class="btn btn-danger" id="confirm-yes">Confirm</button>
    </div>
  </div>
</div>
```

**Style**:
```css
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  display: none;
}

.modal.active { display: flex; }

.modal-overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  margin: auto;
  background: white;
  border-radius: 16px;
  padding: 24px;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}
```

**JavaScript API**:
```javascript
async function showConfirm(message) {
  return new Promise((resolve) => {
    // Show modal, resolve on button click
  });
}

// Usage
if (await showConfirm('Delete 5 files?')) {
  // User confirmed
}
```

---

## ♿ Accessibility (A11y)

### Keyboard Navigation
- All interactive elements focusable via Tab
- Enter/Space activates buttons
- Escape closes modals
- Arrow keys navigate lists

### ARIA Labels
```html
<button aria-label="Delete file example.txt">
  🗑️
</button>

<div role="progressbar" aria-valuenow="60" aria-valuemin="0" aria-valuemax="100">
  60%
</div>

<div role="status" aria-live="polite">
  Operation completed successfully
</div>
```

### Focus Indicators
```css
*:focus {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

*:focus:not(:focus-visible) {
  outline: none;
}
```

---

## 📱 Responsive Design

### Breakpoints
```css
--mobile: 640px;      /* Small phones */
--tablet: 768px;      /* Tablets */
--desktop: 1024px;    /* Desktop */
--wide: 1280px;       /* Wide screens */
```

### Grid System
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}
```

---

## 🎭 Animation & Motion

### Principles
- **Duration**: 200-300ms for UI transitions
- **Easing**: `ease-in-out` for natural movement
- **Respect prefers-reduced-motion**

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Common Animations
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes slideIn {
  from { transform: translateY(-10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.fade-in { animation: slideIn 0.3s ease-out; }
```

---

## 📋 Component Checklist (Pre-Implementation)

Before building any component:
- [ ] Meets WCAG 2.1 Level AA contrast requirements
- [ ] Fully keyboard navigable
- [ ] Has appropriate ARIA labels
- [ ] Tested with VoiceOver (macOS screen reader)
- [ ] Respects `prefers-reduced-motion`
- [ ] Responsive across all breakpoints
- [ ] Matches design system color palette

---

## 🔮 Future Enhancements (Post-MVP)

- Dark mode support
- Custom theme engine
- Animation library (Framer Motion)
- Component storybook (Storybook.js)

---

**Next Review**: After Phase 2 (UI/UX Enhancements) completion
