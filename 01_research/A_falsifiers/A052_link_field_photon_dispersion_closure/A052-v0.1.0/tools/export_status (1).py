import json, pathlib
p=pathlib.Path('outputs/revealed/verdict.json')
print(json.dumps(json.loads(p.read_text()),indent=2) if p.exists() else 'no reveal verdict')
