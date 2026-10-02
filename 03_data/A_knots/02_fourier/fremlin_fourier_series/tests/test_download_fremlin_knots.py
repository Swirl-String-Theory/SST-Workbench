"""Offline unit tests for download_fremlin_knots (no network)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from download_fremlin_knots import (  # noqa: E402
    dest_path,
    extract_asset_urls,
    extract_child_page_urls,
    is_knot_page_stem,
    page_stem,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
BASE = "https://david.fremlin.de/knots/"
PAGE_3_1 = BASE + "3_1.htm"
INDEX = BASE + "index.htm"


def test_page_stem_decodes_percent_underscore():
    assert page_stem("https://david.fremlin.de/knots/3%5F1.htm") == "3_1"
    assert page_stem(PAGE_3_1) == "3_1"
    assert page_stem(BASE + "12a%5F1202.htm") == "12a_1202"
    assert page_stem(BASE + "15331.htm") == "15331"
    assert page_stem(INDEX) == "index"


def test_is_knot_page_stem():
    assert is_knot_page_stem("3_1")
    assert is_knot_page_stem("8_21")
    assert is_knot_page_stem("12a_1202")
    assert is_knot_page_stem("15331")
    assert not is_knot_page_stem("index")
    assert not is_knot_page_stem("table")
    assert not is_knot_page_stem("questions")


def test_extract_assets_from_3_1_includes_imgs_and_anchors():
    html = (FIXTURES / "knot_3_1.htm").read_text(encoding="utf-8")
    urls = extract_asset_urls(html, PAGE_3_1, BASE)
    basenames = sorted(Path(u).name for u in urls)
    # Images only via <img>, not <a>
    assert "knot.3_1.jpeg" in basenames
    assert "knot.3_1u.jpeg" in basenames
    assert "knot.3_1p.jpeg" in basenames
    # Anchors
    assert "knot.3_1.fseries" in basenames
    assert "knot.3_1u.fseries" in basenames
    assert "knot.3_1p.fseries" in basenames
    assert "knot.3_1.short" in basenames
    assert "knot.3_1.scad" in basenames
    assert "knot.3_1.stl" in basenames
    # External knotinfo / openscad links must be excluded
    assert all(u.startswith(BASE) for u in urls)
    assert len(urls) == 15  # 3 jpeg + 3 short + 3 fseries + 3 scad + 3 stl


def test_extract_child_pages_from_index_filters_and_decodes():
    html = (FIXTURES / "index.htm").read_text(encoding="utf-8")
    children = extract_child_page_urls(html, INDEX, BASE)
    stems = [page_stem(u) for u in children]
    assert "3_1" in stems
    assert "4_1" in stems
    assert "12a_1202" in stems
    assert "15331" in stems
    assert "table" in stems
    assert "questions" in stems
    knot_only = [s for s in stems if is_knot_page_stem(s)]
    assert set(knot_only) == {"3_1", "4_1", "12a_1202", "15331"}


def test_dest_path_layout():
    p = dest_path(Path("fremlin"), "3_1", BASE + "knot.3_1.fseries")
    assert p == Path("fremlin") / "3_1" / "knot.3_1.fseries"


def test_index_thumbnail_not_treated_as_knot_asset_folder():
    """Thumbnails on the index stay on the index page; crawl only saves on knot pages."""
    html = (FIXTURES / "index.htm").read_text(encoding="utf-8")
    # If someone mistakenly extracted index assets, they'd get thumbnails —
    # crawl() must only call extract_asset_urls on knot stems.
    assert not is_knot_page_stem(page_stem(INDEX))
    urls = extract_asset_urls(html, INDEX, BASE)
    assert any(u.endswith("knot.3_1.thumbnail.jpeg") for u in urls)
