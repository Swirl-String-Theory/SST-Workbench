from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.error
import urllib.request

USER_AGENT = "SST-Katlas-Source/0.1 (offline research catalog importer)"

@dataclass
class DownloadResult:
    name: str
    url: str
    path: str
    bytes: int
    sha256: str
    downloaded_utc: str
    status: str
    etag: str | None = None
    last_modified: str | None = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, name: str, retries: int = 4) -> DownloadResult:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        try:
            headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
            mode = "wb"
            if part.exists() and part.stat().st_size > 0:
                headers["Range"] = f"bytes={part.stat().st_size}-"
                mode = "ab"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as response:
                # If Range was ignored, start from zero to prevent duplicate bytes.
                if mode == "ab" and getattr(response, "status", 200) != 206:
                    mode = "wb"
                with part.open(mode) as out:
                    shutil.copyfileobj(response, out, length=1024 * 1024)
                etag = response.headers.get("ETag")
                last_modified = response.headers.get("Last-Modified")
            part.replace(dest)
            return DownloadResult(
                name=name, url=url, path=str(dest), bytes=dest.stat().st_size,
                sha256=sha256_file(dest),
                downloaded_utc=datetime.now(timezone.utc).isoformat(),
                status="downloaded", etag=etag, last_modified=last_modified,
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == retries:
                raise RuntimeError(f"Download failed after {retries} attempts: {url}: {exc}") from exc
            time.sleep(min(2 ** attempt, 10))
    raise AssertionError("unreachable")


def write_manifest(results: list[DownloadResult], path: Path) -> None:
    path.write_text(json.dumps({
        "schema": "SST-KATLAS-SOURCE-MANIFEST-1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "files": [r.__dict__ for r in results],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
