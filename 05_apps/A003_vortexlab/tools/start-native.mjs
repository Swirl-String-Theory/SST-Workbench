/**
 * Start static web (:4173) + sst-core physics-server (:4174).
 */
import { spawn } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const toolsDir = dirname(fileURLToPath(import.meta.url));
const appRoot = join(toolsDir, '..');
const children = [];

function run(script, extraEnv = {}) {
  const child = spawn(process.execPath, [join(toolsDir, script)], {
    cwd: appRoot,
    env: { ...process.env, ...extraEnv },
    stdio: 'inherit',
    windowsHide: true
  });
  children.push(child);
  child.on('exit', (code, signal) => {
    if (shuttingDown) return;
    console.error(`[start:native] ${script} exited code=${code} signal=${signal}`);
    shutdown(code || 1);
  });
  return child;
}

let shuttingDown = false;
function shutdown(code = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of children) {
    try {
      child.kill();
    } catch {
      /* ignore */
    }
  }
  process.exit(code);
}

process.on('SIGINT', () => shutdown(0));
process.on('SIGTERM', () => shutdown(0));

run('physics-server.mjs');
run('serve.mjs');

console.log('VortexLab start:native — web http://127.0.0.1:4173 · physics http://127.0.0.1:4174');
console.log('Enable “Native SSTcore” in the lab UI (or set localStorage vortexlab.nativeSstcore=1).');
