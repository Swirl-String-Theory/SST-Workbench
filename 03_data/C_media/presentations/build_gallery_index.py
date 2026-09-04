#!/usr/bin/env python3
"""Regenerate index.html with all HTML and PNG files in this folder."""

from __future__ import annotations

import json
import re
from pathlib import Path
FOLDER = Path(__file__).resolve().parent
OUTPUT = FOLDER / "index.html"
SKIP = {"index.html"}

GITHUB_REPO = "Swirl-String-Theory/Swirl-String-Theory"
GITHUB_BASE = f"https://github.com/{GITHUB_REPO}"
SST_CORE_URL = "https://sst-core.com"
# GitHub Pages when /docs is the published folder (Settings → Pages → /docs)
GITHUB_PAGES_BASE = (
    f"https://swirl-string-theory.github.io/Swirl-String-Theory/Presentation_PDF"
)


def natural_key(text: str) -> list:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def display_name(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"_pdf(\s*\(\d+\))?$", "", stem, flags=re.IGNORECASE)
    stem = stem.replace("_", " ")
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem.title()


def slide_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        return "image"
    return "html"


def collect_files() -> list[str]:
    patterns = ("*.html", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp")
    files: list[str] = []
    for pattern in patterns:
        for path in FOLDER.glob(pattern):
            if path.name.lower() not in SKIP:
                files.append(path.name)
    return sorted(set(files), key=natural_key)


def build_entry(filename: str) -> dict:
    return {
        "file": filename,
        "title": display_name(filename),
        "type": slide_type(filename),
    }


def build_html(files: list[str]) -> str:
    entries = [build_entry(f) for f in files]
    manifest = json.dumps(entries, ensure_ascii=False, indent=2)

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SST Presentaties</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    html, body {{
      margin: 0;
      height: 100%;
      font-family: "Segoe UI", system-ui, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      overflow: hidden;
    }}
    .layout {{
      display: grid;
      grid-template-rows: auto 1fr auto;
      height: 100vh;
    }}
    header {{
      display: flex;
      align-items: center;
      gap: 0.65rem;
      padding: 0.6rem 1rem;
      background: #1e293b;
      border-bottom: 1px solid #334155;
      flex-wrap: wrap;
    }}
    header h1 {{
      margin: 0;
      font-size: 1rem;
      font-weight: 600;
      flex: 1;
      min-width: 12rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .badge {{
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      background: #334155;
      color: #94a3b8;
    }}
    .badge.image {{ background: #14532d; color: #86efac; }}
    .badge.html {{ background: #1e3a5f; color: #93c5fd; }}
    .counter {{
      font-size: 0.85rem;
      color: #94a3b8;
      white-space: nowrap;
    }}
    select {{
      max-width: min(28rem, 45vw);
      padding: 0.35rem 0.5rem;
      border-radius: 6px;
      border: 1px solid #475569;
      background: #0f172a;
      color: #e2e8f0;
      font-size: 0.85rem;
    }}
    .header-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      align-items: center;
    }}
    .header-links a {{
      color: #38bdf8;
      font-size: 0.85rem;
      text-decoration: none;
      white-space: nowrap;
    }}
    .header-links a:hover {{ text-decoration: underline; }}
    .stage {{
      position: relative;
      min-height: 0;
      background: #020617;
      overflow: hidden;
    }}
    .viewer {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      border: none;
    }}
    .viewer.hidden {{ display: none; }}
    iframe.viewer {{ background: #fff; }}
    img.viewer {{
      object-fit: contain;
      background: #0f172a;
    }}
    nav.gallery-nav {{
      display: grid;
      grid-template-columns: auto auto 1fr auto auto;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      background: #1e293b;
      border-top: 1px solid #334155;
    }}
    .nav-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      min-width: 7rem;
      padding: 0.65rem 1.25rem;
      border: none;
      border-radius: 8px;
      background: #2563eb;
      color: #fff;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s, transform 0.1s;
    }}
    .nav-btn.secondary {{
      background: #475569;
      min-width: auto;
    }}
    .nav-btn.secondary:hover:not(:disabled) {{ background: #64748b; }}
    .nav-btn:hover:not(:disabled) {{ background: #1d4ed8; }}
    .nav-btn:active:not(:disabled) {{ transform: scale(0.98); }}
    .nav-btn:disabled {{
      background: #334155;
      color: #64748b;
      cursor: not-allowed;
    }}
    .nav-hint {{
      text-align: center;
      font-size: 0.8rem;
      color: #64748b;
    }}
    @media (max-width: 900px) {{
      nav.gallery-nav {{
        grid-template-columns: 1fr 1fr;
      }}
      .nav-hint {{ grid-column: 1 / -1; }}
    }}
    @media (max-width: 640px) {{
      .nav-btn {{ min-width: 3rem; padding: 0.65rem; }}
      .nav-btn .label {{ display: none; }}
      header h1 {{ font-size: 0.9rem; }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <header>
      <span class="badge" id="type-badge">HTML</span>
      <h1 id="title">SST Presentaties</h1>
      <span class="counter" id="counter"></span>
      <select id="jump" aria-label="Kies item"></select>
      <div class="header-links">
        <a id="link-local" href="#" target="_blank" rel="noopener">Lokaal</a>
        <a href="{SST_CORE_URL}" target="_blank" rel="noopener">sst-core.com</a>
        <a id="link-github" href="{GITHUB_BASE}" target="_blank" rel="noopener">GitHub</a>
        <a id="link-pages" href="{GITHUB_PAGES_BASE}/" target="_blank" rel="noopener">GitHub Pages</a>
      </div>
    </header>
    <main class="stage">
      <iframe id="viewer-html" class="viewer hidden" title="Presentatie"></iframe>
      <img id="viewer-image" class="viewer hidden" alt="">
    </main>
    <nav class="gallery-nav" aria-label="Galerij navigatie">
      <button type="button" class="nav-btn" id="prev" aria-label="Vorige">
        <span aria-hidden="true">&#9664;</span>
        <span class="label">Vorige</span>
      </button>
      <button type="button" class="nav-btn secondary" id="random" aria-label="Willekeurige pagina">
        <span class="label">Willekeurig</span>
      </button>
      <p class="nav-hint">← → bladeren &nbsp;·&nbsp; R = willekeurig &nbsp;·&nbsp; verversen = nieuw willekeurig</p>
      <button type="button" class="nav-btn" id="next" aria-label="Volgende">
        <span class="label">Volgende</span>
        <span aria-hidden="true">&#9654;</span>
      </button>
    </nav>
  </div>
  <script>
    const SLIDES = {manifest};

    const viewerHtml = document.getElementById("viewer-html");
    const viewerImage = document.getElementById("viewer-image");
    const titleEl = document.getElementById("title");
    const typeBadge = document.getElementById("type-badge");
    const counterEl = document.getElementById("counter");
    const jumpEl = document.getElementById("jump");
    const linkLocal = document.getElementById("link-local");
    const prevBtn = document.getElementById("prev");
    const nextBtn = document.getElementById("next");
    const randomBtn = document.getElementById("random");

    let index = 0;

    function isPageReload() {{
      const nav = performance.getEntriesByType?.("navigation")?.[0];
      return nav?.type === "reload";
    }}

    function clamp(i) {{
      if (!SLIDES.length) return 0;
      return ((i % SLIDES.length) + SLIDES.length) % SLIDES.length;
    }}

    function randomIndex() {{
      if (!SLIDES.length) return 0;
      if (SLIDES.length === 1) return 0;
      let pick = Math.floor(Math.random() * SLIDES.length);
      if (pick === index) pick = (pick + 1) % SLIDES.length;
      return pick;
    }}

    function fileParam() {{
      const q = new URLSearchParams(location.search);
      const f = q.get("f");
      if (!f) return null;
      const i = SLIDES.findIndex(s => s.file === f);
      return i >= 0 ? i : null;
    }}

    function initialIndex() {{
      if (!SLIDES.length) return 0;
      if (!isPageReload()) {{
        const fromUrl = fileParam();
        if (fromUrl !== null) return fromUrl;
      }}
      return randomIndex();
    }}

    function updateUrl() {{
      const slide = SLIDES[index];
      if (!slide) return;
      const url = new URL(location.href);
      url.searchParams.set("f", slide.file);
      history.replaceState({{ index }}, "", url);
    }}

    function updateLinks(slide) {{
      linkLocal.href = slide.file;
    }}

    function showViewer(slide) {{
      const isImage = slide.type === "image";
      viewerHtml.classList.toggle("hidden", isImage);
      viewerImage.classList.toggle("hidden", !isImage);
      if (isImage) {{
        viewerHtml.removeAttribute("src");
        viewerImage.src = slide.file;
        viewerImage.alt = slide.title;
      }} else {{
        viewerImage.removeAttribute("src");
        viewerHtml.src = slide.file;
      }}
      typeBadge.textContent = isImage ? "PNG" : "HTML";
      typeBadge.className = "badge " + slide.type;
    }}

    function render() {{
      if (!SLIDES.length) {{
        titleEl.textContent = "Geen bestanden gevonden";
        counterEl.textContent = "";
        prevBtn.disabled = nextBtn.disabled = randomBtn.disabled = true;
        return;
      }}
      const slide = SLIDES[index];
      showViewer(slide);
      titleEl.textContent = slide.title;
      counterEl.textContent = `${{index + 1}} / ${{SLIDES.length}}`;
      updateLinks(slide);
      prevBtn.disabled = SLIDES.length <= 1;
      nextBtn.disabled = SLIDES.length <= 1;
      randomBtn.disabled = SLIDES.length <= 1;
      jumpEl.value = String(index);
      updateUrl();
    }}

    function goTo(i) {{
      if (!SLIDES.length) return;
      index = clamp(i);
      render();
    }}

    function goRandom() {{
      if (!SLIDES.length) return;
      index = randomIndex();
      render();
    }}

    function initSelect() {{
      jumpEl.innerHTML = "";
      SLIDES.forEach((s, i) => {{
        const opt = document.createElement("option");
        opt.value = String(i);
        const tag = s.type === "image" ? "PNG" : "HTML";
        opt.textContent = `${{i + 1}}. [${{tag}}] ${{s.title}}`;
        jumpEl.appendChild(opt);
      }});
    }}

    prevBtn.addEventListener("click", () => goTo(index - 1));
    nextBtn.addEventListener("click", () => goTo(index + 1));
    randomBtn.addEventListener("click", goRandom);
    jumpEl.addEventListener("change", () => goTo(Number(jumpEl.value)));

    document.addEventListener("keydown", (e) => {{
      if (e.target.closest("select")) return;
      if (e.key === "ArrowLeft") {{ e.preventDefault(); goTo(index - 1); }}
      if (e.key === "ArrowRight") {{ e.preventDefault(); goTo(index + 1); }}
      if (e.key === "r" || e.key === "R") {{ e.preventDefault(); goRandom(); }}
      if (e.key === "Home") {{ e.preventDefault(); goTo(0); }}
      if (e.key === "End") {{ e.preventDefault(); goTo(SLIDES.length - 1); }}
    }});

    initSelect();
    index = initialIndex();
    render();
  </script>
</body>
</html>
"""


def main() -> None:
    files = collect_files()
    html_count = sum(1 for f in files if slide_type(f) == "html")
    image_count = len(files) - html_count
    OUTPUT.write_text(build_html(files), encoding="utf-8")
    print(
        f"Wrote {OUTPUT.name}: {html_count} HTML, {image_count} images "
        f"({len(files)} total)."
    )


if __name__ == "__main__":
    main()
