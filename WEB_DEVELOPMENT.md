# Web Frontend Development Guide

This document describes the TypeScript-based web frontend architecture and development workflow.

## Architecture

### Overview

The web frontend is built with **TypeScript**, compiled with **ESBuild**, and served as a single-page application. The architecture follows an **API-first** pattern where all business logic lives in the Python backend, and the frontend is a thin client.

### Technology Stack

- **TypeScript 5.3+** - Type-safe JavaScript with strict mode
- **ESBuild 0.20+** - Fast bundler (sub-second builds)
- **Vanilla JS** - No framework dependencies
- **Server-Sent Events (SSE)** - Real-time operation streaming
- **localStorage** - Theme and preference persistence

### File Structure

```
src/mac_maintenance/web/static/
├── ts/                          # TypeScript source files
│   ├── app.ts                   # Entry point, initialization
│   ├── types.ts                 # Type re-exports and extensions
│   └── modules/
│       ├── dashboard.ts         # System metrics, sparklines
│       ├── maintenance.ts       # Operations, SSE, progress
│       ├── storage.ts           # Storage analysis
│       ├── schedule.ts          # Schedule management
│       ├── ui.ts                # Theme, toast, modals
│       └── utils.ts             # Formatters, sanitization
├── app.js                       # ESBuild output (gitignored)
├── app.js.map                   # Source map (gitignored)
└── index.html                   # HTML template
```

## Module Responsibilities

### app.ts (Entry Point)
- Initializes the application on DOM ready
- Exposes functions to `window` object for HTML onclick handlers
- Sets up periodic metric updates (5s for metrics, 10s for processes)

### modules/dashboard.ts
- **System monitoring**: Load CPU, memory, disk metrics
- **Health score**: Display overall system health
- **Top processes**: Show resource consumers
- **Sparklines**: Canvas-based micro-charts
- **Trends**: Calculate and display metric trends (↑ ↓ •)
- **Animations**: Smooth value transitions with easing

### modules/maintenance.ts (Largest)
- **Operations**: Load and display maintenance operations
- **WHY/WHAT guidance**: Expandable help sections
- **Execution**: Run operations via SSE streaming
- **Progress tracking**: Real-time progress with ETA
- **Queue status**: Poll operation status every 2s
- **Templates**: Apply operation presets
- **Clipboard**: Copy operation output

### modules/storage.ts
- **Analysis**: Scan directories for large files
- **Deletion**: Trash or permanently delete files
- **Selection**: Multi-select with count display
- **Breadcrumbs**: Path navigation
- **Progress**: Bulk operation tracking

### modules/schedule.ts
- **CRUD**: Create, read, update, delete schedules
- **Templates**: Weekly, monthly, custom presets
- **Frequencies**: Daily, weekly, monthly options
- **launchd**: macOS scheduling integration
- **Conflicts**: Detect overlapping schedules

### modules/ui.ts
- **Theme**: Light/dark/system with localStorage persistence
- **Toast**: Notification system (success, error, warning, info)
- **Loading**: Full-screen loading indicator
- **Progress overlay**: Modal for long-running operations
- **Animations**: Value animation with easing
- **Tab switching**: Navigate between views

### modules/utils.ts
- **formatBytes()**: Human-readable file sizes
- **formatDuration()**: Time formatting (s, m, h)
- **escapeHtml()**: XSS prevention
- **handleSearchKey()**: Enter/Escape key handlers

## Development Workflow

### Initial Setup

```bash
# Install Node.js dependencies
npm install

# Verify installation
npm run type-check
npm run build:web
```

### Development Mode

**Option 1: Watch mode (auto-rebuild)**
```bash
# Terminal 1: Watch TypeScript files
npm run watch:web

# Terminal 2: Run web server
./run-web.sh
```

**Option 2: Single build + server**
```bash
# Build and start server
./run-web.sh
```

### Making Changes

1. **Edit TypeScript files** in `src/mac_maintenance/web/static/ts/`
2. **Watch mode** will auto-rebuild (or run `npm run build:web`)
3. **Reload browser** to see changes
4. **Check console** for errors

### Type Checking

```bash
# Run type checker (no output = success)
npm run type-check

# TypeScript will catch:
# - Type mismatches
# - Missing properties
# - Incorrect function signatures
# - Null/undefined errors
```

### Build Output

```bash
# Production build (minified)
npm run build:web

# Output:
# - src/mac_maintenance/web/static/app.js (~45KB)
# - src/mac_maintenance/web/static/app.js.map (~134KB)
```

## Adding New Features

### 1. Add API Type Definitions

Edit `types/api.d.ts` if adding new API endpoints:

```typescript
export interface NewFeatureResponse {
  success: boolean;
  data: {
    field: string;
  };
  timestamp: string;
}
```

### 2. Create or Update Module

Add function to appropriate module (e.g., `modules/dashboard.ts`):

```typescript
import type { NewFeatureResponse } from '../types';

export async function loadNewFeature(): Promise<void> {
  try {
    const response = await fetch('/api/new-feature');
    const data: NewFeatureResponse = await response.json();

    // Update UI with data
    const container = document.getElementById('new-feature');
    if (container) {
      container.innerHTML = `<p>${data.data.field}</p>`;
    }
  } catch (error) {
    console.error('Error loading feature:', error);
    showToast('Failed to load feature', 'error');
  }
}
```

### 3. Export to Window (If Needed for onclick)

Edit `app.ts` to expose function:

```typescript
declare global {
  interface Window {
    loadNewFeature: () => Promise<void>;
  }
}

window.loadNewFeature = loadNewFeature;
```

### 4. Use in HTML

```html
<button onclick="loadNewFeature()">Load Feature</button>
```

### 5. Build and Test

```bash
npm run type-check  # Verify types
npm run build:web   # Build bundle
./run-web.sh        # Test in browser
```

## Code Style Guidelines

### TypeScript Conventions

- **Use explicit types** for function parameters and returns
- **Avoid `any`** except for truly dynamic data (e.g., error responses)
- **Use type imports**: `import type { Type } from './types'`
- **Prefer `const`** over `let` when possible
- **Use optional chaining**: `element?.textContent`
- **Use nullish coalescing**: `value ?? 'default'`

### Error Handling

```typescript
try {
  const response = await fetch('/api/endpoint');
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  const data: ExpectedType = await response.json();
  // ... process data
} catch (error) {
  console.error('Error:', error);
  showToast('Operation failed', 'error');
}
```

### XSS Prevention

**NEVER use innerHTML with user input directly**:

```typescript
// BAD - XSS vulnerable
element.innerHTML = `<div>${userInput}</div>`;

// GOOD - Safe
element.innerHTML = `<div>${escapeHtml(userInput)}</div>`;

// BEST - Use textContent when possible
element.textContent = userInput;
```

## Common Tasks

### Update Types After API Changes

1. Edit `types/api.d.ts` to match new API response
2. Run `npm run type-check` to find affected code
3. Update TypeScript code to handle new fields
4. Rebuild and test

### Debug Type Errors

```bash
# Get detailed error output
npx tsc --noEmit

# Common fixes:
# - Add null checks: if (element) { ... }
# - Use non-null assertion: value!
# - Cast to any (last resort): (data as any).field
```

### Optimize Bundle Size

```bash
# Check bundle size
ls -lh src/mac_maintenance/web/static/app.js

# Current: ~45KB minified (target: <100KB)

# If too large:
# 1. Remove unused imports
# 2. Use dynamic imports for rarely-used code
# 3. Check for duplicate dependencies
```

### Add External Library

```bash
# Install library
npm install --save library-name

# Install types (if available)
npm install --save-dev @types/library-name

# Import in TypeScript
import { feature } from 'library-name';
```

## Testing

### Manual Testing Checklist

After changes, test:

- [ ] Dashboard: Metrics load and update every 5s
- [ ] Storage: Analysis works, deletion succeeds
- [ ] Maintenance: Operations run with SSE output
- [ ] Schedule: CRUD operations work
- [ ] Theme: Toggle cycles light → dark → system
- [ ] Toast: Notifications appear and dismiss
- [ ] Loading: Overlay shows during operations
- [ ] Console: No errors in DevTools

### Browser Testing

Test in:
- **Safari** (primary target on macOS)
- **Chrome** (secondary)
- **Firefox** (tertiary)

### Performance Testing

```javascript
// In browser console
performance.measure('metric-load');
// ... perform action
performance.getEntriesByType('measure');
```

## Troubleshooting

### Build Fails

```bash
# Check Node.js version
node --version  # Requires 18+

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check for syntax errors
npx tsc --noEmit
```

### Type Errors

```bash
# Show all type errors
npm run type-check

# Common issues:
# - Missing null checks
# - Incorrect type imports
# - API type mismatch
```

### Runtime Errors

1. **Check browser console** for JavaScript errors
2. **Verify API responses** in Network tab
3. **Check source maps** for original TypeScript line numbers
4. **Add console.log()** statements for debugging

### Server Won't Start

```bash
# Check if port is in use
lsof -ti:8080

# Check Python environment
source .venv/bin/activate
pip install -e .

# Check build output exists
ls -l src/mac_maintenance/web/static/app.js
```

## Advanced Topics

### Source Maps

Source maps (`app.js.map`) allow debugging TypeScript in the browser:

1. Open DevTools
2. Go to Sources tab
3. See original TypeScript files with line numbers
4. Set breakpoints in TypeScript code

### ESBuild Configuration

Customize build in `scripts/build-web.sh`:

```bash
npx esbuild src/mac_maintenance/web/static/ts/app.ts \
  --bundle \
  --target=es2020 \         # JavaScript version
  --platform=browser \       # Browser environment
  --outfile=... \            # Output path
  --sourcemap \              # Enable source maps
  --format=iife \            # Immediately-invoked function
  --minify                   # Compress output
```

### Type Extensions

Extend API types for frontend use:

```typescript
// types.ts
import type { Schedule as BaseSchedule } from '../../../../types/api';

export interface Schedule extends BaseSchedule {
  // Add frontend-specific fields
  uiState?: {
    expanded: boolean;
  };
}
```

### Global State Management

State is managed per-module:

```typescript
// modules/dashboard.ts
let previousMetrics = { cpu: 0, memory: 0, disk: 0 };

export function updateMetrics(newMetrics) {
  previousMetrics = newMetrics;
}
```

**No global state library** is used to keep dependencies minimal.

## Future Enhancements

Potential improvements:

1. **Unit Tests**: Add Vitest for testing modules
2. **Hot Module Replacement**: Faster development feedback
3. **Code Splitting**: Load modules on-demand
4. **Type Generation**: Auto-generate types from Python models
5. **ESLint**: Add linting rules for code quality
6. **Prettier**: Automatic code formatting
7. **Web Workers**: Offload heavy processing
8. **Service Worker**: Offline support

## Resources

- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [ESBuild Documentation](https://esbuild.github.io/)
- [MDN Web Docs](https://developer.mozilla.org/)
- [Can I Use](https://caniuse.com/) - Browser compatibility

## Support

For issues or questions:
1. Check this guide first
2. Review TypeScript error messages
3. Check browser console for runtime errors
4. Verify API responses in Network tab
5. Open an issue on GitHub with error details

---

**Last Updated**: 2026-02-01
**TypeScript Version**: 5.3.3
**ESBuild Version**: 0.20.0
