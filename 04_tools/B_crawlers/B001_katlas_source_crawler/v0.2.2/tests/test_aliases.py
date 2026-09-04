import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from katlas_source.aliases import build_friendly_aliases, friendly_alias_relpath, sync_alias_page_snapshots


class FriendlyAliasTests(unittest.TestCase):
    def _db(self, td: str):
        db = Path(td) / "catalog.sqlite3"
        con = sqlite3.connect(db)
        con.executescript("""
            CREATE TABLE objects(
                id TEXT PRIMARY KEY, kind TEXT, crossings INTEGER, family TEXT,
                ordinal INTEGER, table_name TEXT, dataset TEXT, relpath TEXT,
                page_url TEXT, pd TEXT, gauss TEXT, dt TEXT, conway TEXT, braid TEXT
            );
            CREATE TABLE aliases(
                alias TEXT PRIMARY KEY, target_id TEXT, crossings INTEGER,
                relpath TEXT, canonical_relpath TEXT, reason TEXT
            );
        """)
        return db, con

    def test_direct_alias_for_sharded_11_crossing_knot(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "Katlas_Source"
            canonical = out / "knots/11/alternating/0351-0400/K11a367"
            canonical.mkdir(parents=True)
            (canonical / "katlas.json").write_text('{"identity":{"katlas_id":"K11a367"}}', encoding="utf-8")
            (canonical / "source.rdf.nt").write_text("rdf", encoding="utf-8")
            db, con = self._db(td)
            con.execute(
                "INSERT INTO objects VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("K11a367","knot",11,"alternating",367,"Hoste-Thistlethwaite","Knots11",
                 "knots/11/alternating/0351-0400/K11a367","https://katlas.org/wiki/K11a367",
                 None,None,None,None,None),
            )
            cfg = {"friendly_knot_aliases":[{"alias":"11_1","target_id":"K11a367","reason":"favorite"}]}
            results = build_friendly_aliases(cfg, out, con)
            con.commit(); con.close()
            self.assertEqual(results[0]["status"], "CREATED")
            alias_dir = out / "knots/11/11_1"
            self.assertTrue((alias_dir / "katlas.json").exists())
            self.assertTrue((alias_dir / "source.rdf.nt").exists())
            meta = json.loads((alias_dir / "ALIAS.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["target_id"], "K11a367")
            self.assertEqual(friendly_alias_relpath("11_1", 11).as_posix(), "knots/11/11_1")

            (canonical / "page.wikitext").write_text("page", encoding="utf-8")
            copied = sync_alias_page_snapshots(db, out, "K11a367")
            self.assertEqual(copied, 1)
            self.assertEqual((alias_dir / "page.wikitext").read_text(), "page")

    def test_10_crossing_same_id_can_have_direct_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "Katlas_Source"
            canonical = out / "knots/10/rolfsen/0001-0050/10_1"
            canonical.mkdir(parents=True)
            (canonical / "katlas.json").write_text('{"identity":{"katlas_id":"10_1"}}', encoding="utf-8")
            db, con = self._db(td)
            con.execute(
                "INSERT INTO objects VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("10_1","knot",10,None,1,"Rolfsen","Rolfsen","knots/10/rolfsen/0001-0050/10_1",
                 "https://katlas.org/wiki/10_1",None,None,None,None,None),
            )
            cfg = {"friendly_knot_aliases":[{"alias":"10_1","target_id":"10_1","reason":"favorite"}]}
            build_friendly_aliases(cfg, out, con)
            con.commit(); con.close()
            self.assertTrue((out / "knots/10/10_1/ALIAS.json").exists())


if __name__ == "__main__":
    unittest.main()
