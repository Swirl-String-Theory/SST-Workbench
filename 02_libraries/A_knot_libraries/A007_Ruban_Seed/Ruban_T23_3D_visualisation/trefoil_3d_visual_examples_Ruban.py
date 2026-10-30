#!/usr/bin/env python3
"""3D visualisations of Ruban's T(2,3) trefoil seed for SST.

Default: Ruban (2018) analytical centreline with R0=1 and B0=r0/R0=77/500.
Optional: original Fourier ideal-trefoil input from the supplied script.

Produces six PNGs and geometry_validation.json. No dynamical simulation is
performed; the ribbon is a geometric Frenet-normal strip, NOT a material
swirl-string twist or proof of vortex stability.

Examples:
    python trefoil_3d_visual_examples_Ruban.py
    python trefoil_3d_visual_examples_Ruban.py --geometry ideal
    python trefoil_3d_visual_examples_Ruban.py --B0 0.154 --R0 1 --n-points 4096
    python trefoil_3d_visual_examples_Ruban.py --tube-radius 0.03

Reference: V. P. Ruban (2018), Long-lived quantum vortex knots,
JETP Letters 107, 615-619. DOI 10.1134/S0021364018050120.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import numpy as np

# Ruban (2018) illustrative seed configuration (dimensionless R0 by default).
DEFAULT_R0 = 1.0
DEFAULT_B0 = 77 / 500  # exact decimal 0.154
RUBAN_DELTA = 1 / 20    # regularisation/numerical parameter, NOT a shape input
RUBAN_LAMBDA = 1.4 + 0.5 * np.log(200.0)  # ~= 4.0491586833

# Retained unmodified from the supplied original Fourier trefoil script.
IDEAL_TREFOIL_COEFFS = [
    (1, 0.374139, 0.000000, 0.000000, 0.000000, 0.373928, 0.000000),
    (2, 0.824246, 0.750260, 0.000352, 0.750450, -0.823952, -0.001991),
    (3, 0.000257, -0.000932, 0.352397, -0.000770, 0.000726, -0.386764),
    (4, 0.011652, -0.010656, 0.000743, 0.010739, 0.011613, -0.000230),
    (5, 0.010504, 0.110306, 0.000199, 0.110745, -0.010366, -0.000235),
    (6, 0.000015, -0.000006, -0.047465, -0.000050, -0.000001, 0.004595),
    (7, -0.000292, 0.002417, -0.000008, -0.002529, -0.000255, -0.000009),
    (8, 0.016487, -0.021784, 0.000041, -0.021922, -0.016421, -0.000044),
    (9, -0.000029, -0.000018, 0.011178, 0.000049, 0.000041, 0.008414),
    (10, -0.000216, -0.000290, -0.000018, 0.000311, -0.000197, -0.000044),
    (11, -0.011727, 0.002184, 0.000007, 0.002202, 0.011682, 0.000020),
    (12, 0.000026, 0.000019, -0.001308, -0.000004, -0.000019, -0.007039),
    (13, 0.000325, 0.000055, -0.000009, -0.000059, 0.000289, 0.000024),
    (14, 0.005213, 0.003201, 0.000001, 0.003210, -0.005188, 0.000010),
    (15, -0.000015, -0.000016, -0.001917, -0.000017, 0.000001, 0.003121),
    (16, -0.000136, 0.000062, 0.000019, -0.000075, -0.000112, -0.000007),
    (17, -0.000995, -0.003463, -0.000001, -0.003474, 0.000988, -0.000015),
    (18, 0.000003, 0.000008, 0.002178, 0.000019, 0.000008, -0.000615),
    (19, 0.000033, -0.000094, -0.000016, 0.000113, 0.000028, -0.000004),
    (20, -0.000999, 0.002013, -0.000000, 0.002019, 0.000998, 0.000000),
    (21, 0.000004, 0.000001, -0.001270, -0.000013, -0.000012, -0.000626),
    (22, 0.000034, 0.000060, 0.000009, -0.000072, 0.000026, 0.000010),
    (23, 0.001383, -0.000539, 0.000002, -0.000540, -0.001382, 0.000004),
    (24, -0.000005, -0.000011, 0.000344, 0.000009, 0.000007, 0.000890),
    (25, -0.000057, -0.000025, 0.000001, 0.000019, -0.000048, -0.000008),
    (26, -0.000931, -0.000356, -0.000000, -0.000357, 0.000931, -0.000005),
    (27, 0.000006, 0.000009, 0.000228, -0.000002, -0.000000, -0.000597),
    (28, 0.000040, -0.000007, -0.000004, 0.000019, 0.000036, 0.000004),
    (29, 0.000308, 0.000611, 0.000001, 0.000611, -0.000307, 0.000007),
    (30, 0.000002, 0.000001, -0.000391, -0.000006, 0.000001, 0.000195),
]

def _ruban_eval(s: np.ndarray, R0: float, B0: float, order: int = 0) -> np.ndarray:
    """Ruban T(2,3): (R+r sin(3theta)) (cos(2theta),sin(2theta)), z=r cos(3theta).

    s is periodic on [0,1), theta = 2*pi*s. Analytical derivatives are w.r.t. s.
    """
    theta = 2.0 * np.pi * np.asarray(s)
    p, q = 2, 3
    r0 = R0 * B0
    cp, sp = np.cos(p*theta), np.sin(p*theta)
    cq, sq = np.cos(q*theta), np.sin(q*theta)
    A = R0 + r0 * sq
    if order == 0:
        return np.column_stack((A*cp, A*sp, r0*cq))
    Ap = r0*q*cq
    if order == 1:
        dtheta = np.column_stack((Ap*cp-p*A*sp, Ap*sp+p*A*cp, -r0*q*sq))
        return (2*np.pi)*dtheta
    if order == 2:
        App = -r0*q*q*sq
        ddtheta = np.column_stack(((App-p*p*A)*cp-2*p*Ap*sp,
                                    (App-p*p*A)*sp+2*p*Ap*cp,
                                    -r0*q*q*cq))
        return (2*np.pi)**2*ddtheta
    raise ValueError('Derivative order must be 0, 1, or 2')


def _ideal_eval(s: np.ndarray, order: int = 0) -> np.ndarray:
    """Original ideal-trefoil Fourier coefficients and analytic derivatives."""
    result = np.zeros((len(s), 3), dtype=float)
    for k, Ax, Ay, Az, Bx, By, Bz in IDEAL_TREFOIL_COEFFS:
        a = np.array((Ax, Ay, Az))
        b = np.array((Bx, By, Bz))
        w = 2*np.pi*k
        phase = w*s
        if order == 0:
            result += np.cos(phase)[:, None]*a + np.sin(phase)[:, None]*b
        elif order == 1:
            result += w*(-np.sin(phase)[:, None]*a + np.cos(phase)[:, None]*b)
        elif order == 2:
            result -= w*w*(np.cos(phase)[:, None]*a + np.sin(phase)[:, None]*b)
        else:
            raise ValueError('Derivative order must be 0, 1, or 2')
    return result


def eval_curve(s, geometry='ruban', R0=DEFAULT_R0, B0=DEFAULT_B0, order=0):
    if geometry == 'ruban':
        return _ruban_eval(s, R0, B0, order=order)
    if geometry == 'ideal':
        return _ideal_eval(s, order=order)
    raise ValueError(f'Unknown geometry: {geometry}')


def unit(v: np.ndarray) -> np.ndarray:
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-14)


def equal_arclength_parameters(n: int, geometry: str, R0: float, B0: float):
    """Resample the *analytical* curve at nearly equal arclength intervals."""
    n_dense = max(8*n, 20000)
    u = np.arange(n_dense)/n_dense
    xyz = eval_curve(u, geometry, R0, B0)
    distances = np.linalg.norm(np.roll(xyz,-1,axis=0)-xyz, axis=1)
    cum_length = np.concatenate(([0.], np.cumsum(distances)))
    u_closed = np.concatenate((u, [1.]))
    targets = np.arange(n) * (cum_length[-1] / n)
    return np.interp(targets, cum_length, u_closed)


def compute_geometry(n_pts=2400, geometry='ruban', R0=DEFAULT_R0, B0=DEFAULT_B0):
    s = equal_arclength_parameters(n_pts, geometry, R0, B0)
    x = eval_curve(s, geometry, R0, B0)
    d1 = eval_curve(s, geometry, R0, B0, order=1)
    d2 = eval_curve(s, geometry, R0, B0, order=2)
    tangent = unit(d1)
    cross = np.cross(d1, d2)
    cross_norm = np.linalg.norm(cross, axis=1)
    if np.min(cross_norm) <= 1.e-12:
        raise ValueError('Degenerate Frenet frame: curvature nearly vanishes.')
    binormal = unit(cross)
    normal = unit(np.cross(binormal, tangent))
    curvature = cross_norm / np.linalg.norm(d1, axis=1)**3
    return s, x, tangent, normal, binormal, curvature


def close_path(points: np.ndarray):
    return np.vstack((points, points[0]))


def make_axes(title: str, xyz: np.ndarray, *, figsize=(9, 7), azim=-62, elev=26):
    fig = plt.figure(figsize=figsize, facecolor='white')
    ax = fig.add_subplot(111, projection='3d', computed_zorder=False)
    ax.set_title(title, fontsize=12, pad=18)
    ax.view_init(elev=elev, azim=azim)
    mins, maxs = xyz.min(axis=0), xyz.max(axis=0)
    center = 0.5*(mins+maxs)
    radius = 0.60*max(maxs-mins)
    ax.set(xlim=(center[0]-radius,center[0]+radius),
           ylim=(center[1]-radius,center[1]+radius),
           zlim=(center[2]-radius,center[2]+radius),
           xlabel='x', ylabel='y', zlabel='z')
    ax.set_box_aspect((1, 1, 1))
    ax.grid(alpha=0.22)
    return fig, ax


def save_fig(fig, out: Path, filename: str):
    fig.savefig(out/filename, dpi=170, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def save_centerline(out, xyz, geometry, R0, B0):
    title = ('Ruban T(2,3) - analytical centerline | B0=0.154'
             if geometry=='ruban' else 'Ideal Fourier trefoil - centerline')
    fig, ax = make_axes(title, xyz)
    curve = close_path(xyz)
    ax.plot(*curve.T, lw=2.5, color='#146C94', zorder=4)
    ax.scatter(*xyz[0], s=45, c='#EF8E21', depthshade=False, zorder=5)
    if geometry=='ruban':
        phi=np.linspace(0,2*np.pi,400)
        ax.plot(R0*np.cos(phi),R0*np.sin(phi),phi*0,
                color='#7F8B96', linestyle='--', lw=0.9, alpha=0.55)
    save_fig(fig, out, '01_centerline.png')


def save_tangents(out, xyz, T, geometry, R0, B0):
    fig,ax=make_axes(f'{geometry.title()} trefoil - tangent vectors (T)',xyz)
    ax.plot(*close_path(xyz).T,color='#146C94',lw=1.65)
    step=max(1,len(xyz)//30)
    P=xyz[::step]
    Q=T[::step]*(0.15*R0)
    ax.quiver(*P.T,*Q.T,normalize=False,color='#D97725',linewidth=1.0,
              arrow_length_ratio=0.23)
    save_fig(fig,out,'02_tangent_quivers.png')


def save_frame(out, xyz, T, N, B, geometry, R0):
    fig,ax=make_axes(f'{geometry.title()} trefoil - Frenet frame (T,N,B)',xyz)
    ax.plot(*close_path(xyz).T,color='#41647A',lw=1.15,alpha=0.8)
    step=max(1,len(xyz)//20)
    P=xyz[::step]
    scale=0.17*R0
    for vectors,color in ((T,'#007A6D'),(N,'#E88E23'),(B,'#7C51A1')):
        Q=vectors[::step]*scale
        ax.quiver(*P.T,*Q.T,normalize=False,color=color,linewidth=1.2,
                  arrow_length_ratio=0.23)
    legend=[Line2D([0],[0],color=color,lw=2,label=label)
            for color,label in (('#007A6D','T: tangent'),('#E88E23','N: normal'),
                                ('#7C51A1','B: binormal'))]
    ax.legend(handles=legend,loc='upper left',frameon=False,fontsize=9)
    save_fig(fig,out,'03_frenet_quivers.png')


def save_curvature(out, xyz, kappa, geometry):
    fig,ax=make_axes(f'{geometry.title()} trefoil - curvature along centerline',xyz)
    curve=close_path(xyz)
    segments=np.stack((curve[:-1],curve[1:]),axis=1)
    norm=Normalize(vmin=float(np.min(kappa)),vmax=float(np.max(kappa)))
    colors=cm.viridis(norm(kappa))
    ax.add_collection3d(Line3DCollection(segments,colors=colors,linewidths=3.2))
    cbar=fig.colorbar(cm.ScalarMappable(norm=norm,cmap='viridis'),
                      ax=ax,shrink=0.65,pad=0.08)
    cbar.set_label('Curvature (inverse model-length)')
    save_fig(fig,out,'04_curvature_colormap.png')


def save_ribbon(out, xyz, N, geometry, half_width):
    fig,ax=make_axes(f'{geometry.title()} trefoil - geometric normal ribbon',xyz)
    stride=max(1,len(xyz)//650)
    pos=np.r_[np.arange(0,len(xyz),stride),0]
    pts=xyz[pos]
    normal=N[pos]
    left=pts + half_width*normal
    right=pts - half_width*normal
    surface=np.stack((left,right),axis=1)
    ax.plot_surface(surface[:,:,0],surface[:,:,1],surface[:,:,2],
                    color='#55B9C1',alpha=0.80,shade=True,
                    rstride=1,cstride=1,linewidth=0,antialiased=True)
    ax.plot(*left.T,lw=0.65,color='#166D7A',alpha=0.95)
    ax.plot(*right.T,lw=0.65,color='#166D7A',alpha=0.95)
    ax.plot(*close_path(xyz).T,lw=1.05,color='#B75A26',alpha=0.95)
    save_fig(fig,out,'05_ribbon.png')


def save_tube(out,xyz,N,B,geometry,tube_radius):
    fig,ax=make_axes(f'{geometry.title()} trefoil - tube (radius={tube_radius:.5g})',xyz)
    stride=max(1,len(xyz)//700)
    positions=np.r_[np.arange(0,len(xyz),stride),0]
    theta=np.linspace(0,2*np.pi,25,endpoint=True)
    offsets=tube_radius*(np.cos(theta)[None,:,None]*N[positions,None,:] +
                         np.sin(theta)[None,:,None]*B[positions,None,:])
    surface=xyz[positions,None,:]+offsets
    ax.plot_surface(surface[:,:,0],surface[:,:,1],surface[:,:,2],
                    color='#2589B0',alpha=0.87,shade=True,rstride=1,cstride=1,
                    linewidth=0,antialiased=True)
    save_fig(fig,out,'06_tube_surface.png')


def run(args):
    if args.R0 <= 0 or not 0 < args.B0 < 1 or args.n_points < 100:
        raise ValueError('Require R0>0, 0<B0<1 and n-points>=100')
    out=(args.output_dir if args.output_dir is not None else
         Path(f'trefoil_3d_examples_{args.geometry}'))
    out.mkdir(parents=True,exist_ok=True)
    s,x,T,N,B,kappa=compute_geometry(args.n_points,args.geometry,args.R0,args.B0)
    radius = (args.tube_radius if args.tube_radius is not None else
              (args.R0*np.exp(-RUBAN_LAMBDA) if args.geometry=='ruban' else 0.04*args.R0))
    ribbon_width = args.ribbon_half_width if args.ribbon_half_width is not None else 0.055*args.R0
    if radius<=0 or ribbon_width<=0:
        raise ValueError('Tube radius and ribbon half-width must be positive')
    save_centerline(out,x,args.geometry,args.R0,args.B0)
    save_tangents(out,x,T,args.geometry,args.R0,args.B0)
    save_frame(out,x,T,N,B,args.geometry,args.R0)
    save_curvature(out,x,kappa,args.geometry)
    save_ribbon(out,x,N,args.geometry,ribbon_width)
    save_tube(out,x,N,B,args.geometry,radius)
    # Analytic periodicity check and sampled segment-length ratio.
    periodicity=float(np.linalg.norm(eval_curve(np.array([0.]),args.geometry,args.R0,args.B0)[0]-
                   eval_curve(np.array([1.]),args.geometry,args.R0,args.B0)[0]))
    dist=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
    result={'geometry':args.geometry,'knot':'T(2,3)' if args.geometry=='ruban' else 'ideal 3_1',
            'n_points':len(x),'R0':args.R0,'B0':args.B0 if args.geometry=='ruban' else None,
            'r0':args.B0*args.R0 if args.geometry=='ruban' else None,
            'ribbon_half_width_visual':ribbon_width,'tube_radius_visual':radius,
            'centerline_periodicity_residual':periodicity,
            'segment_length_max_min_ratio':float(dist.max()/dist.min()),
            'max_frame_dot_residual':float(max(abs(np.einsum('ij,ij->i',T,N)).max(),
                     abs(np.einsum('ij,ij->i',T,B)).max(),abs(np.einsum('ij,ij->i',N,B)).max())),
            'curvature_min':float(kappa.min()),'curvature_max':float(kappa.max()),
            'length_polygonal':float(dist.sum()),
            'is_static_seed_only':True,
            'ribbon_is_material_twist':False}
    if args.geometry=='ruban':
        result['ruban_reference']={'delta':RUBAN_DELTA,'Lambda':float(RUBAN_LAMBDA),
             'xi_over_R0':float(np.exp(-RUBAN_LAMBDA)),
             'note':'Delta and Lambda are not used in the centerline formula; tube is illustrative.'}
    (out/'geometry_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Saved to:',out.resolve())
    for p in sorted(out.glob('*.png')): print(' ',p.name)
    print('Closure residual:',f'{periodicity:.3e}')
    print('Segment max/min:',f'{result["segment_length_max_min_ratio"]:.9f}')
    return result


def parse_args():
    parser=argparse.ArgumentParser(description='Ruban T(2,3) trefoil 3D visual examples')
    parser.add_argument('--geometry',choices=['ruban','ideal'],default='ruban')
    parser.add_argument('--R0',type=float,default=DEFAULT_R0,
                        help='major torus radius, in arbitrary model-length units')
    parser.add_argument('--B0',type=float,default=DEFAULT_B0,
                        help='Ruban r0/R0, default 77/500')
    parser.add_argument('--n-points',type=int,default=2400)
    parser.add_argument('--ribbon-half-width',type=float,default=None,
                        help='illustrative strip half-width, default 0.055*R0')
    parser.add_argument('--tube-radius',type=float,default=None,
                        help='illustrative tube radius, default R0*exp(-Lambda) for Ruban')
    parser.add_argument('--output-dir',type=Path,default=None)
    return parser.parse_args()

if __name__=='__main__':
    run(parse_args())
