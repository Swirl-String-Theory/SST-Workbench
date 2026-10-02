/**
 * Headless smoke test for vortexring-lab v7.3.1
 * Run: node browser-smoke-v7.3.1.mjs [path-to-html]
 */
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.resolve(process.argv[2] || path.join(__dirname, '../v7/vortexring-lab-v7.3.1.html'));
const fileUrl = pathToFileURL(htmlPath).href + '?selftest=1';

let puppeteer;
try {
  const require = createRequire(import.meta.url);
  puppeteer = require('puppeteer');
} catch {
  console.error('FAIL: puppeteer not installed. Run: npm install puppeteer --no-save (in vortexring-lab/)');
  process.exit(1);
}

const failures = [];

function check(name, cond, detail = '') {
  if (!cond) failures.push({ name, detail });
  console.log(`${cond ? 'OK' : 'FAIL'}: ${name}${detail ? ' — ' + detail : ''}`);
}

const browser = await puppeteer.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--use-gl=angle', '--use-angle=swiftshader'],
});
try {
  const page = await browser.newPage();
  const consoleErrors = [];
  page.on('pageerror', (err) => consoleErrors.push(String(err)));
  page.on('console', (msg) => {
    if (msg.type() === 'error' && !/ERR_FILE_NOT_FOUND|ideal_knots_data/i.test(msg.text())) {
      consoleErrors.push(msg.text());
    }
  });

  await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 120000 });
  await page.waitForFunction(() => typeof window.runSelfTest === 'function', { timeout: 30000 });

  // Animation frames (ACN diag path)
  await new Promise((r) => setTimeout(r, 1500));

  check('no runtime errors during load/frames', consoleErrors.length === 0, consoleErrors.slice(0, 3).join(' | '));

  const selftest = await page.evaluate(async () => {
    const rep = window.runSelfTest();
    return { pass: rep.pass, results: rep.results, version: rep.version };
  });
  check('selftest T0–T6 all pass', selftest.pass, selftest.results?.filter((r) => !r.pass).map((r) => r.name).join(', '));
  check('selftest version 7.3.1', selftest.version === '7.3.1', selftest.version);

  const ui = await page.evaluate(() => {
    const overviewCount = document.querySelectorAll('#quickControlsDock').length;
    const collOverview = document.getElementById('collOverview');
    const title = document.querySelector('#quickControlsDock .quick-controls-title')?.textContent?.trim();
    return { overviewCount, collOverview: !!collOverview, title };
  });
  check('single OVERZICHT dock', ui.overviewCount === 1 && !ui.collOverview, `count=${ui.overviewCount} collOverview=${ui.collOverview}`);
  check('OVERZICHT title', ui.title === 'OVERZICHT', ui.title);

  // ModelLog 0.2 — intercept JSON export blob
  await page.evaluate(() => {
    window.__capturedExport = null;
    const orig = URL.createObjectURL.bind(URL);
    URL.createObjectURL = (blob) => {
      blob.text().then((t) => { window.__capturedExport = JSON.parse(t); });
      return orig(blob);
    };
    const cb = document.getElementById('cModelLog');
    if (cb) { cb.checked = true; cb.dispatchEvent(new Event('change', { bubbles: true })); }
    const acc = document.getElementById('sAcc');
    if (acc) { acc.value = String(Number(acc.value) + 1); acc.dispatchEvent(new Event('input', { bubbles: true })); }
    document.getElementById('bReset')?.click();
  });
  await page.evaluate(() => document.getElementById('bModelLogExport')?.click());
  await page.waitForFunction(() => window.__capturedExport !== null, { timeout: 5000 }).catch(() => {});

  const exportData = await page.evaluate(() => window.__capturedExport);
  check('ModelLog export schema 0.2', exportData?.schema === 'vortexlab-model-log/0.2', exportData?.schema);
  check('ModelLog has drop counters', exportData?.dropped && 'actions' in exportData.dropped, JSON.stringify(exportData?.dropped));
  check('ModelLog export action logged', exportData?.userActions?.some((a) => a.p === 'ui:click:bModelLogExport'), 'missing export action');

  // a_phys fm readout (Rosetta; does not drive integrator)
  const aPhys = await page.evaluate(() => {
    const inp = document.getElementById('sAPhys');
    const readoutBefore = document.getElementById('vA')?.textContent;
    inp.value = '1.40897017 fm';
    inp.dispatchEvent(new Event('change', { bubbles: true }));
    return {
      readout: document.getElementById('vAPhys')?.textContent,
      vAUnchanged: document.getElementById('vA')?.textContent === readoutBefore,
    };
  });
  check('a_phys fm readout', /1\.409\s*fm/i.test(aPhys.readout || ''), aPhys.readout);
  check('a_phys does not change vA readout', aPhys.vAUnchanged, String(aPhys.vAUnchanged));

  // a_sim under n=1 lock threshold unlocks coupling
  const aSimUnlock = await page.evaluate(() => {
    const lock = document.getElementById('cCoreFlowLock');
    if (lock) { lock.checked = true; lock.dispatchEvent(new Event('change', { bubbles: true })); }
    const inp = document.getElementById('sA');
    inp.value = '1.40897017e-12';
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    return {
      lockChecked: document.getElementById('cCoreFlowLock')?.checked,
      readout: document.getElementById('coreFlowReadout')?.textContent || '',
      vA: document.getElementById('vA')?.textContent || '',
    };
  });
  check('a_sim tiny value unlocks coreFlowLock', aSimUnlock.lockChecked === false, `lock=${aSimUnlock.lockChecked}`);
  check('coreFlow unlock notice', /ontgrendeld/i.test(aSimUnlock.readout), aSimUnlock.readout.slice(0, 80));

  // Incomplete input should not corrupt vA with NaN
  const safeInput = await page.evaluate(() => {
    const bad = ['1e', '', '-'];
    const samples = [];
    for (const v of bad) {
      const inp = document.getElementById('sA');
      inp.value = v;
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      const txt = document.getElementById('vA')?.textContent || '';
      samples.push({ v, txt, hasNaN: /NaN/i.test(txt) });
    }
    return samples;
  });
  check('incomplete sA input keeps vA without NaN', safeInput.every((s) => !s.hasNaN), JSON.stringify(safeInput));

  if (failures.length) {
    console.error('\nSMOKE TEST FAILED:');
    for (const f of failures) console.error(`  - ${f.name}: ${f.detail}`);
    process.exit(1);
  }
  console.log('\nPASS: browser smoke v7.3.1');
} finally {
  await browser.close();
}
