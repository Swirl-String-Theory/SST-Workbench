from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request

from .downloader import USER_AGENT
from .aliases import sync_alias_page_snapshots
from .page_enrich import enrich_one, sync_alias_enrichment


@dataclass
class PageFetchResult:
    katlas_id: str
    relpath: str
    raw_url: str
    page_url: str
    status: str
    wikitext_bytes: int = 0
    html_bytes: int = 0
    wikitext_sha256: str | None = None
    html_sha256: str | None = None
    attempts: int = 0
    error: str | None = None
    arc_count: int = 0
    note_count: int = 0
    media_count: int = 0


def raw_page_url(katlas_id: str) -> str:
    query = urllib.parse.urlencode({"title": katlas_id, "action": "raw"})
    return f"https://katlas.org/index.php?{query}"


def rendered_page_url(katlas_id: str) -> str:
    return "https://katlas.org/wiki/" + urllib.parse.quote(katlas_id, safe="_")


def _fetch_bytes(url: str, *, retries: int, backoff_seconds: float) -> tuple[bytes, int]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(1, max(1, retries) + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read(), attempt
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_error = exc
            if attempt < max(1, retries):
                time.sleep(max(0.0, backoff_seconds) * (2 ** (attempt - 1)))
    assert last_error is not None
    raise last_error


def _atomic_write(dest: Path, data: bytes) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return hashlib.sha256(data).hexdigest()


def fetch_page_snapshots(
    katlas_id: str,
    obj_dir: Path,
    *,
    delay_seconds: float = 0.8,
    retries: int = 3,
    backoff_seconds: float = 2.0,
) -> tuple[str, str, int, str, str]:
    """Fetch raw MediaWiki source + rendered HTML for one curated object."""
    raw_url = raw_page_url(katlas_id)
    page_url = rendered_page_url(katlas_id)
    raw_data, a1 = _fetch_bytes(raw_url, retries=retries, backoff_seconds=backoff_seconds)
    html_data, a2 = _fetch_bytes(page_url, retries=retries, backoff_seconds=backoff_seconds)
    raw_sha = _atomic_write(obj_dir / "page.wikitext", raw_data.decode("utf-8", errors="replace").encode("utf-8"))
    html_sha = _atomic_write(obj_dir / "page.html", html_data)
    time.sleep(max(0.0, delay_seconds))
    return raw_url, page_url, max(a1, a2), raw_sha, html_sha


def fetch_raw_page(
    katlas_id: str,
    dest: Path,
    delay_seconds: float = 0.8,
    retries: int = 3,
    backoff_seconds: float = 2.0,
) -> tuple[str, int, str]:
    """Backward-compatible raw-only fetch used by older callers/tests."""
    url = raw_page_url(katlas_id)
    data, attempt = _fetch_bytes(url, retries=retries, backoff_seconds=backoff_seconds)
    encoded = data.decode("utf-8", errors="replace").encode("utf-8")
    sha = _atomic_write(dest, encoded)
    time.sleep(max(0.0, delay_seconds))
    return url, attempt, sha


def select_profile_targets(db_path: Path, max_auto_crossings: int, extra_ids: list[str]) -> list[tuple[str, str]]:
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            """SELECT id, relpath FROM objects WHERE crossings <= ?
               ORDER BY crossings, kind, id""",
            (max_auto_crossings,),
        ).fetchall()
        seen = {row[0] for row in rows}
        for katlas_id in extra_ids:
            if katlas_id in seen:
                continue
            row = con.execute("SELECT id, relpath FROM objects WHERE id=?", (katlas_id,)).fetchone()
            if row is not None:
                rows.append(row); seen.add(katlas_id)
        return rows
    finally:
        con.close()


def fetch_profile(*, db_path: Path, out_root: Path, profile_name: str, profile: dict,
                  force: bool = False, delay_seconds: float | None = None) -> dict:
    max_auto = int(profile.get("max_auto_crossings", 7))
    extra_ids = list(profile.get("extra_ids", []))
    delay = float(profile.get("delay_seconds", 0.8) if delay_seconds is None else delay_seconds)
    retries = int(profile.get("retries", 3))
    backoff = float(profile.get("backoff_seconds", 2.0))
    targets = select_profile_targets(db_path, max_auto, extra_ids)
    present_ids = {x for x, _ in targets}
    missing_extra_ids = [x for x in extra_ids if x not in present_ids]
    results: list[PageFetchResult] = []

    for index, (katlas_id, relpath) in enumerate(targets, start=1):
        obj_dir = out_root / relpath
        wt = obj_dir / "page.wikitext"
        hp = obj_dir / "page.html"
        raw_url = raw_page_url(katlas_id)
        page_url = rendered_page_url(katlas_id)
        print(f"[fetch {index:04d}/{len(targets):04d}] {katlas_id}")
        try:
            attempts = 0
            if force or not (wt.exists() and hp.exists()):
                raw_url, page_url, attempts, raw_sha, html_sha = fetch_page_snapshots(
                    katlas_id, obj_dir, delay_seconds=delay, retries=retries, backoff_seconds=backoff
                )
                status = "FETCHED"
            else:
                raw_sha = hashlib.sha256(wt.read_bytes()).hexdigest()
                html_sha = hashlib.sha256(hp.read_bytes()).hexdigest()
                status = "SKIPPED_EXISTS"

            enrichment = enrich_one(katlas_id=katlas_id, obj_dir=obj_dir, page_url=page_url)
            sync_alias_page_snapshots(db_path, out_root, katlas_id)
            sync_alias_enrichment(db_path, out_root, katlas_id)
            results.append(PageFetchResult(
                katlas_id=katlas_id, relpath=relpath, raw_url=raw_url, page_url=page_url,
                status=status, wikitext_bytes=wt.stat().st_size if wt.exists() else 0,
                html_bytes=hp.stat().st_size if hp.exists() else 0,
                wikitext_sha256=raw_sha, html_sha256=html_sha, attempts=attempts,
                arc_count=len(enrichment["arc_presentations"]),
                note_count=len(enrichment["semantic_notes"]),
                media_count=len(enrichment["media_references"]),
            ))
        except Exception as exc:
            results.append(PageFetchResult(
                katlas_id=katlas_id, relpath=relpath, raw_url=raw_url, page_url=page_url,
                status="FAILED", attempts=retries, error=f"{type(exc).__name__}: {exc}"
            ))

    report = {
        "schema": "SST-KATLAS-PAGE-FETCH-REPORT-1.1",
        "profile": profile_name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "max_auto_crossings": max_auto,
        "extra_ids_requested": extra_ids,
        "extra_ids_missing_from_catalog": missing_extra_ids,
        "target_count": len(targets),
        "fetched": sum(r.status == "FETCHED" for r in results),
        "skipped_existing": sum(r.status == "SKIPPED_EXISTS" for r in results),
        "failed": sum(r.status == "FAILED" for r in results),
        "objects_with_arc": sum(r.arc_count > 0 for r in results),
        "objects_with_notes": sum(r.note_count > 0 for r in results),
        "objects_with_media": sum(r.media_count > 0 for r in results),
        "results": [asdict(r) for r in results],
    }
    report_path = out_root / "_catalog" / f"PAGE_FETCH_{profile_name}_REPORT.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
