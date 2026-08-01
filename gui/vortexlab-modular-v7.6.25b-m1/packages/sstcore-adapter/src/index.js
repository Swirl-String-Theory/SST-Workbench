import { spawn } from 'node:child_process';

/**
 * Process-isolated SSTcore adapter skeleton.
 * Protocol: one JSON request on stdin, one JSON response on stdout.
 * This keeps Python/C++ failures outside the Node process during migration.
 */
export function runSstcoreProcess(request, options = {}) {
  const executable = options.executable ?? process.env.SSTCORE_EXECUTABLE;
  if (!executable) {
    throw new Error('Set SSTCORE_EXECUTABLE to the SSTcore CLI path.');
  }
  const args = options.args ?? ['serve-once', '--format', 'json'];
  return new Promise((resolve, reject) => {
    const child = spawn(executable, args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: true,
      shell: false
    });
    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', chunk => { stdout += chunk; });
    child.stderr.on('data', chunk => { stderr += chunk; });
    child.once('error', reject);
    child.once('close', code => {
      if (code !== 0) {
        reject(new Error(`SSTcore exited with code ${code}: ${stderr.trim()}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`Invalid SSTcore JSON response: ${error.message}`));
      }
    });
    child.stdin.end(JSON.stringify(request));
  });
}
