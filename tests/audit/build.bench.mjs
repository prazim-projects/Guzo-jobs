import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { gzipSync } from 'node:zlib';
import { test } from 'node:test';

const root = resolve('dist/audit');
assert.ok(existsSync(join(root, 'index.html')), 'Run the audit production build before bundle benchmarks');
const walk = path => readdirSync(path).flatMap(name => {
  const child = join(path, name);
  return statSync(child).isDirectory() ? walk(child) : [child];
});
const assets = walk(root).filter(path => /\.(?:js|css)$/.test(path)).map(path => ({
  path: path.slice(root.length + 1).replaceAll('\\', '/'), bytes: statSync(path).size,
  gzipBytes: gzipSync(readFileSync(path)).length,
}));
const html = readFileSync(join(root, 'index.html'), 'utf8');
const modernHtml = html.replace(/<script\b[^>]*nomodule[\s\S]*?<\/script>/g, '');
const entryPaths = [...modernHtml.matchAll(/(?:src|href)="([^"]+\.(?:js|css))"/g)].map(match => match[1].replace(/^\//, ''));
const initial = assets.filter(asset => entryPaths.includes(asset.path));
const metrics = {
  budgets: { initialGzipKiB: 250, largestJsGzipKiB: 250, totalJsGzipKiB: 1024, totalCssGzipKiB: 100 },
  initialGzipKiB: initial.reduce((sum, a) => sum + a.gzipBytes, 0) / 1024,
  largestJsGzipKiB: Math.max(...assets.filter(a => a.path.endsWith('.js')).map(a => a.gzipBytes)) / 1024,
  totalJsGzipKiB: assets.filter(a => a.path.endsWith('.js')).reduce((s, a) => s + a.gzipBytes, 0) / 1024,
  totalCssGzipKiB: assets.filter(a => a.path.endsWith('.css')).reduce((s, a) => s + a.gzipBytes, 0) / 1024,
  assets,
  note: 'Local transfer-size budgets; initial entry uses modern scripts and CSS; total assets include both variants. Excludes transitive runtime imports. Not Web Vitals or a device-speed measurement.',
};
mkdirSync('docs/audit/results', { recursive: true });
writeFileSync('docs/audit/results/bundle.json', JSON.stringify(metrics, null, 2));
test('built HTML references a measured application entry', () => assert.ok(initial.some(a => a.path.endsWith('.js'))));
for (const key of ['initialGzipKiB', 'largestJsGzipKiB', 'totalJsGzipKiB', 'totalCssGzipKiB']) {
  test(`${key} <= ${metrics.budgets[key]} KiB`, () => assert.ok(metrics[key] <= metrics.budgets[key], `${metrics[key].toFixed(1)} KiB exceeds ${metrics.budgets[key]} KiB`));
}
