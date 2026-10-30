from pathlib import Path
import hashlib, json, tempfile, unittest
import numpy as np
from sst_pklsa.combined_atlas import (CombinedSeedAtlas, AtlasIntegrityError, safe_path,
    load_ruban_component, geometry_sha256, SCHEMA, sha, valid_components)
from build_combined import checked_copy, write


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        t=np.arange(1024)*2*np.pi/1024
        self.points=np.column_stack((np.cos(t),np.sin(t),np.zeros_like(t)))
        self.parts=[self.points+[0,0,i] for i in range(3)]
        components=[]
        for i,p in enumerate(self.parts):
            f=self.root/f'c{i}.xyz';np.savetxt(f,p,fmt='%.17g')
            components.append({'component_index':i,'path':f.name,'sha256':sha(f),'point_count':1024})
        self.record={'id':'RUBAN_v036_test_nominal','collection':'ruban_v036','source_seed_id':'test',
            'variant':'nominal','parent_id':None,'component_count':3,'component_points':[1024]*3,
            'components':components,'research_only':True,'production_admission':False,
            'state':'RESEARCH_GEOMETRY_UNADMITTED','dynamic_stability':'NOT_TESTED',
            'gates':{'scientific':'NOT_RUN'},'geometry_sha256':geometry_sha256(self.parts)}
        self.save([self.record])

    def tearDown(self):self.tmp.cleanup()

    def save(self,records):
        (self.root/'COMBINED_INDEX.json').write_text(json.dumps({'schema':SCHEMA,'record_count':len(records),'records':records}))

    def test_link_component_order_and_placement_preserved(self):
        loaded=CombinedSeedAtlas(self.root).load(self.record['id'],allow_research=True)
        self.assertEqual(len(loaded),3)
        for a,b in zip(loaded,self.parts):np.testing.assert_array_equal(a,b)

    def test_research_not_default_selected(self):
        a=CombinedSeedAtlas(self.root);self.assertEqual(a.list_ids(),[])
        self.assertEqual(a.list_ids(include_research=True),[self.record['id']])

    def test_research_requires_explicit_load_opt_in(self):
        with self.assertRaises(AtlasIntegrityError):CombinedSeedAtlas(self.root).load(self.record['id'])

    def test_corrupted_raw_bytes_fail(self):
        (self.root/'c1.xyz').write_text('0 0 0\n')
        with self.assertRaises(AtlasIntegrityError):CombinedSeedAtlas(self.root).load(self.record['id'],allow_research=True)

    def test_missing_component_fails(self):
        (self.root/'c1.xyz').unlink()
        with self.assertRaises(AtlasIntegrityError):CombinedSeedAtlas(self.root).load(self.record['id'],allow_research=True)

    def test_conflicting_ids_fail(self):
        self.save([self.record,self.record])
        with self.assertRaises(AtlasIntegrityError):CombinedSeedAtlas(self.root)

    def test_unsafe_paths_fail(self):
        for value in ['../outside','C:/outside','/outside','a\\b','a/../b','a//b','a/./b','']:
            with self.subTest(value=value),self.assertRaises(AtlasIntegrityError):safe_path(self.root,value)

    def test_component_order_tampering_fails(self):
        self.record['components'].reverse();self.save([self.record])
        with self.assertRaises(AtlasIntegrityError):CombinedSeedAtlas(self.root)

    def test_missing_nominal_parent_fails(self):
        self.record.update(variant='perturbed',parent_id='missing');self.save([self.record])
        with self.assertRaises(AtlasIntegrityError):CombinedSeedAtlas(self.root)

    def test_scientific_promotion_rejected(self):
        self.record['gates']['scientific']='PASS';self.save([self.record])
        with self.assertRaises(AtlasIntegrityError):CombinedSeedAtlas(self.root)

    def test_production_admission_rejected(self):
        self.record['production_admission']=True;self.save([self.record])
        with self.assertRaises(AtlasIntegrityError):CombinedSeedAtlas(self.root)

    def test_parsed_geometry_hash_tampering_fails(self):
        self.record['geometry_sha256']='0'*64;self.save([self.record])
        with self.assertRaises(AtlasIntegrityError):CombinedSeedAtlas(self.root).load(self.record['id'],allow_research=True)

    def test_wrong_points_and_nan_rejected(self):
        for p in [self.points[:1023],self.points.copy()]:
            if len(p)==1024:p[0,0]=np.nan
            f=self.root/'bad.xyz';np.savetxt(f,p)
            with self.assertRaises(AtlasIntegrityError):load_ruban_component(f)

    def test_extra_xyz_columns_rejected(self):
        f=self.root/'bad.xyz';np.savetxt(f,np.column_stack((self.points,np.ones(1024))))
        with self.assertRaises(AtlasIntegrityError):load_ruban_component(f)

    def test_repeat_copy_identical_and_conflict_fail_closed(self):
        source=self.root/'c0.xyz';dest=self.root/'copied.xyz';expected=sha(source)
        checked_copy(source,dest,expected);before=dest.stat().st_mtime_ns
        checked_copy(source,dest,expected);self.assertEqual(before,dest.stat().st_mtime_ns)
        dest.write_text('bad')
        with self.assertRaises(AtlasIntegrityError):checked_copy(source,dest,expected)

    def test_create_only_json_never_overwrites(self):
        p=self.root/'out.json';write(p,{'kept':True})
        with self.assertRaises(FileExistsError):write(p,{'kept':False})
        self.assertTrue(json.loads(p.read_text())['kept'])

    def test_describe_cannot_mutate_internal_state(self):
        atlas=CombinedSeedAtlas(self.root);r=atlas.describe(self.record['id']);r['production_admission']=True
        self.assertFalse(atlas.describe(self.record['id'])['production_admission'])

if __name__=='__main__':unittest.main()
