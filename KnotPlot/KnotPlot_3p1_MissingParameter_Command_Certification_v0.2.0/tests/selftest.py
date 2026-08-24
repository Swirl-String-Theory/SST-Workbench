from pathlib import Path
import sys,re
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import analyze_results as ar

t=np.linspace(0,2*np.pi,32,endpoint=False)
a=np.c_[np.cos(t),np.sin(t),0*t]
q=np.array([[0,-1,0],[1,0,0],[0,0,1]],float)
b=a@q.T+np.array([3,4,5])
assert ar.kabsch_rms(a,b) < 1e-12
assert ar.arr_hash(a)==ar.arr_hash(a.copy())

PARAMS=('charge','hooke','power','timeincr')

for stage in ('cert','extended'):
    files=list((ROOT/'kpc'/stage).glob('*.kpc'))
    assert len(files)==12, (stage,len(files))

for p in PARAMS:
    for stage in ('cert','extended'):
        for f in (ROOT/'kpc'/stage).glob(f'{p}_*.kpc'):
            txt=f.read_text()
            assert 'load 3.1' in txt
            assert 'refine nbeads 300' in txt

            active=[]
            for q in PARAMS:
                assign=re.findall(
                    rf'(?mi)^\s*{re.escape(q)}\s*=\s*[^%\r\n]+$',
                    txt
                )
                bare=re.findall(
                    rf'(?mi)^\s*{re.escape(q)}\s+(?![=])[^%\r\n]+$',
                    txt
                )
                assert not bare, (f,q,'bare command syntax remains',bare)
                if assign:
                    active.append(q)
                    assert len(assign)==1, (f,q,assign)
            assert active==[p], (f,active)

run20=(ROOT/'run_20_extended_certified.cmd').read_text()
runall=(ROOT/'run_all.cmd').read_text()
assert 'EXTENDED_SKIPPED.flag' in run20
assert 'EXTENDED_SKIPPED.flag' in runall
assert '^& exit /b 0' not in run20

print('SELFTEST PASS: 24 KPC scripts use one-parameter `name = value` isolation; extended-skip flow validated')


# Regression: harmless startup preamble must not produce hard failures.
import run_knotplot_stage as rks

good_log = '''Current position is safe.
nothing loaded
 *** nothing to save
nothing to output

KnotPlot: Hypnagogic Software
KnotPlot> knot loaded from `3.1'
KnotPlot> knot saved to `out/foo.k'
KnotPlot> data output to file `out/foo.txt'
'''
rej, hard = rks.classify_log(good_log, 'charge')
assert rej == [], rej
assert hard == [], hard

# Regression: a real post-load save/output failure is still fatal.
bad_save_log = '''KnotPlot: Hypnagogic Software
KnotPlot> knot loaded from `3.1'
KnotPlot> *** nothing to save
'''
rej, hard = rks.classify_log(bad_save_log, 'charge')
assert rej == [], rej
assert len(hard) == 1 and 'nothing to save' in hard[0]['text'].lower(), hard

# Regression: timeincr rejection after load remains visible.
bad_param_log = '''KnotPlot: Hypnagogic Software
KnotPlot> knot loaded from `3.1'
KnotPlot> *** Unknown parameter: timeincr
'''
rej, hard = rks.classify_log(bad_param_log, 'timeincr')
assert len(rej) == 1, rej
assert hard == [], hard

print('LOG CLASSIFIER REGRESSION PASS')
