#!/usr/bin/env node
// Local runtime/WebGL smoke for vortexring-lab v7.5.4.
// Usage: node browser-smoke-v7_5_4.mjs [html]
import { createRequire } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const file = path.resolve(process.argv[2] || path.join(__dirname, '../v7/vortexring-lab-v7_5_4.html'));
const url = pathToFileURL(file).href + '?selftest=1';

let puppeteer;
try {
  puppeteer = createRequire(import.meta.url)('puppeteer');
} catch {
  console.error('FAIL: puppeteer not installed. Run: npm install puppeteer --no-save');
  process.exit(1);
}

const errors = [];
let pass = true;
const check = (name, ok, detail = '') => {
  console.log((ok ? 'PASS  ' : 'FAIL  ') + name + (detail ? '  — ' + detail : ''));
  if (!ok) pass = false;
};

const browser = await puppeteer.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--use-gl=angle', '--use-angle=swiftshader'],
});
try {
  const page = await browser.newPage();
  page.on('console', (m) => {
    if (m.type() === 'error' && !/ideal_knots_data|ERR_FILE_NOT_FOUND/i.test(m.text())) errors.push(m.text());
  });
  page.on('pageerror', (e) => errors.push(String(e)));

  await page.goto(url, { waitUntil: 'networkidle0', timeout: 120000 });
  await page.waitForFunction(() => typeof window.runSelfTest === 'function', { timeout: 30000 });

  const frames = await page.evaluate(() => new Promise((res) => {
    let n = 0;
    const tick = () => (++n >= 12 ? res(n) : requestAnimationFrame(tick));
    requestAnimationFrame(tick);
  }));
  check('≥10 gerenderde frames', frames >= 10, String(frames) + ' frames');
  check('geen console-/pageerrors', errors.length === 0, errors.slice(0, 3).join(' | ') || 'schoon');

  const selftest = await page.evaluate(() => {
    const rep = window.runSelfTest();
    return { pass: rep.pass, version: rep.version, failed: rep.results?.filter((r) => !r.pass).map((r) => r.name) };
  });
  check('selftest pass', selftest.pass, selftest.failed?.join(', '));
  check('selftest version 7.5.4', selftest.version === '7.5.4', selftest.version);

  for (const id of ['scaleProbeRow', 'sScaleProbe', 'scaleProbePreset', 'cTopologyGuard', 'cBundleBEM']) {
    check('UI #' + id, await page.$('#' + id) !== null);
  }

  const scaleProbe = await page.evaluate(() => {
    const inp = document.getElementById('sScaleProbe');
    if (!inp) return { ok: false };
    inp.value = 'planck';
    inp.dispatchEvent(new Event('change', { bubbles: true }));
    const v = document.getElementById('vScaleProbe')?.textContent || '';
    return { ok: /1\.616/.test(v) || /e-35/.test(v), v };
  });
  check('Planck scale probe readout', scaleProbe.ok, scaleProbe.v);
} finally {
  await browser.close();
}

if (!pass) process.exit(2);
console.log('\nPASS: browser smoke v7.5.4');
