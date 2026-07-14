# Vortexlab vendor assets (CDN fallback)

Plaats hier lokale kopieën voor offline gebruik:

- `three.min.js` — Three.js r128 (https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js)
- `katex.min.js`, `katex.min.css`, `auto-render.min.js` — KaTeX 0.16.9
```html
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.17.0/dist/katex.min.css" integrity="sha384-vlBdW0r3AcZO/HboRPznQNowvexd3fY8qHOWkBi5q7KGgqJ+F48+DceybYmrVbmB" crossorigin="anonymous">

    <!-- The loading of KaTeX is deferred to speed up page rendering -->
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.17.0/dist/katex.min.js" integrity="sha384-AtrdNsnxl/75rvBneBVH7DtOvCxSVahR2zWqle1coBKd8DEmLoviqNeJSx64gNAs" crossorigin="anonymous"></script>

    <!-- To automatically render math in text elements, include the auto-render extension: -->
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.17.0/dist/contrib/auto-render.min.js" integrity="sha384-bjyGPfbij8/NDKJhSGZNP/khQVgtHUE5exjm4Ydllo42FwIgYsdLO2lXGmRBf5Mz" crossorigin="anonymous"
        onload="renderMathInElement(document.body);"></script>
```
Het HTML-bestand probeert eerst `vendor/`, daarna CDN.