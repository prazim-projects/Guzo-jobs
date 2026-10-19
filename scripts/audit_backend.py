"""Run backend tests with synthetic credentials and an isolated database."""
import json
import os
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / '.test-deps'), str(ROOT / 'guzo-jobs-back')]
# read_env does not override these synthetic values; do not inherit real secrets.
for key, value in {
    'SECRET_KEY': 'audit-only-synthetic-secret-key-never-use-for-deployment-123456789',
    'DEBUG': 'False', 'TELEBIRR_APP_ID': 'audit', 'TELEBIRR_APP_KEY': 'audit',
    'TELEBIRR_MERCHANT_ID': 'audit', 'TELEBIRR_NOTIFY_URL': 'https://example.invalid/notify',
    'TELEBIRR_RECEIVER_NAME': 'Audit Receiver', 'TELEBIRR_RECEIVER_PHONE': '251900001234',
    'EMAIL_BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
    'DJANGO_SETTINGS_MODULE': 'guzo_jobs_backend.audit_settings',
}.items():
    os.environ[key] = value

import django
django.setup()
from django.test.runner import DiscoverRunner


class AuditResult(unittest.TextTestResult):
    records = []

    def startTest(self, test):
        self.started = time.perf_counter()
        super().startTest(test)

    def record(self, test, status, detail=''):
        self.records.append({'test': test.id(), 'status': status,
                             'durationMs': round((time.perf_counter() - self.started) * 1000, 2),
                             'detail': detail})

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, 'passed')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, 'failed', self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, 'error', self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, 'skipped', reason)


    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.record(subtest, 'failed' if issubclass(err[0], test.failureException) else 'error',
                        self._exc_info_to_string(err, test))


class AuditRunner(DiscoverRunner):
    def get_resultclass(self):
        return AuditResult


if __name__ == '__main__':
    output = ROOT / 'docs' / 'audit' / 'results'
    output.mkdir(parents=True, exist_ok=True)
    if '--deploy' in sys.argv:
        from django.core.checks import Tags, run_checks
        from django.test import override_settings
        # The harness must override hosts for testserver; audit the shipped value separately.
        from guzo_jobs_backend import settings as app_settings
        # Test HTTP requests disable redirects; deployment checks must inspect shipped values.
        with override_settings(SECURE_SSL_REDIRECT=app_settings.SECURE_SSL_REDIRECT):
            issues = run_checks(tags=[Tags.security], include_deployment_checks=True)
        records = [{'id': issue.id, 'message': issue.msg} for issue in issues]
        if not app_settings.ALLOWED_HOSTS:
            records.append({'id': 'audit.ALLOWED_HOSTS', 'message': 'Shipped default settings have an empty ALLOWED_HOSTS.'})
        (output / 'deployment.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
        for record in records:
            print(f"{record['id']}: {record['message']}")
        sys.exit(bool(records))
    started = time.perf_counter()
    try:
        failures = AuditRunner(verbosity=2, interactive=False).run_tests(['api'])
    finally:
        (output / 'backend.json').write_text(json.dumps({
            'durationSeconds': round(time.perf_counter() - started, 3),
            'environment': {'python': sys.version.split()[0], 'django': django.get_version(),
                            'database': 'isolated in-memory SQLite', 'externalServices': 'mocked'},
            'tests': AuditResult.records,
        }, indent=2), encoding='utf-8')
    sys.exit(bool(failures))
