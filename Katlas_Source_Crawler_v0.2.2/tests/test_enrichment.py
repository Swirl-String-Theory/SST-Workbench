import tempfile
import unittest
from pathlib import Path
from katlas_source.page_enrich import extract_arc_presentation, extract_note_sections, extract_media_references, enrich_one

class EnrichmentTests(unittest.TestCase):
    def test_extract_three_web_only_layers(self):
        wt = '''== Quick Notes ==\nThis knot is also known as Example. See also T(3,2).\n\n== Knot presentations ==\nAn Arc Presentation\n[{11,8}, {7,9}, {8,6}]\n[[File:ExampleKnot.png|thumb|Example]]\n'''
        html = '<html><body><img src="/images/a/ab/Example.svg" alt="diagram"></body></html>'
        self.assertTrue(extract_arc_presentation(wt))
        self.assertTrue(extract_note_sections(wt))
        media = extract_media_references(wt, html, 'https://katlas.org/wiki/9_2')
        self.assertGreaterEqual(len(media), 2)

    def test_enrich_merges_arc_into_katlas_json(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d/'page.wikitext').write_text('== Notes ==\nhello\nAn Arc Presentation [{1,2}, {2,3}, {3,1}]\n[[Image:X.png]]', encoding='utf8')
            (d/'page.html').write_text('<img src="/images/X.png">', encoding='utf8')
            (d/'katlas.json').write_text('{"identity":{"katlas_id":"3_1"},"presentations":{},"invariants":{}}', encoding='utf8')
            r = enrich_one(katlas_id='3_1', obj_dir=d, page_url='https://katlas.org/wiki/3_1')
            self.assertTrue(r['arc_presentations'])
            self.assertTrue((d/'page_enrichment.json').exists())
            import json
            k=json.loads((d/'katlas.json').read_text())
            self.assertIn('page_enrichment',k)
            self.assertIn('arc',k['presentations'])

if __name__ == '__main__': unittest.main()
