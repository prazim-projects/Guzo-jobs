import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, writeFileSync, createWriteStream } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
process.chdir(root);
const output = join(root, 'docs/audit/results');
mkdirSync(output, { recursive: true });
const node = process.execPath;
const npm = process.env.npm_execpath || join(dirname(node), 'node_modules/npm/bin/npm-cli.js');
const summary = { startedAt: new Date().toISOString(), node: process.version, checks: [] };

async function run(name, command, args, timeoutMs = 180_000) {
  console.log(`\nAudit: ${name}`);
  const log = createWriteStream(join(output, `${name}.log`));
  const started = Date.now();
  let stdout = '';
  const result = await new Promise(resolveResult => {
    const child = spawn(command, args, { cwd: root, shell: false,
      env: { ...process.env, VITE_GRAPHQL_ENDPOINT: 'http://127.0.0.1:8000/graphql/', NO_COLOR: '1' } });
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; child.kill(); }, timeoutMs);
    for (const stream of [child.stdout, child.stderr]) stream.on('data', chunk => {
      if (stream === child.stdout) stdout += chunk.toString();
      log.write(chunk); process.stdout.write(chunk);
    });
    child.on('error', error => { log.write(String(error)); });
    child.on('close', code => { clearTimeout(timer); resolveResult({ name, status: timedOut ? 'timeout' : code === 0 ? 'passed' : 'failed', exitCode: code,
      durationSeconds: (Date.now() - started) / 1000, log: `${name}.log` }); });
  });
  await new Promise(resolveLog => log.end(resolveLog));
  if (name === 'lint' && result.exitCode === 2) result.status = 'blocked';
  if (name === 'dependencies') {
    try {
      const report = JSON.parse(stdout);
      writeFileSync(join(output, 'dependencies.json'), JSON.stringify(report, null, 2));
      if (!report.metadata?.vulnerabilities) result.status = 'blocked';
    } catch {
      result.status = 'blocked';
    }
  }
  summary.checks.push(result);
  writeFileSync(join(output, 'summary.json'), JSON.stringify(summary, null, 2));
  return result.status === 'passed';
}

await run('frontend', node, ['node_modules/vitest/vitest.mjs', 'run', '--config', 'vitest.audit.config.ts', '--reporter=default', '--reporter=json', '--outputFile=docs/audit/results/frontend.json']);
await run('backend', process.env.AUDIT_PYTHON || 'python', ['scripts/audit_backend.py']);
await run('deployment', process.env.AUDIT_PYTHON || 'python', ['scripts/audit_backend.py', '--deploy']);
await run('typecheck', node, ['node_modules/vue-tsc/bin/vue-tsc.js', '--noEmit']);
await run('lint', node, ['node_modules/eslint/bin/eslint.js', 'src', '--format', 'json', '--output-file', 'docs/audit/results/lint.json']);
const built = await run('build', node, ['node_modules/vite/bin/vite.js', 'build', '--outDir', 'dist/audit']);
if (built) await run('bundle', node, ['--test', 'tests/audit/build.bench.mjs']);
else summary.checks.push({ name: 'bundle', status: 'blocked', reason: 'Production bundle did not build' });
if (!process.argv.includes('--offline')) {
  if (existsSync(npm)) await run('dependencies', node, [npm, 'audit', '--json', '--cache', '.tmp/npm-cache'], 90_000);
  else summary.checks.push({ name: 'dependencies', status: 'blocked', reason: 'npm CLI missing' });
} else summary.checks.push({ name: 'dependencies', status: 'not-run', reason: '--offline supplied' });
summary.finishedAt = new Date().toISOString();
writeFileSync(join(output, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('\nAudit results: docs/audit/results/summary.json. Browser suite: npm run audit:ui.');
process.exitCode = summary.checks.some(check => !['passed', 'not-run'].includes(check.status)) ? 1 : 0;
