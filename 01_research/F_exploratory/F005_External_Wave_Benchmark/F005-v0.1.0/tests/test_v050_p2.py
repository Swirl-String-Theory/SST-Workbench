import csv, hashlib, importlib.util, json, math, tempfile, unittest, zipfile
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'data'/'f005_v050_p2.py'
spec=importlib.util.spec_from_file_location('f005_v050_p2',P)
p2=importlib.util.module_from_spec(spec);spec.loader.exec_module(p2)

class P2Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.src=self.root/'sources'/'acquisition_evidence';self.src.mkdir(parents=True)
 def tearDown(self):self.tmp.cleanup()
 def test_hash(self):
  f=self.src/'a.py';f.write_bytes(b'hello');self.assertEqual(p2.sha256_file(f),hashlib.sha256(b'hello').hexdigest())
 def test_path_escape(self):
  f=self.root/'outside.py';f.write_text('a');self.assertFalse(p2.within(f,self.src))
 def test_source_static_not_execute(self):
  p=self.src/'a.py';p.write_text('raise RuntimeError("must not execute")\nacceleration_axis_sign=1\n',encoding='utf-8')
  r=p2.source_files_audit(self.src);self.assertEqual(r['status'],'CANDIDATE_STATIC_TEXT_FOUND_REVIEW_REQUIRED');self.assertGreater(len(r['files'][0]['candidate_lines']['acceleration_axis']),0)
 def test_source_empty_block(self):
  self.assertEqual(p2.source_files_audit(self.root/'absent')['status'],'NO_ACQUISITION_FILES_SUBMITTED')
 def test_sign_missing(self):
  self.assertEqual(p2.evidence_binding({'value':None},self.root,self.src)['status'],'NOT_SUBMITTED')
 def test_sign_good_bytes_still_review(self):
  p=self.src/'a.py';p.write_text('input_acceleration = + robot_acceleration\n')
  val={'value':1,'evidence_relative_file':'a.py','evidence_sha256':p2.sha256_file(p),'start_line':1,'end_line':1}
  self.assertIn('SEMANTICS_REVIEW_REQUIRED',p2.evidence_binding(val,self.root,self.src)['status'])
 def test_sign_bad_hash(self):
  p=self.src/'a.py';p.write_text('height = -slope\n')
  val={'value':-1,'evidence_relative_file':'a.py','evidence_sha256':'0'*64,'start_line':1,'end_line':1}
  self.assertEqual(p2.evidence_binding(val,self.root,self.src)['status'],'SOURCE_HASH_NOT_ATTESTED')
 def test_sign_outside_rejected(self):
  val={'value':1,'evidence_relative_file':'../outside.py'}
  self.assertEqual(p2.evidence_binding(val,self.root,self.src)['status'],'EVIDENCE_PATH_NOT_ALLOWED')
 def test_source_loader_not_original_export(self):
  p=self.root/'sloshing_zenodo_package_v1.0.0.zip'
  with zipfile.ZipFile(p,'w') as z:z.writestr('load_dataset.py','import numpy as np\nx=np.load("INPUT_TRAIN.npy")')
  self.assertEqual(p2.zip_loader_audit(p)['status'],'INSPECTION_LOADER_ONLY_NOT_RAW_EXPORT')
 def test_refuse_big_zip(self):
  f=self.root/'DATASET.zip';f.write_bytes(b'X')
  self.assertEqual(p2.zip_loader_audit(f)['status'],'UNEXPECTED_ARCHIVE_NAME_REFUSED')
 def test_split_group_integrity(self):
  f=self.root/'split.csv';f.write_text('row_id_zero_based,proxy_component_id,partition\n1,a,DEV_TRAIN\n2,b,DEV_TRAIN\n3,c,DEV_VALIDATION\n4,d,DEV_VALIDATION\n')
  v,train=p2.split_audit(f,p2.sha256_file(f),expected_count=2,expected_total=4)
  self.assertEqual(v['status'],'LOCKED_INPUT_ONLY_SPLIT_VERIFIED');self.assertEqual(train,{1,2})
 def test_split_hash_mismatch_fails(self):
  f=self.root/'split.csv';f.write_text('any text')
  val,train=p2.split_audit(f,'0'*64)
  self.assertEqual(val['status'],'BLOCKED_SPLIT_SHA256_CHANGED');self.assertFalse(train)
 def test_split_cross_family_fails(self):
  f=self.root/'split.csv';f.write_text('row_id_zero_based,proxy_component_id,partition\n1,a,DEV_TRAIN\n2,b,DEV_TRAIN\n3,a,DEV_VALIDATION\n4,d,DEV_VALIDATION\n')
  val,_=p2.split_audit(f,p2.sha256_file(f),expected_count=2,expected_total=4)
  self.assertEqual(val['status'],'BLOCKED_SPLIT_INTEGRITY')
 def create_raw(self,count=1001):
  p=self.src/'trace.csv'
  with p.open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['time_s','height_mm'])
   for i in range(count):w.writerow([round(-1.001+i*.001,4),0.01+0.002*math.sin(i/20)])
   w.writerow([0.02,0.06])
  return p
 def test_raw_1000_screen_not_hydrodynamic_rest(self):
  p=self.create_raw();data=p2.raw_premotion_trace(p,0.0)
  self.assertEqual(data['scalar_pre_motion_1000_samples'],'PASS');self.assertFalse(data['hydrodynamic_rest_certified'])
 def test_premotion_locked_train_only(self):
  p=self.create_raw();m=self.src/'map.csv';m.write_text('row_id_zero_based,raw_csv,sha256,motion_start_time_s\n999,trace.csv,%s,0\n'%p2.sha256_file(p))
  r=p2.premotion_audit('map.csv',self.src,{1,2})
  self.assertIn('INVALID',r['status']);self.assertEqual(r['evaluated'],0)
 def test_premotion_good_train_no_auto_attest(self):
  p=self.create_raw();m=self.src/'map.csv';m.write_text('row_id_zero_based,raw_csv,sha256,motion_start_time_s\n1,trace.csv,%s,0\n'%p2.sha256_file(p))
  r=p2.premotion_audit('map.csv',self.src,{1})
  self.assertEqual(r['evaluated'],1);self.assertFalse(r['cases'][0]['hydrodynamic_rest_certified'])
 def test_premotion_bad_hash(self):
  self.create_raw();m=self.src/'map.csv';m.write_text('row_id_zero_based,raw_csv,sha256,motion_start_time_s\n1,trace.csv,%s,0\n'%('0'*64))
  r=p2.premotion_audit('map.csv',self.src,{1});self.assertEqual(r['evaluated'],0)
 def test_missing_does_not_false_pass(self):
  r=p2.main_run(self.root,self.root/'out')
  self.assertEqual(r['status'],'E0_P2_REVIEW_NOT_CERTIFIED')
  self.assertEqual(r['gates']['E0_MAIN_EULER_GATE'],'BLOCKED')
  self.assertFalse((self.root/'config'/'EULER_GEOMETRY_REQUIRED.json').exists())
 def test_output_paths(self):
  r=p2.main_run(self.root,self.root/'out')
  self.assertTrue((self.root/'out'/'p2_audit_report.json').exists())
  self.assertIn('NOT_CERTIFIED',(self.root/'out'/'P2_AUDIT_SUMMARY.md').read_text())

if __name__=='__main__':unittest.main()
