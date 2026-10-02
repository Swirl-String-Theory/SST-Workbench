import { loadVortexDeps } from './load-deps.js';

await loadVortexDeps('..');
await import('./vortexring-lab-app.js');
