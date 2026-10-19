import { describe, expect, it } from 'vitest';
import { isStrongPassword, suggestPassword } from '@/utils/password';
import { isCurrentUserId, resolveJobImage, FALLBACK_JOB_IMAGE } from '@/utils/jobHelpers';
import { authError, setLanguage, t } from '@/utils/i18n';

describe('Logic benchmark: password policy', () => {
  it.each(['', 'Ab1!short', 'alllowercase123!', 'ALLUPPERCASE123!', 'NoNumbersHere!', 'NoSymbolsHere123', 'Spaces Only 123'])('rejects %j', password => {
    expect(isStrongPassword(password)).toBe(false);
  });
  it('accepts the exact 12-character boundary', () => expect(isStrongPassword('Abcdefghij1!')).toBe(true));
  it('generates 100 unique policy-compliant passwords', () => {
    const passwords = Array.from({ length: 100 }, suggestPassword);
    expect(passwords.every(p => p.length === 20 && isStrongPassword(p))).toBe(true);
    expect(new Set(passwords).size).toBe(100);
  });
});

describe('Logic benchmark: identity and translation', () => {
  it('matches numeric and string IDs', () => expect(isCurrentUserId(42, '42')).toBe(true));
  it('does not match different IDs', () => expect(isCurrentUserId('42', '43')).toBe(false));
  it.each([[undefined, undefined], [null, null], ['', ''], [undefined, '']])('never treats absent IDs as ownership (%j, %j)', (a, b) => {
    expect(isCurrentUserId(a, b)).toBe(false);
  });
  it('provides a local fallback without a remote image request', () => expect(resolveJobImage({})).toBe(FALLBACK_JOB_IMAGE));
  it('switches translations and falls back for unknown labels', () => {
    setLanguage('am'); expect(t('Accept Job')).not.toBe('Accept Job');
    setLanguage('en'); expect(t('Accept Job')).toBe('Accept Job');
    expect(t('audit_unknown_key')).toBe('audit_unknown_key');
  });
  it('does not render raw internal server error text', () => {
    expect(authError(new Error('SQL syntax error at private_table'))).toBe('request_failed');
  });
});
