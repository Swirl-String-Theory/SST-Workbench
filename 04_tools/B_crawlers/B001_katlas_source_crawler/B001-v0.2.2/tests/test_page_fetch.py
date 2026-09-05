import sqlite3
import tempfile
import unittest
from pathlib import Path

from katlas_source.page_fetch import select_profile_targets


class PageFetchSelectionTests(unittest.TestCase):
    def test_low_crossings_plus_unique_extras(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "catalog.sqlite3"
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE objects (id TEXT PRIMARY KEY, relpath TEXT, crossings INTEGER, kind TEXT)")
            con.executemany(
                "INSERT INTO objects(id,relpath,crossings,kind) VALUES (?,?,?,?)",
                [
                    ("3_1", "knots/03/3_1", 3, "knot"),
                    ("L6a4", "links/06/L6a4", 6, "link"),
                    ("7_4", "knots/07/7_4", 7, "knot"),
                    ("8_19", "knots/08/8_19", 8, "knot"),
                    ("9_2", "knots/09/9_2", 9, "knot"),
                    ("10_124", "knots/10/x/10_124", 10, "knot"),
                ],
            )
            con.commit(); con.close()

            rows = select_profile_targets(db, 7, ["8_19", "9_2", "10_124", "3_1", "MISSING"])
            ids = [x[0] for x in rows]
            self.assertEqual(ids[:3], ["3_1", "L6a4", "7_4"])
            self.assertEqual(ids[3:], ["8_19", "9_2", "10_124"])
            self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
