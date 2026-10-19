import { createServer } from 'node:http';
import { readFileSync, existsSync, mkdirSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { resolve, extname, sep } from 'node:path';
import { gzipSync } from 'node:zlib';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

const arg = (key, fallback) => process.argv.find(value => value.startsWith(`--${key}=`))?.slice(key.length + 3) || fallback;
const root = resolve(arg('dir', 'dist/audit'));
const label = arg('label', 'current').replace(/[^a-z0-9_-]/gi, '-');
const output = resolve('docs/performance/results');
if (!existsSync(resolve(root, 'index.html'))) throw new Error('Build first: node node_modules/vite/bin/vite.js build --outDir dist/audit');
mkdirSync(output, { recursive: true });
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.json': 'application/json' };
// An isolated gzip-enabled static origin: no Vite/HMR or backend dependency.
const server = createServer((request, response) => {
  try {
    const path = resolve(root, `.${decodeURIComponent(new URL(request.url, 'http://localhost').pathname)}`);
    if (path !== root && !path.startsWith(root + sep)) { response.writeHead(403).end(); return; }
    const file = path === root ? resolve(root, 'index.html') : path;
    if (!existsSync(file)) { response.writeHead(404).end(); return; }
    const body = readFileSync(file);
    const compressed = /gzip/.test(request.headers['accept-encoding'] || '');
    const payload = compressed ? gzipSync(body) : body;
    response.writeHead(200, { 'Content-Type': mime[extname(file)] || 'application/octet-stream',
      'Content-Length': payload.length, 'Cache-Control': extname(file) === '.html' ? 'no-cache' : 'public, max-age=31536000, immutable',
      Vary: 'Accept-Encoding', ...(compressed ? { 'Content-Encoding': 'gzip' } : {}) });
    response.end(payload);
  } catch { response.writeHead(500).end(); }
});
await new Promise(resolveReady => server.listen(0, '127.0.0.1', resolveReady));
// Use an isolated browser profile and Node's built-in WebSocket/CDP support.
// No browser downloads, additional dependencies, or existing user tabs.
const chromePath = [process.env.CHROME_PATH,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/google-chrome', '/usr/bin/chromium',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'].find(path => path && existsSync(path));
if (!chromePath) { server.close(); throw new Error('Set CHROME_PATH to an installed Chrome or Chromium browser.'); }
mkdirSync('.tmp', { recursive: true });
const profile = mkdtempSync(resolve('.tmp', 'performance-chrome-'));
const chrome = spawn(chromePath, ['--headless=new', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', '--disable-background-networking', '--remote-debugging-port=0',
  `--user-data-dir=${profile}`, 'about:blank'], { windowsHide: true, stdio: 'ignore' });
let launchError;
chrome.on('error', error => { launchError = error; });
let socket;
let send;
try {
  const portFile = resolve(profile, 'DevToolsActivePort');
  for (let i = 0; !existsSync(portFile); i++) {
    if (launchError) throw launchError;
    if (chrome.exitCode !== null || i >= 120) throw new Error('Chrome did not start within 30 seconds');
    await delay(250);
  }
  const port = Number(readFileSync(portFile, 'utf8').split('\n')[0]);
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl);
  await new Promise((done, fail) => { socket.addEventListener('open', done, { once: true }); socket.addEventListener('error', fail, { once: true }); });
  let nextId = 0;
  let transferBytes = 0;
  const pending = new Map();
  const requests = [];
  socket.addEventListener('message', ({ data }) => {
    const message = JSON.parse(data);
    if (message.method === 'Network.loadingFinished') transferBytes += message.params.encodedDataLength;
    if (message.method === 'Network.requestWillBeSent') requests.push(message.params.request.url);
    const callback = pending.get(message.id);
    if (callback) { pending.delete(message.id); clearTimeout(callback.timer); message.error ? callback.fail(new Error(message.error.message)) : callback.done(message.result); }
  });
  send = (method, params = {}) => new Promise((done, fail) => {
    const id = ++nextId;
    const timer = setTimeout(() => { pending.delete(id); fail(new Error(`CDP timeout: ${method}`)); }, 15000);
    pending.set(id, { done, fail, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Network.enable');
  await send('Network.setCacheDisabled', { cacheDisabled: true });
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 200000, uploadThroughput: 93750, connectionType: 'cellular4g' });
  await send('Page.addScriptToEvaluateOnNewDocument', { source: `
    window.__loadAudit = { lcp: 0, shifts: [], tasks: [] };
    new PerformanceObserver(list => { for (const e of list.getEntries()) window.__loadAudit.lcp = e.startTime; }).observe({type:'largest-contentful-paint', buffered:true});
    new PerformanceObserver(list => { for (const e of list.getEntries()) if (!e.hadRecentInput) window.__loadAudit.shifts.push({time:e.startTime,value:e.value}); }).observe({type:'layout-shift', buffered:true});
    new PerformanceObserver(list => { for (const e of list.getEntries()) window.__loadAudit.tasks.push({start:e.startTime,duration:e.duration}); }).observe({type:'longtask', buffered:true});
  ` });
  const url = `http://127.0.0.1:${server.address().port}/`;
  await send('Page.navigate', { url });
  let sample;
  for (let i = 0; i < 120; i++) {
    await delay(250);
    const result = await send('Runtime.evaluate', { returnByValue: true, expression: `JSON.stringify({ready:document.readyState,now:performance.now(),fcp:performance.getEntriesByName('first-contentful-paint')[0]?.startTime,...window.__loadAudit})` });
    sample = JSON.parse(result.result.value);
    if (sample.ready === 'complete' && sample.fcp && sample.lcp && sample.now >= 8000) break;
  }
  if (!sample?.fcp || !sample.lcp || sample.ready !== 'complete') throw new Error('Page never completed with measurable FCP and LCP');
  let cls = 0, session = 0, sessionStart = 0, lastShift = -Infinity;
  for (const shift of sample.shifts) {
    if (shift.time - lastShift > 1000 || shift.time - sessionStart > 5000) { session = 0; sessionStart = shift.time; }
    session += shift.value; cls = Math.max(cls, session); lastShift = shift.time;
  }
  const budgets = { fcpMs: 1800, lcpMs: 2500, blockingMs: 200, cls: 0.1, transferBytes: 150 * 1024 };
  const metrics = { fcpMs: sample.fcp, lcpMs: sample.lcp,
    blockingMs: sample.tasks.reduce((sum, task) => sum + Math.max(0, task.start + task.duration - Math.max(task.start, sample.fcp) - 50), 0), cls, transferBytes };
  const summary = { label, measuredAt: new Date().toISOString(), browser: await send('Browser.getVersion'),
    metrics, budgets, settings: { cpuSlowdown: 4, latencyMs: 150, downloadBitsPerSecond: 1600000, viewport: '390x844', observedUntilMs: sample.now, cache: 'disabled' },
    checks: Object.entries(budgets).map(([name, budget]) => ({ name, passed: metrics[name] <= budget, actual: metrics[name], budget })),
    requests,
    note: 'Cold first-visit onboarding, gzip-enabled production build, applied Chrome throttling. Blocking time sums long-task excess over 50ms from FCP through the observation window (at least 8 seconds); it is not Lighthouse TBT/TTI. Local lab result, not field data or authenticated-route performance.' };
  writeFileSync(resolve(output, `${label}-chrome.json`), JSON.stringify(summary, null, 2));
  const screenshot = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(resolve(output, `${label}-chrome.png`), Buffer.from(screenshot.data, 'base64'));
  console.log(JSON.stringify({ metrics, checks: summary.checks }, null, 2));
  if (process.argv.includes('--check') && summary.checks.some(check => !check.passed)) process.exitCode = 1;
} finally {
  if (send && socket?.readyState === WebSocket.OPEN) { try { await send('Browser.close'); } catch { /* Browser may close before its reply. */ } }
  socket?.close();
  chrome.kill();
  await new Promise(resolveClosed => server.close(resolveClosed));
  // Only remove the temporary profile created above, never a user's profile.
  if (profile.startsWith(resolve('.tmp') + sep)) {
    try { rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 }); } catch { /* Locked browser files remain in ignored .tmp. */ }
  }
}
