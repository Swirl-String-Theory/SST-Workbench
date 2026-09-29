import csv, json, sys
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[1]
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.2-outputs')
    result=json.loads((out/'blind_results.json').read_text())
    mapping=json.loads((root/'reveal/HOLDOUT_MAPPING_v0.2.2.json').read_text())
    group_map=mapping['group_mapping']
    lines=['# Revealed interpretation — A050-v0.2.2','',f"Blind verdict: `{result['verdict']}`",'', '## Holdout group reveal','']
    for g in result.get('holdout_groups',[]):
        lines.append(f"- {g['group_id']} -> {group_map.get(g['group_id'],'UNKNOWN')}: status={g['status']}, branch={g['branch_mode']}, support={g['supporting_replicates']}/{g['replicate_count']}.")
    lines += ['', '## Interpretation boundary','', 'The reveal assigns anonymous confirmatory groups back to their generated reference geometries. Confirmation is still a statement about this dimensionless filament/elliptic-closure campaign. It does not establish an absolute physical scale, a unique material wave identification, or a clock mapping. Floquet/RPO inference remains outside v0.2.2.','']
    (out/'revealed_interpretation.md').write_text('\n'.join(lines),encoding='utf-8')
    print('\n'.join(lines))
if __name__=='__main__': main()
