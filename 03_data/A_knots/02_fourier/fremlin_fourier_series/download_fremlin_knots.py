#!/usr/bin/env python3
"""Download David Fremlin knot assets from https://david.fremlin.de/knots/.

Crawls the index page, visits each knot page (3_1 … 15331), and saves every
linked asset (.fseries, .short, .scad, .stl) plus every <img> (.jpeg/.jpg/.png)
into fremlin/<page_stem>/<basename>, byte-for-byte as served.

Usage
-----
  python download_fremlin_knots.py
  python download_fremlin_knots.py --out fremlin --force
  python download_fremlin_knots.py --index https://david.fremlin.de/knots/index.htm
"""
from __future__ import annotations

import argparse
import os
import re
import time
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "download_fremlin_knots.py requires requests and beautifulsoup4\n"
        f"  pip install requests beautifulsoup4\n({e})"
    ) from e

DEFAULT_INDEX = "https://david.fremlin.de/knots/index.htm"
TARGET_EXTS = {".fseries", ".short", ".scad", ".stl", ".jpeg", ".jpg", ".png"}
# Knot page stems look like 3_1, 8_21, 12a_1202, or 15331.
KNOT_STEM_RE = re.compile(r"^(?:\d+[a-z]?_\d+|15331)$", re.IGNORECASE)
TIMEOUT = 30
USER_AGENT = "SST-Workbench-Ideal_Fremlin_Fseries/1.0 (+local research archive)"
DEFAULT_DELAY_S = 0.25


def same_dir_or_below(url: str, base_dir_url: str) -> bool:
    u, b = urlparse(url), urlparse(base_dir_url)
    return (u.netloc == b.netloc) and u.path.startswith(b.path)


def page_stem(url: str) -> str:
    """Return decoded page stem, e.g. …/3%5F1.htm -> 3_1."""
    name = Path(unquote(urlparse(url).path)).name
    stem = os.path.splitext(name)[0]
    return stem or "index"


def is_knot_page_stem(stem: str) -> bool:
    return bool(KNOT_STEM_RE.match(stem))


def asset_ext(url: str) -> str:
    return os.path.splitext(unquote(urlparse(url).path))[1].lower()


def dest_path(out_root: Path, stem: str, file_url: str) -> Path:
    filename = Path(unquote(urlparse(file_url).path)).name
    return out_root / stem / filename


def extract_asset_urls(html: str, page_url: str, base_dir_url: str) -> list[str]:
    """Collect same-dir asset URLs from <a href> and <img src>."""
    soup = BeautifulSoup(html, "html.parser")
    found: list[str] = []
    seen: set[str] = set()

    def consider(raw: str | None) -> None:
        if not raw:
            return
        href = raw.strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            return
        full = urljoin(page_url, href)
        if asset_ext(full) not in TARGET_EXTS:
            return
        if not same_dir_or_below(full, base_dir_url):
            return
        if full in seen:
            return
        seen.add(full)
        found.append(full)

    for a in soup.find_all("a", href=True):
        consider(a.get("href"))
    for img in soup.find_all("img", src=True):
        consider(img.get("src"))
    return found


def extract_child_page_urls(html: str, page_url: str, base_dir_url: str) -> list[str]:
    """Collect same-dir .htm links."""
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href.lower().endswith(".htm"):
            continue
        full = urljoin(page_url, href)
        if not same_dir_or_below(full, base_dir_url):
            continue
        if full in seen:
            continue
        seen.add(full)
        out.append(full)
    return out


def fetch_text(session: requests.Session, url: str) -> str:
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def download_file(
    session: requests.Session,
    file_url: str,
    dest: Path,
    *,
    force: bool = False,
) -> str:
    """Download one file. Returns 'skip' | 'ok'."""
    if dest.exists() and not force:
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with session.get(file_url, stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 15):
                    if chunk:
                        f.write(chunk)
            tmp.replace(dest)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
    return "ok"


def crawl(
    index_url: str = DEFAULT_INDEX,
    out_root: str | Path = "fremlin",
    *,
    force: bool = False,
    delay_s: float = DEFAULT_DELAY_S,
    session: requests.Session | None = None,
) -> dict:
    """Crawl Fremlin knot pages and download assets into out_root/<stem>/."""
    out = Path(out_root)
    own_session = session is None
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})

    base_dir = index_url if index_url.endswith("/") else index_url.rsplit("/", 1)[0] + "/"
    visited: set[str] = set()
    to_visit = [index_url]
    downloaded: set[str] = set()
    stats = {"pages": 0, "knot_pages": 0, "ok": 0, "skip": 0, "fail": 0, "assets": 0}

    try:
        while to_visit:
            url = to_visit.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                html = fetch_text(session, url)
            except Exception as e:
                print(f"[WARN] Could not fetch {url}: {e}")
                stats["fail"] += 1
                continue

            stats["pages"] += 1
            stem = page_stem(url)

            if is_knot_page_stem(stem):
                stats["knot_pages"] += 1
                for asset_url in extract_asset_urls(html, url, base_dir):
                    if asset_url in downloaded:
                        continue
                    dest = dest_path(out, stem, asset_url)
                    stats["assets"] += 1
                    try:
                        print(f"[GET] {asset_url} -> {dest}")
                        status = download_file(session, asset_url, dest, force=force)
                        downloaded.add(asset_url)
                        stats[status] = stats.get(status, 0) + 1
                        if status == "skip":
                            print("      (skip exists)")
                    except Exception as e:
                        print(f"[WARN] Could not download {asset_url}: {e}")
                        stats["fail"] += 1
                    if delay_s > 0:
                        time.sleep(delay_s)

            for child in extract_child_page_urls(html, url, base_dir):
                if child in visited or child in to_visit:
                    continue
                # Only enqueue knot pages (skip table.htm, questions.htm, …).
                if is_knot_page_stem(page_stem(child)):
                    to_visit.append(child)

            if delay_s > 0:
                time.sleep(delay_s)
    finally:
        if own_session:
            session.close()

    print(
        f"[DONE] knot_pages={stats['knot_pages']} assets={stats['assets']} "
        f"ok={stats['ok']} skip={stats['skip']} fail={stats['fail']}"
    )
    return stats


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--index",
        default=DEFAULT_INDEX,
        help=f"Fremlin knots index URL (default: {DEFAULT_INDEX})",
    )
    p.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parent / "fremlin"),
        help="Output root (default: ./fremlin next to this script)",
    )
    p.add_argument("--force", action="store_true", help="Re-download even if file exists")
    p.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_S,
        help="Delay between requests (s)",
    )
    args = p.parse_args(argv)
    crawl(args.index, args.out, force=args.force, delay_s=args.delay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
