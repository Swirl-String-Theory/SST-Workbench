#!/usr/bin/env node
// Local runtime/WebGL smoke for vortexring-lab v7.5.2.
// Usage: npm i puppeteer && node browser-smoke-v7_5_2.mjs [html]
import puppeteer from 'puppeteer';
import path from 'node:path';
import process from 'node:process';

const file = path.resolve(process.argv[2] || 'vortexring-lab-v7_5_2.html');
const url = 'file://' + file + '?selftest=1';
const errors = [];
let pass = true;
const check = (name, ok, detail = '') => {
  console.log((ok ? 'PASS  ' : 'FAIL  ') + name + (detail ? '  — ' + detail : ''));
  if (!ok) pass = false;
};

const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--allow-file-access-from-files', '--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist']
});
const page = await browser.newPage();
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push(String(e)));
await page.goto(url, { waitUntil: 'networkidle0', timeout: 90000 });

const frames = await page.evaluate(() => new Promise(res => {
  let n = 0; const tick = () => (++n >= 12 ? res(n) : requestAnimationFrame(tick));
  requestAnimationFrame(tick);
}));
check('≥10 gerenderde frames', frames >= 10, frames + ' frames');
check('geen console-/pageerrors', errors.length === 0, errors.slice(0, 4).join(' | ') || 'schoon');

await page.waitForSelector('#selftestOverlay', { timeout: 60000 });
const st = await page.$eval('#selftestOverlay', el => el.innerText);
check('zelftest zonder ❌', !st.includes('❌'), st.split('\n')[0]);
for (const t of ['T0l', 'T0m', 'T0n', 'T9j', 'T9k', 'T9l', 'T9m'])
  check('zelftest bevat ' + t, st.includes(t));
check('zelftestkop meldt v7.5.2 GESLAAGD', st.includes('ZELFTEST 7.5.2') && st.includes('GESLAAGD'));

for (const id of ['cBundleBEM', 'sBundleBoundaryMode', 'sBundleBEMQuality', 'bundleBEMReadout', 'cTopologyGuard'])
  check('nieuw UI-element #' + id, await page.$('#' + id) !== null);
check('topology guard standaard aan', await page.$eval('#cTopologyGuard', el => el.checked));
check('Niveau-C BEM standaard aan', await page.$eval('#cBundleBEM', el => el.checked));

// Activate the SST bundle and its dynamical coupling, then allow the BEM cache
// and bent representative lines to rebuild.
await page.evaluate(() => {
  const toggle = (id, value) => {
    const el = document.getElementById(id);
    if (el && el.checked !== value) { el.checked = value; el.dispatchEvent(new Event('change', { bubbles: true })); }
  };
  toggle('cSSTBundle', true);
  toggle('cBundleBEM', true);
  toggle('cBundleFlow', true);
});
await new Promise(r => setTimeout(r, 1800));
const bemText = await page.$eval('#bundleBEMReadout', el => el.textContent.trim());
check('BEM-readout rapporteert actieve solve', /BEM \d+ panelen/.test(bemText) && !/mislukt|residu te groot/i.test(bemText), bemText);

const lineCount = await page.evaluate(() => {
  // latticeGrp is lexical, not window-bound; count rendered THREE line objects
  // indirectly through the canvas state is unavailable, so verify readout + no runtime error.
  return document.getElementById('vBundleLines')?.textContent || '';
});
check('representatieve bundellijnen geconfigureerd', Number(lineCount) >= 7, String(lineCount));

// Existing on-demand reversibility diagnostic must remain operational.
await page.click('#bEpsRev');
await new Promise(r => setTimeout(r, 700));
const eps = await page.$eval('#hEpsRev', el => el.textContent.trim());
check('ε_rev geeft eindige meting bij α=0', /e[-+]\d+/i.test(eps), 'hEpsRev=' + eps);

await browser.close();
console.log(pass ? '\nBROWSER-SMOKE GROEN' : '\nBROWSER-SMOKE ROOD');
process.exit(pass ? 0 : 1);
