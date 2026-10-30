Ruban T(2,3) trefoil - 3D visualization
======================================

Run (Python 3 with numpy and matplotlib):
  pip install numpy matplotlib
  python trefoil_3d_visual_examples_Ruban.py

Default geometry:
  X=[1+0.154 sin(3theta)] cos(2theta)
  Y=[1+0.154 sin(3theta)] sin(2theta)
  Z=0.154 cos(3theta)
  0<=theta<2*pi

Six PNG outputs and geometry_validation.json are generated in
  ./trefoil_3d_examples_ruban/

Optional:
  python trefoil_3d_visual_examples_Ruban.py --geometry ideal
  python trefoil_3d_visual_examples_Ruban.py --n-points 4096 --R0 1 --B0 0.154
  python trefoil_3d_visual_examples_Ruban.py --tube-radius 0.03

Key distinction: Ruban refers to the 2018 analytic torus-knot seed,
not to the graphical ribbon strip (which only depicts a normal framing).
The tube and ribbon are geometric illustrations, not Euler dynamics,
material internal twist, or an established stability result.

Ruban reference: V. P. Ruban, Long-lived quantum vortex knots,
JETP Letters 107 (2018). doi:10.1134/S0021364018050120
