import json, sys
mods={}
for name in ['numpy','scipy','pybind11','setuptools','pytest']:
    try:
        m=__import__(name); mods[name]=getattr(m,'__version__','ok')
    except Exception as e:
        mods[name]='MISSING: '+str(e)
print(json.dumps({'python':sys.version,'modules':mods},indent=2))
raise SystemExit(1 if any(str(v).startswith('MISSING') for v in mods.values()) else 0)
