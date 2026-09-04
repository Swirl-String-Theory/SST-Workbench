from __future__ import annotations
from pathlib import Path
import csv, json, math
import numpy as np

def _write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

def _read_csv(path: Path) -> list[dict]:
    with Path(path).open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def analytic_signal_hilbert(x: np.ndarray) -> np.ndarray:
    # FFT Hilbert transform, matching the standard analytic-signal construction.
    x=np.asarray(x, dtype=float)
    n=len(x)
    X=np.fft.fft(x)
    h=np.zeros(n, dtype=float)
    if n % 2 == 0:
        h[0]=1.0
        h[n//2]=1.0
        h[1:n//2]=2.0
    else:
        h[0]=1.0
        h[1:(n+1)//2]=2.0
    return np.fft.ifft(X*h)

def _local_extrema(y: np.ndarray, order: int = 2):
    ymax=[]
    ymin=[]
    n=len(y)
    for i in range(order, n-order):
        w=y[i-order:i+order+1]
        if y[i] >= np.max(w):
            ymax.append(i)
        if y[i] <= np.min(w):
            ymin.append(i)
    return np.array(ymax,dtype=int), np.array(ymin,dtype=int)

def _poly_envelope(t, y, idx, degree):
    if len(idx) < degree+1:
        degree=max(1, min(degree, len(idx)-1))
    if degree < 1:
        raise ValueError("Not enough extrema to fit envelope.")
    coef=np.polyfit(t[idx], y[idx], degree)
    return np.polyval(coef, t), coef

def reconstruct_phase_from_population(
    raw_csv: Path,
    out_dir: Path,
    envelope_degree: int = 7,
    phase_degree: int = 3,
    exclude_edge_cycles: int = 1,
    max_iterations: int = 25,
) -> dict:
    rows=_read_csv(raw_csv)
    if not rows:
        raise ValueError("No population rows found.")
    # Accepted column aliases.
    def pick(r, names):
        for n in names:
            if n in r and r[n] not in ("",None):
                return r[n]
        raise KeyError(f"Missing any of columns {names}")
    data=[]
    for r in rows:
        t=float(pick(r,("twoT_s","2T_s","twoT_ms","2T_ms")))
        if ("twoT_ms" in r or "2T_ms" in r) and not ("twoT_s" in r or "2T_s" in r):
            t *= 1e-3
        pop=float(pick(r,("population_outport1","population","P","population_percent")))
        if "population_percent" in r and "population_outport1" not in r and "population" not in r and "P" not in r:
            pop *= 0.01
        sem=None
        for n in ("sem_population","SEM","sem","sem_percent"):
            if n in r and r[n] not in ("",None):
                sem=float(r[n])
                if n=="sem_percent":
                    sem*=0.01
                break
        data.append((t,pop,sem))
    data.sort(key=lambda x:x[0])
    t=np.array([x[0] for x in data],float)
    y=np.array([x[1] for x in data],float)
    sem=np.array([np.nan if x[2] is None else x[2] for x in data],float)

    if len(t) < 40:
        raise ValueError("At least 40 population points are required for robust chirped-phase extraction.")

    max_idx,min_idx=_local_extrema(y,order=2)
    if len(max_idx)<4 or len(min_idx)<4:
        raise ValueError("Too few local extrema found for envelope reconstruction.")

    upper, upper_coef=_poly_envelope(t,y,max_idx,envelope_degree)
    lower, lower_coef=_poly_envelope(t,y,min_idx,envelope_degree)
    mean=0.5*(upper+lower)
    amp=0.5*(upper-lower)
    amp=np.maximum(amp, 1e-6)
    yn=(y-mean)/amp
    yn=np.clip(yn,-1.2,1.2)

    z=analytic_signal_hilbert(yn)
    phi0=np.unwrap(np.angle(z))
    # Choose orientation with increasing phase.
    if np.polyfit(t,phi0,1)[0] < 0:
        phi0=-phi0

    # Exclude first and last complete oscillation to mimic the paper's analysis.
    pmin=float(np.min(phi0))
    pmax=float(np.max(phi0))
    lo=pmin + exclude_edge_cycles*2.0*math.pi
    hi=pmax - exclude_edge_cycles*2.0*math.pi
    mask=(phi0>=lo)&(phi0<=hi)
    if np.count_nonzero(mask) < 25:
        mask=np.ones_like(t,dtype=bool)

    # Cubic initial phase fit.
    # np.polyfit returns descending powers; convert to ascending.
    init_desc=np.polyfit(t[mask],phi0[mask],phase_degree)
    c=init_desc[::-1].copy()

    # Direct Gauss-Newton fit to population with envelopes held fixed, as a
    # reproducible approximation to the final fit described by the authors.
    tm=t[mask]
    ym=y[mask]
    mm=mean[mask]
    aa=amp[mask]
    if np.any(np.isfinite(sem[mask]) & (sem[mask]>0)):
        sigma=np.where(np.isfinite(sem[mask]) & (sem[mask]>0), sem[mask], np.nanmedian(sem[mask][np.isfinite(sem[mask]) & (sem[mask]>0)]))
    else:
        sigma=np.ones_like(tm)

    X=np.column_stack([tm**k for k in range(phase_degree+1)])
    for _ in range(max_iterations):
        ph=X@c
        pred=mm+aa*np.cos(ph)
        r=(ym-pred)/sigma
        J=(aa[:,None]*np.sin(ph)[:,None]*X)/sigma[:,None]  # dr/dc
        # damped Gauss-Newton
        A=J.T@J + 1e-10*np.eye(J.shape[1])
        b=-(J.T@r)
        try:
            delta=np.linalg.solve(A,b)
        except np.linalg.LinAlgError:
            delta=np.linalg.lstsq(A,b,rcond=None)[0]
        # simple line search
        base=float(np.mean(r*r))
        accepted=False
        for scale in (1.0,0.5,0.25,0.1,0.05):
            cn=c+scale*delta
            phn=X@cn
            rn=(ym-(mm+aa*np.cos(phn)))/sigma
            if float(np.mean(rn*rn)) <= base:
                c=cn
                accepted=True
                break
        if not accepted or np.linalg.norm(delta) < 1e-12*max(1.0,np.linalg.norm(c)):
            break

    phase_all=np.column_stack([t**k for k in range(phase_degree+1)])@c
    # Force a convention with positive cubic coefficient; cosine readout does not
    # fix the overall phase sign.
    if c[3] < 0:
        c=-c
        phase_all=-phase_all

    pred=mean+amp*np.cos(phase_all)
    resid=y-pred

    # Approximate covariance of the final phase coefficients from the local
    # Gauss-Newton linearization. This is a fit uncertainty, not a full
    # experimental systematic-uncertainty model.
    phm=X@c
    Jm=(aa[:,None]*np.sin(phm)[:,None]*X)/sigma[:,None]
    rm=(ym-(mm+aa*np.cos(phm)))/sigma
    dof=max(1,len(tm)-len(c))
    red_chi2=float(np.sum(rm*rm)/dof)
    try:
        cov=np.linalg.inv(Jm.T@Jm)*red_chi2
        sigma_c3=float(math.sqrt(max(0.0,cov[3,3])))
    except np.linalg.LinAlgError:
        sigma_c3=None

    phase_rows=[
        {
            "twoT_s":float(tv),
            "population":float(pv),
            "sem_population":None if not math.isfinite(sv) else float(sv),
            "phase_fit_rad":float(ph),
            "population_fit":float(pf),
            "included_final_fit":bool(mk),
        }
        for tv,pv,sv,ph,pf,mk in zip(t,y,sem,phase_all,pred,mask)
    ]
    _write_csv(Path(out_dir)/"phase_reconstructed_from_population.csv",phase_rows)

    result={
        "format":"SST-QGI-PHASE-RECONSTRUCTION-2.0",
        "source_grade":"RAW_POPULATION_CSV",
        "n_rows":int(len(t)),
        "envelope_degree":int(envelope_degree),
        "phase_degree":int(phase_degree),
        "exclude_edge_cycles":int(exclude_edge_cycles),
        "upper_envelope_coeff_desc":[float(x) for x in upper_coef],
        "lower_envelope_coeff_desc":[float(x) for x in lower_coef],
        "phase_coeff_ascending":[float(x) for x in c],
        "cubic_coeff_rad_s3_inv":float(c[3]),
        "sigma_cubic_coeff_rad_s3_inv":sigma_c3,
        "reduced_chi2_local":red_chi2,
        "population_rms":float(np.sqrt(np.mean(resid[mask]**2))),
        "note":(
            "Implements the published analysis structure: envelope fit, Hilbert-transform phase "
            "initialization/unwrapping, cubic phase, and final direct population fit. "
            "It is an independent reimplementation, not the authors' original code."
        ),
    }
    Path(out_dir).mkdir(parents=True,exist_ok=True)
    (Path(out_dir)/"phase_reconstruction.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result


def _connected_components(mask: np.ndarray):
    # Small 8-connected component finder for color-segmented figure markers.
    h,w=mask.shape
    seen=np.zeros_like(mask,dtype=bool)
    comps=[]
    for y in range(h):
        for x in range(w):
            if not mask[y,x] or seen[y,x]:
                continue
            stack=[(y,x)]
            seen[y,x]=True
            pts=[]
            while stack:
                yy,xx=stack.pop()
                pts.append((yy,xx))
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        if dx==0 and dy==0:
                            continue
                        ny=yy+dy; nx=xx+dx
                        if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:
                            seen[ny,nx]=True
                            stack.append((ny,nx))
            comps.append(pts)
    return comps

def digitize_fig2_population(
    pdf_path: Path,
    out_csv: Path,
    page_index: int = 11,
    x_min_ms: float = 0.35,
    x_max_ms: float = 2.40,
    y_min_percent: float = 10.0,
    y_max_percent: float = 90.0,
    axes_bbox_norm=(0.170,0.091,0.785,0.297),
) -> dict:
    """
    Digitize the blue experimental population markers in Fig. 2A.

    This is a publication-figure extraction, not author-level raw numerical data.
    It is nevertheless closer to the raw observable than digitizing Fig. 3 because
    phase is subsequently reconstructed by this package from population vs. 2T.
    """
    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PyMuPDF is required for PDF digitization.") from exc

    doc=fitz.open(str(pdf_path))
    if page_index < 0 or page_index >= len(doc):
        raise ValueError(f"page_index {page_index} outside PDF with {len(doc)} pages")
    page=doc[page_index]
    scale=4.0
    pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale), alpha=False)
    img=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)[:,:,:3]

    x0n,y0n,x1n,y1n=axes_bbox_norm
    x0=int(x0n*pix.width); x1=int(x1n*pix.width)
    y0=int(y0n*pix.height); y1=int(y1n*pix.height)
    crop=img[y0:y1,x0:x1,:]

    R=crop[:,:,0].astype(int)
    G=crop[:,:,1].astype(int)
    B=crop[:,:,2].astype(int)
    blue=(B>115)&((B-R)>35)&((B-G)>10)&(R<175)&(G<190)

    comps=_connected_components(blue)
    points=[]
    H,W=blue.shape
    for comp in comps:
        a=np.asarray(comp,int)
        ys=a[:,0]; xs=a[:,1]
        area=len(comp)
        width=int(xs.max()-xs.min()+1)
        height=int(ys.max()-ys.min()+1)
        # Experimental marker + errorbar components are compact and narrow.
        # Reject long annotation arrows, text fragments, and isolated antialias pixels.
        if area < 10 or area > 800:
            continue
        if width > 34 or height > 65:
            continue
        cx=float(np.median(xs))
        cy=float(np.median(ys))
        # Exclude components hugging the plot boundary.
        if cx < 3 or cx > W-4 or cy < 3 or cy > H-4:
            continue
        twoT_ms=x_min_ms+(cx/(W-1))*(x_max_ms-x_min_ms)
        pop_pct=y_max_percent-(cy/(H-1))*(y_max_percent-y_min_percent)
        sem_pct=max(
            0.0,
            0.5*height/(H-1)*(y_max_percent-y_min_percent)
        )
        points.append((twoT_ms,pop_pct,sem_pct,area,width,height))

    # Sort and deduplicate components that belong to the same marker/errorbar.
    points.sort(key=lambda q:q[0])
    merged=[]
    for q in points:
        if merged and abs(q[0]-merged[-1][0]) < 0.0009:
            # Keep the larger component as the more likely full marker/errorbar.
            if q[3] > merged[-1][3]:
                merged[-1]=q
        else:
            merged.append(q)

    if len(merged) < 40:
        raise RuntimeError(
            f"Only {len(merged)} Fig.2 population markers were digitized; "
            "need at least 40. Inspect/adjust axes_bbox_norm or color thresholds."
        )

    rows=[
        {
            "twoT_s":q[0]*1e-3,
            "population_outport1":q[1]*0.01,
            "sem_population":q[2]*0.01,
            "source_grade":"PUBLISHED_FIGURE2_POPULATION_DIGITIZED",
        }
        for q in merged
    ]
    _write_csv(out_csv,rows)

    # Save a diagnostic color mask when Pillow is available.
    try:
        from PIL import Image
        diagnostic=np.zeros_like(crop)
        diagnostic[:,:,0]=np.where(blue,30,245)
        diagnostic[:,:,1]=np.where(blue,110,245)
        diagnostic[:,:,2]=np.where(blue,220,245)
        Image.fromarray(diagnostic).save(Path(out_csv).with_name("figure2_blue_mask.png"))
    except Exception:
        pass

    return {
        "format":"SST-QGI-FIG2-POPULATION-DIGITIZATION-2.0",
        "source_grade":"PUBLISHED_FIGURE2_POPULATION_DIGITIZED",
        "n_digitized_markers":len(rows),
        "page_index":page_index,
        "axes_bbox_norm":[float(x) for x in axes_bbox_norm],
        "x_range_ms":[x_min_ms,x_max_ms],
        "y_range_percent":[y_min_percent,y_max_percent],
        "warning":(
            "Digitized from plotted Fig.2 experimental population markers. "
            "This is not author-level raw numerical data. Phase is recomputed in-pipeline."
        ),
    }


def digitize_fig3_experimental_phase(
    pdf_path: Path,
    out_csv: Path,
    page_index: int = 12,
    x_min_ms: float = 0.25,
    x_max_ms: float = 2.50,
    y_min_rad: float = 0.0,
    y_max_rad: float = 100.0,
    axes_bbox_norm=(0.173,0.089,0.745,0.292),
) -> dict:
    # Public fallback only. This digitizes the red experimental phase fit in
    # Fig. 3A. It is NOT raw author data.
    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PyMuPDF is required for PDF digitization.") from exc

    doc=fitz.open(str(pdf_path))
    if page_index < 0 or page_index >= len(doc):
        raise ValueError(f"page_index {page_index} outside PDF with {len(doc)} pages")
    page=doc[page_index]
    pix=page.get_pixmap(matrix=fitz.Matrix(3.0,3.0), alpha=False)
    img=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)[:,:,:3]
    x0n,y0n,x1n,y1n=axes_bbox_norm
    x0=int(x0n*pix.width); x1=int(x1n*pix.width)
    y0=int(y0n*pix.height); y1=int(y1n*pix.height)
    crop=img[y0:y1,x0:x1,:]

    # Select saturated red pixels: experimental data line is pure red while the
    # systematic band is pale pink. Select the component with the largest
    # horizontal span so the legend sample does not contaminate the curve.
    R=crop[:,:,0].astype(int); G=crop[:,:,1].astype(int); B=crop[:,:,2].astype(int)
    red=(R>175)&(R-G>65)&(R-B>65)&(G<150)&(B<150)
    comps=_connected_components(red)
    if not comps:
        raise RuntimeError("No saturated-red components detected in Fig.3A.")
    best=max(
        comps,
        key=lambda comp: (
            max(p[1] for p in comp)-min(p[1] for p in comp),
            len(comp)
        )
    )
    a=np.asarray(best,int)
    if (a[:,1].max()-a[:,1].min()) < 0.35*red.shape[1]:
        raise RuntimeError("No horizontally extended red experimental phase curve detected.")
    xs=[]; ys=[]
    for xi in range(int(a[:,1].min()),int(a[:,1].max())+1):
        yi=a[a[:,1]==xi,0]
        if len(yi):
            xs.append(xi); ys.append(float(np.median(yi)))
    if len(xs) < 80:
        raise RuntimeError(
            "Too few red phase-line pixels detected. Adjust axes_bbox_norm or color threshold."
        )
    xs=np.array(xs,float); ys=np.array(ys,float)
    # Median-bin to suppress legend fragments and antialiasing.
    nbins=140
    edges=np.linspace(xs.min(),xs.max(),nbins+1)
    rows=[]
    for j in range(nbins):
        m=(xs>=edges[j])&(xs<edges[j+1])
        if np.count_nonzero(m)<1:
            continue
        xc=float(np.median(xs[m])); yc=float(np.median(ys[m]))
        fracx=xc/(red.shape[1]-1)
        fracy=yc/(red.shape[0]-1)
        twoT_ms=x_min_ms+fracx*(x_max_ms-x_min_ms)
        phase=y_max_rad-fracy*(y_max_rad-y_min_rad)
        rows.append({
            "twoT_s":twoT_ms*1e-3,
            "phase_rad":phase,
            "source_grade":"PUBLISHED_FIGURE3_DATA_FIT_DIGITIZED",
        })
    _write_csv(out_csv,rows)

    t=np.array([r["twoT_s"] for r in rows],float)
    ph=np.array([r["phase_rad"] for r in rows],float)
    coef_desc=np.polyfit(t,ph,3)
    coef=coef_desc[::-1]
    return {
        "format":"SST-QGI-FIG3-DIGITIZATION-2.0",
        "source_grade":"PUBLISHED_FIGURE3_DATA_FIT_DIGITIZED",
        "n_points":len(rows),
        "page_index":page_index,
        "axes_bbox_norm":[float(x) for x in axes_bbox_norm],
        "phase_coeff_ascending":[float(x) for x in coef],
        "cubic_coeff_rad_s3_inv":float(coef[3]),
        "warning":(
            "This is a digitization of the published experimental-data fit line in Fig. 3A, "
            "not raw numerical author data. It is suitable for a public-data cross-check, "
            "not for claiming author-level raw-data precision."
        ),
    }

def specific_action_from_cubic(
    c3_rad_s3_inv: float,
    g_m_s2: float,
    sigma_c3_rad_s3_inv: float | None = None,
    sigma_g_m_s2: float | None = None,
) -> dict:
    # If phi(t)=c3*t^3+..., with t=2T:
    #   |c3| = m*g^2/(24*hbar)
    #   hbar/m = g^2/(24*|c3|)
    #   h/m    = pi*g^2/(12*|c3|)
    # No particle mass, kg, h or hbar is required.
    c3=abs(float(c3_rad_s3_inv))
    if c3 <= 0:
        raise ValueError("cubic coefficient must be nonzero")
    hbar_over_m=g_m_s2**2/(24.0*c3)
    h_over_m=2.0*math.pi*hbar_over_m

    rel_var=0.0
    uncertainty_terms=0
    if sigma_c3_rad_s3_inv is not None and sigma_c3_rad_s3_inv >= 0:
        rel_var += (float(sigma_c3_rad_s3_inv)/c3)**2
        uncertainty_terms += 1
    if sigma_g_m_s2 is not None and sigma_g_m_s2 >= 0:
        rel_var += (2.0*float(sigma_g_m_s2)/g_m_s2)**2
        uncertainty_terms += 1
    rel_sigma=math.sqrt(rel_var) if uncertainty_terms else None

    return {
        "cubic_coeff_abs_rad_s3_inv":c3,
        "sigma_cubic_coeff_rad_s3_inv":sigma_c3_rad_s3_inv,
        "g_m_s2":g_m_s2,
        "sigma_g_m_s2":sigma_g_m_s2,
        "hbar_over_m_m2_s":hbar_over_m,
        "h_over_m_m2_s":h_over_m,
        "sigma_hbar_over_m_m2_s":None if rel_sigma is None else hbar_over_m*rel_sigma,
        "sigma_h_over_m_m2_s":None if rel_sigma is None else h_over_m*rel_sigma,
        "mass_used":False,
        "planck_target_used":False,
        "kg_unit_used":False,
    }

