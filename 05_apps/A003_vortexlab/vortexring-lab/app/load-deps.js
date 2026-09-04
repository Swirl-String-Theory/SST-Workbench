/**
 * Laadt scripts met lokale vendor/ fallback naar CDN.
 * @param {string} localRel — pad relatief aan HTML (bijv. vendor/three.min.js)
 * @param {string} cdnUrl
 * @returns {Promise<void>}
 */
export function loadScriptDual(localRel, cdnUrl) {
  return new Promise((resolve, reject) => {
    const tryLoad = (src, onFail) => {
      const s = document.createElement('script');
      s.src = src;
      s.onload = () => resolve();
      s.onerror = onFail;
      document.head.appendChild(s);
    };
    tryLoad(localRel, () => tryLoad(cdnUrl, () => reject(new Error(`Failed: ${localRel} and ${cdnUrl}`))));
  });
}

export function loadStyleDual(localRel, cdnUrl) {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = localRel;
    link.onload = () => resolve();
    link.onerror = () => {
      const l2 = document.createElement('link');
      l2.rel = 'stylesheet';
      l2.href = cdnUrl;
      l2.onload = () => resolve();
      l2.onerror = () => reject(new Error(`Failed style: ${localRel}`));
      document.head.appendChild(l2);
    };
    document.head.appendChild(link);
  });
}

export async function loadVortexDeps(base = '') {
  const b = base.endsWith('/') ? base : `${base}/`;
  await loadStyleDual(`${b}vendor/katex.min.css`, 'https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css');
  await loadScriptDual(`${b}vendor/three.min.js`, 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js');
  await loadScriptDual(`${b}vendor/katex.min.js`, 'https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js');
  await loadScriptDual(`${b}vendor/auto-render.min.js`, 'https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js');
}
