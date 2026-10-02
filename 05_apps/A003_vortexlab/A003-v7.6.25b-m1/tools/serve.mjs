import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize, resolve } from 'node:path';

const root = resolve(process.argv[2] ?? 'apps/web');
const port = Number(process.env.PORT ?? 4173);
const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml'
};

createServer(async (req, res) => {
  try {
    const urlPath = decodeURIComponent(new URL(req.url, `http://${req.headers.host}`).pathname);
    const relative = urlPath === '/' ? 'index.html' : urlPath.replace(/^\/+/, '');
    const filePath = resolve(root, normalize(relative));
    if (!filePath.startsWith(root)) throw new Error('Path traversal rejected.');
    const info = await stat(filePath);
    if (!info.isFile()) throw new Error('Not a file.');
    const body = await readFile(filePath);
    res.writeHead(200, {
      'Content-Type': mime[extname(filePath)] ?? 'application/octet-stream',
      'Cache-Control': 'no-store',
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Resource-Policy': 'same-origin'
    });
    res.end(body);
  } catch (error) {
    res.writeHead(404, {'Content-Type': 'text/plain; charset=utf-8'});
    res.end(`Not found: ${error.message}`);
  }
}).listen(port, '127.0.0.1', () => {
  console.log(`VortexLab modular M1: http://127.0.0.1:${port}`);
});
