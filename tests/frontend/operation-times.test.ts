/**
 * TDD Tests for Operation Time Tracking
 *
 * Run with: npm test (after vitest is installed)
 * Or manually validate each test case
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  loadOperationTimes,
  recordOperationTime,
  getAverageDuration,
  getMedianDuration,
  getTypicalDurationDisplay,
  calculateETA,
  getOperationHistory,
  clearOperationTimes,
} from '../../src/upkeep/web/static/ts/modules/operation-times';

describe('Operation Time Tracking', () => {
  // Clear localStorage before each test
  beforeEach(() => {
    clearOperationTimes();
  });

  afterEach(() => {
    clearOperationTimes();
  });

  describe('loadOperationTimes()', () => {
    it('should return empty object when no data exists', () => {
      const times = loadOperationTimes();
      expect(times).toEqual({});
    });

    it('should return stored data when it exists', () => {
      localStorage.setItem('upkeep-operation-times', JSON.stringify({
        'brew-update': { runs: [50], average: 50 }
      }));

      const times = loadOperationTimes();
      expect(times).toHaveProperty('brew-update');
      expect(times['brew-update'].average).toBe(50);
    });

    it('should handle corrupted JSON gracefully', () => {
      localStorage.setItem('upkeep-operation-times', 'invalid json{');
      const times = loadOperationTimes();
      expect(times).toEqual({});
    });
  });

  describe('recordOperationTime()', () => {
    it('should record first operation time', () => {
      recordOperationTime('brew-update', 45);

      const times = loadOperationTimes();
      expect(times['brew-update']).toBeDefined();
      expect(times['brew-update'].runs).toEqual([45]);
      expect(times['brew-update'].average).toBe(45);
    });

    it('should append to existing runs', () => {
      recordOperationTime('brew-update', 45);
      recordOperationTime('brew-update', 50);
      recordOperationTime('brew-update', 48);

      const times = loadOperationTimes();
      expect(times['brew-update'].runs).toEqual([45, 50, 48]);
      expect(times['brew-update'].average).toBe(47.67); // (45+50+48)/3
    });

    it('should limit to 5 runs max (rolling window)', () => {
      recordOperationTime('brew-update', 40);
      recordOperationTime('brew-update', 45);
      recordOperationTime('brew-update', 50);
      recordOperationTime('brew-update', 48);
      recordOperationTime('brew-update', 52);
      recordOperationTime('brew-update', 49); // 6th run, should drop 40

      const times = loadOperationTimes();
      expect(times['brew-update'].runs).toEqual([45, 50, 48, 52, 49]);
      expect(times['brew-update'].runs).not.toContain(40);
      expect(times['brew-update'].runs.length).toBe(5);
    });

    it('should round durations to nearest second', () => {
      recordOperationTime('brew-update', 45.7);

      const times = loadOperationTimes();
      expect(times['brew-update'].runs[0]).toBe(46);
    });

    it('should calculate correct average', () => {
      recordOperationTime('test-op', 10);
      recordOperationTime('test-op', 20);
      recordOperationTime('test-op', 30);

      const times = loadOperationTimes();
      expect(times['test-op'].average).toBe(20); // (10+20+30)/3
    });

    it('should handle multiple different operations', () => {
      recordOperationTime('brew-update', 50);
      recordOperationTime('macos-check', 120);
      recordOperationTime('dns-clear', 2);

      const times = loadOperationTimes();
      expect(Object.keys(times).length).toBe(3);
      expect(times['brew-update'].average).toBe(50);
      expect(times['macos-check'].average).toBe(120);
      expect(times['dns-clear'].average).toBe(2);
    });
  });

  describe('getAverageDuration()', () => {
    it('should return default 30s for unknown operation', () => {
      const avg = getAverageDuration('unknown-operation');
      expect(avg).toBe(30);
    });

    it('should return historical average for known operation', () => {
      recordOperationTime('brew-update', 45);
      recordOperationTime('brew-update', 50);
      recordOperationTime('brew-update', 55);

      const avg = getAverageDuration('brew-update');
      expect(avg).toBe(50); // (45+50+55)/3
    });

    it('should return default for operation with no runs', () => {
      localStorage.setItem('upkeep-operation-times', JSON.stringify({
        'brew-update': { runs: [], average: 0 }
      }));

      const avg = getAverageDuration('brew-update');
      expect(avg).toBe(30);
    });
  });

  describe('calculateETA()', () => {
    beforeEach(() => {
      // Set up historical data for testing
      recordOperationTime('brew-update', 50);
      recordOperationTime('macos-check', 120);
      recordOperationTime('dns-clear', 2);
    });

    it('should return 0 for empty remaining operations', () => {
      const eta = calculateETA([], null, 0);
      expect(eta).toBe(0);
    });

    it('should calculate ETA for single remaining operation', () => {
      const eta = calculateETA(['brew-update'], null, 0);
      expect(eta).toBe(50);
    });

    it('should sum multiple remaining operations', () => {
      const eta = calculateETA(['brew-update', 'macos-check', 'dns-clear'], null, 0);
      expect(eta).toBe(172); // 50 + 120 + 2
    });

    it('should use default 30s for unknown operations', () => {
      const eta = calculateETA(['unknown-op-1', 'unknown-op-2'], null, 0);
      expect(eta).toBe(60); // 30 + 30
    });

    it('should include remaining time for current operation', () => {
      const eta = calculateETA(['macos-check'], 'brew-update', 0.5); // brew-update 50% done
      // brew-update avg: 50s, 50% done = 25s remaining
      // macos-check avg: 120s
      expect(eta).toBe(145); // 25 + 120
    });

    it('should handle current operation at 0% progress', () => {
      const eta = calculateETA(['macos-check'], 'brew-update', 0);
      expect(eta).toBe(170); // 50 + 120 (full brew-update time + macos-check)
    });

    it('should handle current operation at 99% progress', () => {
      const eta = calculateETA(['macos-check'], 'brew-update', 0.99);
      expect(eta).toBe(121); // 0.5 + 120 (almost done with brew-update)
    });

    it('should handle no current operation', () => {
      const eta = calculateETA(['brew-update', 'macos-check'], null, 0);
      expect(eta).toBe(170); // 50 + 120
    });

    it('should round result to nearest second', () => {
      const eta = calculateETA(['brew-update'], 'dns-clear', 0.333);
      // dns-clear: 2s, 33.3% done = 1.33s remaining
      // brew-update: 50s
      // Total: 51.33s, rounds to 51
      expect(eta).toBe(51);
    });
  });

  describe('getMedianDuration()', () => {
    it('should return null for unknown operation', () => {
      const median = getMedianDuration('unknown-op');
      expect(median).toBeNull();
    });

    it('should calculate median for odd number of runs', () => {
      recordOperationTime('test-op', 10);
      recordOperationTime('test-op', 20);
      recordOperationTime('test-op', 30);

      const median = getMedianDuration('test-op');
      expect(median).toBe(20); // Middle value
    });

    it('should calculate median for even number of runs', () => {
      recordOperationTime('test-op', 10);
      recordOperationTime('test-op', 20);
      recordOperationTime('test-op', 30);
      recordOperationTime('test-op', 40);

      const median = getMedianDuration('test-op');
      expect(median).toBe(25); // Average of 20 and 30
    });

    it('should be resistant to outliers (vs average)', () => {
      // Scenario: operation usually takes 2s, but once hung for 120s
      recordOperationTime('flaky-op', 2);
      recordOperationTime('flaky-op', 2);
      recordOperationTime('flaky-op', 3);
      recordOperationTime('flaky-op', 120); // Outlier!

      const median = getMedianDuration('flaky-op');
      const average = getAverageDuration('flaky-op');

      expect(median).toBe(2.5); // Median: (2+3)/2 - representative
      expect(average).toBe(31.75); // Average: (2+2+3+120)/4 - skewed by outlier
    });

    it('should handle single run', () => {
      recordOperationTime('test-op', 42);

      const median = getMedianDuration('test-op');
      expect(median).toBe(42);
    });
  });

  describe('getTypicalDurationDisplay()', () => {
    it('should return null when no data exists', () => {
      const display = getTypicalDurationDisplay('unknown-op');
      expect(display).toBeNull();
    });

    it('should format seconds (< 60s)', () => {
      recordOperationTime('fast-op', 45);

      const display = getTypicalDurationDisplay('fast-op');
      expect(display).toBe('45s');
    });

    it('should format minutes and seconds (60s - 3600s)', () => {
      recordOperationTime('medium-op', 150); // 2m 30s

      const display = getTypicalDurationDisplay('medium-op');
      expect(display).toBe('2m 30s');
    });

    it('should format minutes only when no seconds', () => {
      recordOperationTime('medium-op', 120); // Exactly 2m

      const display = getTypicalDurationDisplay('medium-op');
      expect(display).toBe('2m');
    });

    it('should format hours and minutes (> 3600s)', () => {
      recordOperationTime('slow-op', 5400); // 1h 30m

      const display = getTypicalDurationDisplay('slow-op');
      expect(display).toBe('1h 30m');
    });

    it('should format hours only when no minutes', () => {
      recordOperationTime('slow-op', 7200); // Exactly 2h

      const display = getTypicalDurationDisplay('slow-op');
      expect(display).toBe('2h');
    });

    it('should round seconds appropriately', () => {
      recordOperationTime('test-op', 45.7);

      const display = getTypicalDurationDisplay('test-op');
      expect(display).toBe('46s');
    });

    it('should use median (not average) for display', () => {
      // Outlier test
      recordOperationTime('flaky-op', 2);
      recordOperationTime('flaky-op', 2);
      recordOperationTime('flaky-op', 3);
      recordOperationTime('flaky-op', 120); // Outlier

      const display = getTypicalDurationDisplay('flaky-op');
      // Should show median (2.5s ≈ 3s) not average (31.75s ≈ 32s)
      expect(display).toBe('3s');
    });
  });

  describe('getOperationHistory()', () => {
    it('should return null for unknown operation', () => {
      const history = getOperationHistory('unknown-op');
      expect(history).toBeNull();
    });

    it('should return full history for known operation', () => {
      recordOperationTime('brew-update', 45);
      recordOperationTime('brew-update', 50);

      const history = getOperationHistory('brew-update');
      expect(history).not.toBeNull();
      expect(history?.runs).toEqual([45, 50]);
      expect(history?.average).toBe(47.5);
    });
  });

  describe('clearOperationTimes()', () => {
    it('should remove all stored data', () => {
      recordOperationTime('brew-update', 50);
      recordOperationTime('macos-check', 120);

      clearOperationTimes();

      const times = loadOperationTimes();
      expect(times).toEqual({});
      expect(localStorage.getItem('upkeep-operation-times')).toBeNull();
    });
  });

  describe('Integration Tests', () => {
    it('should accurately predict ETA for typical maintenance run', () => {
      // Simulate recording times from a previous run
      recordOperationTime('brew-update', 52);
      recordOperationTime('brew-update', 48);
      recordOperationTime('brew-update', 50);

      recordOperationTime('macos-check', 120);
      recordOperationTime('macos-check', 115);

      recordOperationTime('dns-clear', 2);
      recordOperationTime('dns-clear', 2);

      // Now predict ETA for new run with same operations
      const operations = ['brew-update', 'macos-check', 'dns-clear'];
      const eta = calculateETA(operations, null, 0);

      // Expected: 50 (brew avg) + 117.5 (macos avg) + 2 (dns avg) = 169.5 → 170
      expect(eta).toBeCloseTo(170, 0);
    });

    it('should improve accuracy with more data', () => {
      // First run - uses defaults
      const eta1 = calculateETA(['new-op-1', 'new-op-2'], null, 0);
      expect(eta1).toBe(60); // 30 + 30 (defaults)

      // After actual runs
      recordOperationTime('new-op-1', 15);
      recordOperationTime('new-op-2', 45);

      // Second prediction - uses historical
      const eta2 = calculateETA(['new-op-1', 'new-op-2'], null, 0);
      expect(eta2).toBe(60); // 15 + 45 (actual times)

      // More accurate!
    });

    it('should handle real-world variability', () => {
      // Simulate variable operation times
      recordOperationTime('brew-update', 40);
      recordOperationTime('brew-update', 55);
      recordOperationTime('brew-update', 48);
      recordOperationTime('brew-update', 52);
      recordOperationTime('brew-update', 50);

      const avg = getAverageDuration('brew-update');
      expect(avg).toBe(49); // (40+55+48+52+50)/5

      // ETA should use this average
      const eta = calculateETA(['brew-update'], null, 0);
      expect(eta).toBe(49);
    });
  });

  describe('Edge Cases', () => {
    it('should handle negative durations gracefully', () => {
      recordOperationTime('test-op', -5);
      const times = loadOperationTimes();
      expect(times['test-op'].runs[0]).toBe(-5); // Records as-is (Math.round)
    });

    it('should handle zero duration', () => {
      recordOperationTime('instant-op', 0);
      const avg = getAverageDuration('instant-op');
      expect(avg).toBe(0);
    });

    it('should handle very large durations', () => {
      recordOperationTime('slow-op', 3600); // 1 hour
      const avg = getAverageDuration('slow-op');
      expect(avg).toBe(3600);
    });

    it('should handle operation IDs with special characters', () => {
      recordOperationTime('brew-update-special_123', 50);
      const avg = getAverageDuration('brew-update-special_123');
      expect(avg).toBe(50);
    });

    it('should handle current operation progress > 1', () => {
      const eta = calculateETA(['brew-update'], 'macos-check', 1.5);
      // Should treat as 100% complete (no remaining time for current)
      expect(eta).toBeLessThanOrEqual(50); // Just brew-update
    });

    it('should handle current operation progress < 0', () => {
      const eta = calculateETA(['brew-update'], 'macos-check', -0.5);
      // Should treat as 0% (full time remaining)
      const fullEta = calculateETA(['brew-update'], 'macos-check', 0);
      expect(eta).toBe(fullEta);
    });
  });
});

/**
 * Manual Test Cases (for browser DevTools Console)
 */
export const manualTests = {
  /**
   * Test 1: Record some times and verify storage
   */
  test1_recordAndVerify: () => {
    clearOperationTimes();
    recordOperationTime('brew-update', 50);
    recordOperationTime('brew-update', 52);
    console.log('Recorded times:', loadOperationTimes());
    console.log('✓ Test 1 passed if you see brew-update with runs [50, 52]');
  },

  /**
   * Test 2: Verify rolling window (max 5)
   */
  test2_rollingWindow: () => {
    clearOperationTimes();
    for (let i = 1; i <= 7; i++) {
      recordOperationTime('test-op', i * 10);
    }
    const times = loadOperationTimes();
    console.log('Runs:', times['test-op'].runs);
    console.log('✓ Test 2 passed if runs = [30, 40, 50, 60, 70] (last 5 only)');
  },

  /**
   * Test 3: Test ETA calculation
   */
  test3_etaCalculation: () => {
    clearOperationTimes();
    recordOperationTime('fast-op', 5);
    recordOperationTime('slow-op', 100);

    const eta = calculateETA(['fast-op', 'slow-op'], null, 0);
    console.log('ETA for fast-op + slow-op:', eta, 'seconds');
    console.log('✓ Test 3 passed if ETA = 105 seconds');
  },

  /**
   * Run all manual tests
   */
  runAll: () => {
    console.log('Running manual tests...\n');
    manualTests.test1_recordAndVerify();
    console.log('\n');
    manualTests.test2_rollingWindow();
    console.log('\n');
    manualTests.test3_etaCalculation();
    console.log('\nAll manual tests complete!');
  }
};
