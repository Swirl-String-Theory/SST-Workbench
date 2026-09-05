from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import sqlite3
from urllib.parse import urljoin


_PAIR_LIST = re.compile(r"\[\s*\{\s*\d+\s*,\s*\d+\s*\}(?:\s*,\s*\{\s*\d+\s*,\s*\d+\s*\})+\s*\]", re.S)
_ARC_MATH = re.compile(r"ArcPresentation\s*\[(.*?)\]", re.S | re.I)
_WIKI_MEDIA = re.compile(r"\[\[(?:File|Image)\s*:\s*([^\]|]+)", re.I)
_URL_MEDIA = re.compile(r"https?://[^\s\]\[<>'\"]+?\.(?:png|jpe?g|gif|svg|webp)(?:\?[^\s\]\[<>'\"]*)?", re.I)
_HEADING = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$", re.M)
_TAG = re.compile(r"<[^>]+>")
_WIKILINK = re.compile(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]")
_TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
_REF = re.compile(r"<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>", re.I | re.S)


def _clean_text(s: str) -> str:
    s = _REF.sub(" ", s)
    for _ in range(3):
        s = _TEMPLATE.sub(" ", s)
    s = _WIKILINK.sub(lambda m: m.group(1), s)
    s = _TAG.sub(" ", s)
    s = unescape(s)
    s = re.sub(r"'{2,5}", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()


def extract_arc_presentation(wikitext: str, rendered_text: str = "") -> list[str]:
    vals: list[str] = []
    for m in _ARC_MATH.finditer(wikitext):
        v = "ArcPresentation[" + m.group(1).strip() + "]"
        vals.append(re.sub(r"\s+", " ", v))

    combined = wikitext + "\n" + rendered_text
    for marker in re.finditer(r"Arc\s+Presentation", combined, re.I):
        tail = combined[marker.end(): marker.end() + 5000]
        m = _PAIR_LIST.search(tail)
        if m:
            vals.append(re.sub(r"\s+", " ", m.group(0)))

    # Fallback: a pair-list in a context that explicitly mentions arc presentation.
    if "arc presentation" in combined.lower():
        for m in _PAIR_LIST.finditer(combined):
            vals.append(re.sub(r"\s+", " ", m.group(0)))
    return list(dict.fromkeys(vals))


def extract_note_sections(wikitext: str) -> list[dict]:
    headings = list(_HEADING.finditer(wikitext))
    out: list[dict] = []
    for i, m in enumerate(headings):
        title = _clean_text(m.group(2))
        if "note" not in title.lower() and "view" not in title.lower():
            continue
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(wikitext)
        body = _clean_text(wikitext[start:end])
        if body:
            out.append({"heading": title, "text": body[:20000], "source": "wikitext-section"})
    return out


class _RenderedHTML(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.images: list[dict] = []
        self.links: list[dict] = []
        self.text_parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {"script", "style"}:
            self._skip_depth += 1
        if tag == "img":
            src = a.get("src")
            if src:
                self.images.append({
                    "src": urljoin(self.base_url, src),
                    "alt": a.get("alt"),
                    "title": a.get("title"),
                })
        if tag == "a":
            href = a.get("href")
            if href and (re.search(r"\.(png|jpe?g|gif|svg|webp)(?:\?|$)", href, re.I) or "/images/" in href):
                self.links.append({"href": urljoin(self.base_url, href)})
        if tag in {"p", "br", "li", "tr", "h1", "h2", "h3", "h4", "td", "th"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"p", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.text_parts.append("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            self.text_parts.append(data)

    @property
    def text(self) -> str:
        s = " ".join(self.text_parts)
        s = re.sub(r"[ \t]+", " ", s)
        s = re.sub(r"\s*\n\s*", "\n", s)
        return s.strip()


def extract_media_references(wikitext: str, html: str, page_url: str) -> list[dict]:
    refs: list[dict] = []
    for m in _WIKI_MEDIA.finditer(wikitext):
        refs.append({"type": "wiki-file", "name": m.group(1).strip()})
    for m in _URL_MEDIA.finditer(wikitext):
        refs.append({"type": "media-url", "url": m.group(0)})
    if html:
        p = _RenderedHTML(page_url)
        p.feed(html)
        for x in p.images:
            refs.append({"type": "rendered-image", **x})
        for x in p.links:
            refs.append({"type": "rendered-media-link", **x})
    # Stable de-dup based on JSON representation.
    seen = set(); out = []
    for r in refs:
        k = json.dumps(r, sort_keys=True, ensure_ascii=False)
        if k not in seen:
            seen.add(k); out.append(r)
    return out


def extract_rendered_note_context(rendered_text: str) -> list[dict]:
    """Best-effort notes from rendered text when MediaWiki stores notes via transclusion.

    Katlas often renders labels such as 'Quick Notes', 'Further Notes and Views',
    or 'Notes on presentations'. This parser keeps short text windows after such
    markers. Raw wikitext remains the provenance source, so this field is an
    enrichment rather than a replacement for the original page.
    """
    out: list[dict] = []
    lines = [x.strip() for x in rendered_text.splitlines() if x.strip()]
    for i, line in enumerate(lines):
        low = line.lower()
        if not ("quick notes" in low or "further notes" in low or "notes on presentations" in low):
            continue
        body: list[str] = []
        for nxt in lines[i + 1:i + 12]:
            nl = nxt.lower()
            if any(marker in nl for marker in ("knot presentations", "three dimensional invariants", "computer talk", "further quantum invariants")):
                break
            body.append(nxt)
        text = " ".join(body).strip()
        if text:
            out.append({"heading": line[:300], "text": text[:10000], "source": "rendered-text-window"})
    return out


def enrich_one(*, katlas_id: str, obj_dir: Path, page_url: str, alias: str | None = None) -> dict:
    wt_path = obj_dir / "page.wikitext"
    html_path = obj_dir / "page.html"
    wikitext = wt_path.read_text(encoding="utf-8", errors="replace") if wt_path.exists() else ""
    html = html_path.read_text(encoding="utf-8", errors="replace") if html_path.exists() else ""
    rendered_text = ""
    if html:
        p = _RenderedHTML(page_url)
        p.feed(html)
        rendered_text = p.text

    notes = extract_note_sections(wikitext)
    notes += [n for n in extract_rendered_note_context(rendered_text) if n not in notes]
    result = {
        "schema": "SST-KATLAS-PAGE-ENRICHMENT-1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "katlas_id": katlas_id,
        "friendly_alias": alias,
        "page_url": page_url,
        "sources": {
            "wikitext": "page.wikitext" if wt_path.exists() else None,
            "html": "page.html" if html_path.exists() else None,
        },
        "arc_presentations": extract_arc_presentation(wikitext, rendered_text),
        "semantic_notes": notes,
        "media_references": extract_media_references(wikitext, html, page_url),
    }
    (obj_dir / "page_enrichment.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    kj = obj_dir / "katlas.json"
    if kj.exists():
        data = json.loads(kj.read_text(encoding="utf-8"))
        data["page_enrichment"] = {
            "arc_presentations": result["arc_presentations"],
            "semantic_notes": result["semantic_notes"],
            "media_references": result["media_references"],
            "snapshot_files": result["sources"],
        }
        # ArcPresentation is a presentation, so also expose it beside PD/Gauss/DT/etc.
        if result["arc_presentations"]:
            data.setdefault("presentations", {})["arc"] = result["arc_presentations"]
        kj.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def sync_alias_enrichment(db_path: Path, out_root: Path, target_id: str | None = None) -> int:
    con = sqlite3.connect(db_path)
    try:
        q = "SELECT alias,target_id,relpath,canonical_relpath FROM aliases"
        args: tuple = ()
        if target_id is not None:
            q += " WHERE target_id=?"; args = (target_id,)
        rows = con.execute(q, args).fetchall()
    finally:
        con.close()
    copied = 0
    for alias, resolved_id, alias_rel, canonical_rel in rows:
        src_dir = out_root / canonical_rel
        dst_dir = out_root / alias_rel
        dst_dir.mkdir(parents=True, exist_ok=True)
        for fn in ("page.wikitext", "page.html", "page_enrichment.json", "katlas.json"):
            src = src_dir / fn
            if src.exists():
                shutil.copy2(src, dst_dir / fn)
        copied += 1
    return copied
