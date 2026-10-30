"""Run: python examples/consumer_python.py /path/to/extracted-atlas-or-zip

An existing falsifier can read explicitly selected, original components through
this bridge without importing E010's parser directly or changing E010 data.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pklsa_bridge import AtlasBridge

with AtlasBridge(sys.argv[1]) as bridge:
    ids=bridge.query(topology='3_1',collection='historical_v031',limit=2)
    for record_id in ids:
        description=bridge.source_summary(record_id)
        parts=bridge.load(record_id)
        print(record_id, [p.shape for p in parts],
              description['historical_topology_status'],
              description['geometry_sha256'])
    research=bridge.query(embedding='T_2_3',variant='nominal',allow_research=True,limit=1)
    for record_id in research:
        arrays=bridge.load(record_id,allow_research=True)
        print('RESEARCH ONLY',record_id,[p.shape for p in arrays])
