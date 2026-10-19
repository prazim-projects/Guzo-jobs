import { spawn } from 'node:child_process';
import { mkdirSync, createWriteStream } from 'node:fs';
import { setTimeout as delay } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';
process.chdir(fileURLToPath(new URL('..', import.meta.url)));
mkdirSync('docs/audit/results', { recursive: true });
const log = createWriteStream('docs/audit/results/browser.log');
const server = spawn(process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '4175', '--strictPort'], {
  shell: false, env: { ...process.env, VITE_GRAPHQL_ENDPOINT: 'http://127.0.0.1:8000/graphql/' }, stdio: ['ignore', 'pipe', 'pipe'],
});
let serverError;
server.on('error', error => { serverError = error; });
server.stdout.on('data', data => log.write(data));
server.stderr.on('data', data => log.write(data));
let browser;
try {
  let ready = false;
  for (let attempt = 0; attempt < 60; attempt++) {
    if (serverError) throw serverError;
    if (server.exitCode !== null) throw new Error('Audit server could not bind port 4175; stop the existing listener and retry.');
    try { ready = (await fetch('http://127.0.0.1:4175', { signal: AbortSignal.timeout(1000) })).ok; } catch { /* retry startup */ }
    if (ready) break;
    await delay(500);
  }
  if (!ready) throw new Error('Audit server was not ready within 30 seconds');
  browser = spawn(process.execPath, ['node_modules/cypress/bin/cypress', 'run', '--config-file', 'cypress.audit.config.ts', '--browser', 'electron'], { shell: false });
  for (const stream of [browser.stdout, browser.stderr]) stream.on('data', data => { log.write(data); process.stdout.write(data); });
  process.exitCode = await new Promise((resolveResult, reject) => {
    browser.on('error', reject); browser.on('close', code => resolveResult(code ?? 1));
  });
} finally {
  browser?.kill(); server.kill();
  await new Promise(resolveLog => log.end(resolveLog));
}
