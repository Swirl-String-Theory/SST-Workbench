#!/usr/bin/env node
// browser-smoke-v7_5.mjs — lokale browser-smoke voor vortexring-lab-v7.5.
// Gebruik:  npm i puppeteer && node browser-smoke-v7_5.mjs [pad-naar-html]
// Vereist (conform v7.4b-acceptatie):
//   1. ≥10 gerenderde frames zonder console-errors of pageerrors
//   2. ?selftest=1 volledig groen, inclusief T0i, T1b en T8
//   3. nieuwe HUD-elementen aanwezig (rowGa/hGa, rowEpsRev/hEpsRev/bEpsRev)
//   4. frame-toggle raakt de solverkant niet (cBgOmega-stand ongewijzigd)
//   5. ε_rev-knop levert een eindige meting bij α=0
// De diag-reeksen-vergelijking (identieke ModelLog-diag in beide display-
// frames) blijft de gedocumenteerde handmatige check uit de spec.
import puppeteer from 'puppeteer';
import path from 'node:path';
import process from 'node:process';

const file = path.resolve(process.argv[2] || 'vortexring-lab-v7_5.html');
const url = 'file://' + file + '?selftest=1';
const errors = [];
let pass = true;
const check = (name, ok, detail = '') => {
  console.log((ok ? 'PASS  ' : 'FAIL  ') + name + (detail ? '  — ' + detail : ''));
  if (!ok) pass = false;
};

const browser = await puppeteer.launch({ headless: 'new' });
const page = await browser.newPage();
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push(String(e)));

await page.goto(url, { waitUntil: 'networkidle0', timeout: 60000 });

// 1. ≥10 frames
const frames = await page.evaluate(() => new Promise(res => {
  let n = 0; const tick = () => (++n >= 12 ? res(n) : requestAnimationFrame(tick));
  requestAnimationFrame(tick);
}));
check('≥10 gerenderde frames', frames >= 10, frames + ' frames');
check('geen console-/pageerrors', errors.length === 0, errors.slice(0, 3).join(' | ') || 'schoon');

// 2. zelftest volledig groen incl. T0i/T1b/T8
await page.waitForSelector('#selftestOverlay', { timeout: 30000 });
const st = await page.evaluate(() => document.getElementById('selftestOverlay').innerText);
check('zelftest zonder ❌', !st.includes('❌'), st.split('\n')[0]);
for (const t of ['T0i', 'T1b', 'T8 frame-equivalentie'])
  check('zelftest bevat ' + t, st.includes(t));
check('zelftestkop meldt v7.5 GESLAAGD', st.includes('ZELFTEST 7.5') && st.includes('GESLAAGD'));

// 3. nieuwe HUD-elementen
for (const id of ['rowGa', 'hGa', 'rowEpsRev', 'hEpsRev', 'bEpsRev'])
  check('HUD-element #' + id, await page.$('#' + id) !== null);

// 4. frame-toggle is puur weergave: solverkant (cBgOmega) blijft staan
const bgBefore = await page.$eval('#cBgOmega', el => el.checked);
await page.click('#frameSeg [data-frame="absolute"]');
await page.click('#frameSeg [data-frame="rotating"]');
const bgAfter = await page.$eval('#cBgOmega', el => el.checked);
check('frame-toggle laat solverkeuze ongemoeid', bgBefore === bgAfter,
      'cBgOmega ' + bgBefore + ' → ' + bgAfter);

// 5. ε_rev-meting op gebruikersactie
await page.click('#bEpsRev');
await new Promise(r => setTimeout(r, 500));
const eps = await page.$eval('#hEpsRev', el => el.textContent.trim());
check('ε_rev geeft eindige meting bij α=0', /e[-+]\d+/i.test(eps), 'hEpsRev=' + eps);

await browser.close();
console.log(pass ? '\nBROWSER-SMOKE GROEN' : '\nBROWSER-SMOKE ROOD');
process.exit(pass ? 0 : 1);
