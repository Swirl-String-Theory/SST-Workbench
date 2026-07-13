/**
 * Headless smoke test for vortexring-lab v7.4.2
 * Run: node browser-smoke-v7.4.2.mjs [path-to-html]
 */
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.resolve(process.argv[2] || path.join(__dirname, 'vortexring-lab-v7.4.2.html'));
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
    if (msg.type() === 'error' && !/ideal_knots_data|ERR_FILE_NOT_FOUND/i.test(msg.text())) {
      consoleErrors.push(msg.text());
    }
  });

  await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 120000 });
  await page.waitForFunction(() => typeof window.runSelfTest === 'function', { timeout: 30000 });
  await new Promise((r) => setTimeout(r, 1500));

  check('no runtime errors during load/frames', consoleErrors.length === 0, consoleErrors.slice(0, 3).join(' | '));

  const selftest = await page.evaluate(() => {
    const rep = window.runSelfTest();
    return { pass: rep.pass, results: rep.results, version: rep.version };
  });
  check('selftest pass', selftest.pass, selftest.results?.filter((r) => !r.pass).map((r) => r.name).join(', '));
  check('selftest version 7.4.2', selftest.version === '7.4.2', selftest.version);

  const ui = await page.evaluate(() => {
    const overviewCount = document.querySelectorAll('#quickControlsDock').length;
    const gpPanels = document.querySelectorAll('#gpDeltaPanel').length;
    const rowOmegas = !!document.getElementById('rowOmegas');
    const bundlePanel = !!document.getElementById('sstBundlePanel');
    return { overviewCount, gpPanels, rowOmegas, bundlePanel };
  });
  check('single OVERZICHT dock', ui.overviewCount === 1, `count=${ui.overviewCount}`);
  check('exactly one GP-Δ panel', ui.gpPanels === 1, `count=${ui.gpPanels}`);
  check('bundle UI elements present', ui.rowOmegas && ui.bundlePanel, `rowOmegas=${ui.rowOmegas} panel=${ui.bundlePanel}`);

  const exclusivity = await page.evaluate(() => {
    const bg = document.getElementById('cBgOmega');
    const flow = document.getElementById('cBundleFlow');
    const bundle = document.getElementById('cSSTBundle');
    if (!bg || !flow || !bundle) return { ok: false, detail: 'missing controls' };

    bundle.checked = true; bundle.dispatchEvent(new Event('change', { bubbles: true }));
    flow.checked = true; flow.dispatchEvent(new Event('change', { bubbles: true }));
    const afterFlow = { bg: bg.checked, flow: flow.checked };

    bg.checked = true; bg.dispatchEvent(new Event('change', { bubbles: true }));
    const afterBg = { bg: bg.checked, flow: flow.checked };

    return { ok: afterFlow.bg === false && afterFlow.flow === true && afterBg.bg === true && afterBg.flow === false, afterFlow, afterBg };
  });
  check('Ω_wall×Ω_bundle exclusivity', exclusivity.ok, JSON.stringify(exclusivity));

} finally {
  await browser.close();
}

if (failures.length) {
  console.error('\nFAILURES:', failures);
  process.exit(2);
}
console.log('\nPASS: browser smoke v7.4.2');

