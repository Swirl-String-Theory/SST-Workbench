from pathlib import Path
print('Candidate registry patch only. Verify next_catalog_ids.A_falsifiers locally before applying A053.')
for p in Path('registry_patch').glob('*'): print(p)
