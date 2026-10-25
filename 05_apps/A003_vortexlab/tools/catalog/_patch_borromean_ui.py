from pathlib import Path
import shutil
import tempfile

src = Path(__file__).with_name("vortexring-lab-v7.6.25b.html")
t = src.read_text(encoding="utf-8")
old = """    const a006=[],singles=[],links=[];
    for(const id of knotplot.ids){
      const k=knotplot.db[id],nc=knotEntryComponents(k).length,L=finiteMetaNumber(k.L),tag=k.status||'candidate';
      const isA006=String(k.family||'').startsWith('a006')||String(k.sourceRole||'').startsWith('a006');
      const short=isA006?(k.topology||id):id;
      const extras=isA006?[k.resolutionN!=null?`N${k.resolutionN}`:null,k.profile,k.chirality,k.cpMode].filter(Boolean).join(' · '):'';
      const label=`${short}${extras?' · '+extras:''}${Number.isFinite(L)?' · L='+L.toFixed(4):''}${nc>1?' · '+nc+' comp':''} · ${tag}`;
      const opt=`<option value="knotplot|${id}">${label}</option>`;
      if(isA006)a006.push(opt);else if(nc>1)links.push(opt);else singles.push(opt);
    }
    if(a006.length)kpGroups.push(`<optgroup label="A006 TWIST SEEDS">${a006.join('')}</optgroup>`);
    if(singles.length)kpGroups.push(`<optgroup label="KNOTPLOT RELAXED KNOT CANDIDATES">${singles.join('')}</optgroup>`);
    if(links.length)kpGroups.push(`<optgroup label="KNOTPLOT RELAXED LINK CANDIDATES">${links.join('')}</optgroup>`);"""
new = """    const a006=[],borromean=[],singles=[],links=[];
    for(const id of knotplot.ids){
      const k=knotplot.db[id],nc=knotEntryComponents(k).length,L=finiteMetaNumber(k.L),tag=k.status||'candidate';
      const fam=String(k.family||''),role=String(k.sourceRole||'');
      const isBorromean=fam.startsWith('a006-borromean')||role.includes('borromean');
      const isA006=!isBorromean&&(fam.startsWith('a006')||role.startsWith('a006'));
      const short=(isA006||isBorromean)?(isBorromean?`Borromean ${k.topology||id}`:(k.topology||id)):id;
      const extras=(isA006||isBorromean)?[k.resolutionN!=null?`N${k.resolutionN}`:null,k.profile,k.chirality,k.cpMode].filter(Boolean).join(' · '):'';
      const label=`${short}${extras?' · '+extras:''}${Number.isFinite(L)?' · L='+L.toFixed(4):''}${nc>1?' · '+nc+' comp':''} · ${tag}`;
      const opt=`<option value="knotplot|${id}">${label}</option>`;
      if(isBorromean)borromean.push(opt);else if(isA006)a006.push(opt);else if(nc>1)links.push(opt);else singles.push(opt);
    }
    if(a006.length)kpGroups.push(`<optgroup label="A006 TWIST SEEDS">${a006.join('')}</optgroup>`);
    if(borromean.length)kpGroups.push(`<optgroup label="A006 BORROMEAN">${borromean.join('')}</optgroup>`);
    if(singles.length)kpGroups.push(`<optgroup label="KNOTPLOT RELAXED KNOT CANDIDATES">${singles.join('')}</optgroup>`);
    if(links.length)kpGroups.push(`<optgroup label="KNOTPLOT RELAXED LINK CANDIDATES">${links.join('')}</optgroup>`);"""
if old not in t:
    raise SystemExit("UI block not found")
t = t.replace(old, new, 1)
tmp = Path(tempfile.gettempdir()) / "vortexring-lab-v7.6.25b.html.borromean"
tmp.write_text(t, encoding="utf-8")
shutil.copyfile(tmp, src)
tmp.unlink(missing_ok=True)
print("monolith borromean UI patched")
