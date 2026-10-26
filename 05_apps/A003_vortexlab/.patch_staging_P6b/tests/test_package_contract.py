from pathlib import Path
import hashlib,json,re,subprocess,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
class PatchContract(unittest.TestCase):
 def test_manifest_and_sources(self):
  man=json.loads((ROOT/'manifest.json').read_text());self.assertEqual(len(man['files']),4)
  paths=set()
  for f in man['files']:
   self.assertNotIn('..',Path(f['path']).parts)
   self.assertNotIn(f['path'],paths);paths.add(f['path'])
   patch=(ROOT/'payload'/f['path']).read_bytes()
   self.assertEqual(sha(patch),f['patched_sha256'])
   self.assertRegex(f['baseline_sha256'],r'^[0-9a-f]{64}$')
 def test_controls_have_corresponding_elements(self):
  html=(ROOT/'payload/apps/web/twist-flow/index.html').read_text()
  js=(ROOT/'payload/apps/web/twist-flow/twist-flow.js').read_text()
  ids=set(re.findall(r'\bid=["\']([^"\']+)',html))
  for name in ['backgroundMode','discreteConfig','coarseLinesRow','continuumCaveat','backgroundSpacing','backgroundSide','backgroundNodes','conversionReadout']:
   self.assertIn(name,ids)
  self.assertIn("value=\"discrete\"",html)
  self.assertIn("['off','coarse','bem','discrete']",js)
 def test_runtime_hooks_and_model_qualifications(self):
  run=(ROOT/'payload/apps/web/src/legacy/vortexlab-runtime.js').read_text()
  for marker in ['window.__vlDiscreteBundleAPI','vlDiscrete.advance(dt)','vlDiscrete.restore();','vlDiscrete.isFinite()','vlDiscrete.render();','vlDiscrete.minDistance(Y)','discreteBundle:vlDiscrete.report()']:
   self.assertIn(marker,run)
  self.assertIn('RESEARCH_TRACK_NOT_EULER_CERTIFIED',run)
  self.assertIn('pinned-open-finite',run)
 def test_javascript_parsing(self):
  for file in ['apps/web/twist-flow/twist-flow.js','apps/web/src/legacy/vortexlab-runtime.js']:
   subprocess.run(['node','--check',str(ROOT/'payload'/file)],check=True,capture_output=True)
if __name__=='__main__':unittest.main()
