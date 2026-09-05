from __future__ import annotations
from pathlib import Path
import hashlib, json, platform, sys, time, traceback
from .parser import parse_ideal_links, select_links
from .analysis import analyze_link
from .models import jsonable
from .report import write_tables, write_plots, write_markdown_report

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def run_campaign(
    input_path: str | Path,
    output_dir: str | Path,
    cfg: dict,
    ids=None,
    all_database: bool=False,
    resume: bool=True,
) -> dict:
    input_path, outdir = Path(input_path), Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    per = outdir/"per_link"
    per.mkdir(exist_ok=True)
    links = select_links(parse_ideal_links(input_path), ids, all_database)
    results, failures = [], []
    started = time.time()
    for number, link in enumerate(links, 1):
        path = per/f"{link.link_id}.json"
        if resume and path.exists():
            results.append(json.loads(path.read_text(encoding="utf-8")))
            print(f"[{number}/{len(links)}] resume {link.link_id}", flush=True)
            continue
        print(f"[{number}/{len(links)}] analyze {link.link_id}", flush=True)
        try:
            result = jsonable(analyze_link(link, cfg))
            path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            results.append(result)
        except Exception as exc:
            failures.append({
                "link_id": link.link_id,
                "error": repr(exc),
                "traceback": traceback.format_exc(),
            })
            print(f"FAILED {link.link_id}: {exc}", flush=True)
    metadata = {
        "suite_version": "0.1.0",
        "preset": cfg.get("name", "custom"),
        "input": str(input_path),
        "input_sha256": sha256(input_path),
        "requested_ids": [x.link_id for x in links],
        "completed_ids": [x["link_id"] for x in results],
        "failures": failures,
        "elapsed_s": time.time()-started,
        "python": sys.version,
        "platform": platform.platform(),
        "config": cfg,
    }
    (outdir/"run_metadata.json").write_text(json.dumps(jsonable(metadata), indent=2), encoding="utf-8")
    if results:
        summary = write_tables(results, outdir)
        if cfg.get("plots", True):
            write_plots(summary, outdir)
        write_markdown_report(results, summary, outdir, metadata)
    return metadata
