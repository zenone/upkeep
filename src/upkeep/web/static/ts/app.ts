/**
 * Upkeep Tool - Frontend Application
 * Entry point for TypeScript modules
 */

import { initTheme, toggleTheme, switchTab, showToast, reloadScripts } from './modules/ui';
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

  // Load initial dashboard data
  loadSystemInfo();
  loadHealthScore();
  loadTopProcesses();
  console.log('✓ Initial dashboard data loading');

  // Set up periodic updates (every 5 seconds)
  setInterval(() => {
    // Only update if on dashboard tab
    const dashboardTab = document.getElementById('dashboard');
    if (dashboardTab && dashboardTab.classList.contains('active')) {
      loadSystemInfo();
      loadHealthScore();
    }
  }, 5000);
  console.log('✓ Periodic updates configured (5s interval)');

  // Set up top processes refresh (every 10 seconds)
  setInterval(() => {
    const dashboardTab = document.getElementById('dashboard');
    if (dashboardTab && dashboardTab.classList.contains('active')) {
      loadTopProcesses();
    }
  }, 10000);
  console.log('✓ Process refresh configured (10s interval)');

  console.log('╔════════════════════════════════════════════════╗');
  console.log('║   UPKEEP - READY                     ║');
  console.log('╚════════════════════════════════════════════════╝');
});
