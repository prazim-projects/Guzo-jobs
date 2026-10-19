import { performance } from 'node:perf_hooks';
import { describe, expect, it } from 'vitest';
import { isCurrentUserId } from '@/utils/jobHelpers';
import { isStrongPassword, suggestPassword } from '@/utils/password';

describe('Performance benchmark: local CPU smoke budgets (unthrottled)', () => {
  it('checks 100,000 IDs and passwords in under 1 second after warm-up', () => {
    for (let i = 0; i < 1000; i++) isStrongPassword('Strong-Pass123!');
    const start = performance.now();
    let matches = 0;
    for (let i = 0; i < 100_000; i++) {
      if (isCurrentUserId(i, String(i)) && isStrongPassword('Strong-Pass123!')) matches++;
    }
    expect(matches).toBe(100_000);
    expect(performance.now() - start).toBeLessThan(1000);
  });
  it('generates 100 strong passwords in under 1 second', () => {
    const start = performance.now();
    const passwords = Array.from({ length: 100 }, suggestPassword);
    expect(passwords.every(isStrongPassword)).toBe(true);
    expect(performance.now() - start).toBeLessThan(1000);
  });
});
