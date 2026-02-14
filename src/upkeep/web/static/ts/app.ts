/**
 * Upkeep Tool - Frontend Application
 * Entry point for TypeScript modules
 */

import { initTheme, toggleTheme, switchTab, showToast, reloadScripts, setTheme, toggleAutoRefresh, setRefreshInterval, togglePreviewMode, toggleConfirmations, initSettings, showKeyboardShortcuts } from './modules/ui';
import { loadSystemInfo, loadHealthScore, loadTopProcesses } from './modules/dashboard';
import { loadOperations, runDoctor, fixDoctorIssue, runSelectedOperations, cancelOperations, skipCurrentOperation, applyTemplate, selectAllOperations, deselectAllOperations, copyOutputToClipboard, showQuickStartWizard, closeWizard, selectWizardOption, initKeyboardShortcuts, closeShortcuts, filterByCategory, toggleCategory } from './modules/maintenance';
import { analyzeStorage, setPath, getUsername } from './modules/storage';
import { onScheduleTabShow, openScheduleModal, closeScheduleModal, loadSchedules, saveSchedule, deleteSchedule, toggleScheduleEnabled, runScheduleNow, applyScheduleTemplate } from './modules/schedule';
import type { TabName } from './types';

console.log('╔════════════════════════════════════════════════╗');
console.log('║   UPKEEP - SCRIPT LOADING            ║');
console.log('╚════════════════════════════════════════════════╝');

// ============================================================================
// Global Functions - Expose to Window for onclick Handlers
// ============================================================================

declare global {
  interface Window {
    // Tab switching
    switchTab: (tabName: TabName) => void;
    showTab: (tabName: TabName) => void;

    // Theme
    toggleTheme: () => void;

    // System Configuration
    reloadScripts: () => Promise<void>;

    // Settings
    setTheme: (theme: string) => void;
    toggleAutoRefresh: (enabled: boolean) => void;
    setRefreshInterval: (seconds: number) => void;
    togglePreviewMode: (enabled: boolean) => void;
    toggleConfirmations: (enabled: boolean) => void;
    showKeyboardShortcuts: () => void;

    // Dashboard
    loadSystemInfo: () => Promise<void>;
    loadHealthScore: () => Promise<void>;
    loadTopProcesses: () => Promise<void>;

    // Maintenance
    loadOperations: () => Promise<void>;
    runDoctor: () => Promise<void>;
    fixDoctorIssue: (action: string) => Promise<void>;
    runSelectedOperations: () => Promise<void>;
    cancelOperations: () => void;
    skipCurrentOperation: () => void;
    applyTemplate: (template: { name: string; operations: string[] }) => void;
    selectAllOperations: () => void;
    deselectAllOperations: () => void;
    upkeepFilterByCategory: (category: string | null) => void;
    upkeepToggleCategory: (category: string) => void;
    copyOutputToClipboard: () => void;
    showQuickStartWizard: () => void;
    closeWizard: () => void;
    selectWizardOption: (option: string) => Promise<void>;

    // Keyboard shortcuts
    closeShortcuts: () => void;

    // Storage
    analyzeStorage: () => Promise<void>;
    setPath: (path: string) => void;
    getUsername: () => string;

    // Schedule
    onScheduleTabShow: () => void;
    openScheduleModal: (scheduleId?: string) => void;
    closeScheduleModal: () => void;
    loadSchedules: () => Promise<void>;
    saveSchedule: () => Promise<void>;
    deleteSchedule: (scheduleId: string) => void;
    toggleScheduleEnabled: (scheduleId: string, enabled: boolean) => Promise<void>;
    runScheduleNow: (scheduleId: string) => void;
    applyScheduleTemplate: (template: any) => void;

    // Utilities
    showToast: (message: string, type?: 'success' | 'error' | 'warning' | 'info', duration?: number) => void;
  }
}

// Expose functions to window
window.switchTab = switchTab;
window.showTab = switchTab; // Alias for compatibility
window.toggleTheme = toggleTheme;
window.reloadScripts = reloadScripts;
window.setTheme = setTheme;
window.toggleAutoRefresh = toggleAutoRefresh;
window.setRefreshInterval = setRefreshInterval;
window.togglePreviewMode = togglePreviewMode;
window.toggleConfirmations = toggleConfirmations;
window.showKeyboardShortcuts = showKeyboardShortcuts;
window.loadSystemInfo = loadSystemInfo;
window.loadHealthScore = loadHealthScore;
window.loadTopProcesses = loadTopProcesses;
window.loadOperations = loadOperations;
window.runDoctor = runDoctor;
window.fixDoctorIssue = fixDoctorIssue;
window.runSelectedOperations = runSelectedOperations;
window.cancelOperations = cancelOperations;
window.skipCurrentOperation = skipCurrentOperation;
window.applyTemplate = applyTemplate;
window.selectAllOperations = selectAllOperations;
window.deselectAllOperations = deselectAllOperations;
window.upkeepFilterByCategory = filterByCategory;
window.upkeepToggleCategory = toggleCategory;
window.copyOutputToClipboard = copyOutputToClipboard;
window.showQuickStartWizard = showQuickStartWizard;
window.closeWizard = closeWizard;
window.selectWizardOption = selectWizardOption;
window.closeShortcuts = closeShortcuts;
window.analyzeStorage = analyzeStorage;
window.setPath = setPath;
window.getUsername = getUsername;
window.onScheduleTabShow = onScheduleTabShow;
window.openScheduleModal = openScheduleModal;
window.closeScheduleModal = closeScheduleModal;
window.loadSchedules = loadSchedules;
window.saveSchedule = saveSchedule;
window.deleteSchedule = deleteSchedule;
window.toggleScheduleEnabled = toggleScheduleEnabled;
window.runScheduleNow = runScheduleNow;
window.applyScheduleTemplate = applyScheduleTemplate;
window.showToast = showToast;

// ============================================================================
// Application Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  console.log('✓ DOM Content Loaded');

  // Keyboard shortcuts ("?" for help)
  initKeyboardShortcuts();

  // Initialize theme
  initTheme();
  console.log('✓ Theme initialized');

  // Initialize settings panel
  initSettings();
  console.log('✓ Settings initialized');

  // Load initial dashboard data
  loadSystemInfo();
  loadHealthScore();
  loadTopProcesses();
  console.log('✓ Initial dashboard data loading');

  // Note: Auto-refresh intervals are now managed by initSettings()
  // based on user preferences (Settings > Dashboard > Auto-Refresh)
  console.log('✓ Auto-refresh configured via settings');

  console.log('╔════════════════════════════════════════════════╗');
  console.log('║   UPKEEP - READY                     ║');
  console.log('╚════════════════════════════════════════════════╝');
});
