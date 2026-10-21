"""Produce versioned KnotPlotRC without replacing the user's supplied original.
All alias paths are relative to the NEW project root.  Run from build root.
"""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'inputs/knotplotrc_original.kps'

aliases=[]
for label,short in [('5_2','52'),('6_1','61')]:
    for n in (256,512,1024):
        for code,profile in [('S','SOFT'),('B','BALANCED'),('Q','TIGHT')]:
            name=f'SmoothClasp_{label}_{profile}_N{n:04}'
            alias=f'{short}{code}{n}'
            aliases.append(f'alias {alias} "read output/individual/{name}/{name}_LOAD.kpc"')
            aliases.append(f'alias {alias}go32 "{alias}; go 32"')
# Preserve old 52N/52R/52T conveniences but now point to v0.2.3 profiles.
for label,short in [('5_2','52'),('6_1','61')]:
    for n in (256,512,1024):
        for old,profile in [('N','TIGHT'),('R','SOFT'),('T','BALANCED')]:
            name=f'SmoothClasp_{label}_{profile}_N{n:04}'
            alias=f'{short}{old}{n}'
            aliases.append(f'alias {alias} "read output/individual/{name}/{name}_LOAD.kpc"')
            aliases.append(f'alias {alias}go32 "{alias}; go 32"')

prefix='% SST-SMOOTHCLASP-v0.2.3 BEGIN\n% Paths assume KnotPlot working directory is this v0.2.3 folder.\n'
prefix+='alias sstbase "show backdrop; mode cbff; bradius = 0.2; cradius = 0.1; tanf = on; tanmag = 9; stusplit = 0; dstep = 1; close = 0.20; max-dr = 0.02"\n'
prefix+='alias .user-reset "sstbase"\n'
block=prefix+'\n'.join(aliases)+'\n% SST-SMOOTHCLASP-v0.2.3 END\n'
(ROOT/'presets/sst_smoothclasp_v023.kps').write_text(block,encoding='ascii')
raw=source.read_text(encoding='utf-8')
# Remove old aliases referencing v0.2.2 files; keep unrelated aliases untouched.
raw=re.sub(r'^alias\s+(?:52|61)[NRT](?:256|512|1024)(?:go32)?\s+.*\n','',raw,flags=re.M)
raw=re.sub(r'^alias sstbase\s+.*\n','',raw,flags=re.M)
raw=re.sub(r'^alias \.user-reset\s+.*\n','',raw,flags=re.M)
(ROOT/'presets/knotplotrc_v023_COMPLETE.kps').write_text(raw.rstrip()+'\n\n'+block,encoding='utf-8')
print('Preset aliases generated:',len(aliases),'source preserved:',source)