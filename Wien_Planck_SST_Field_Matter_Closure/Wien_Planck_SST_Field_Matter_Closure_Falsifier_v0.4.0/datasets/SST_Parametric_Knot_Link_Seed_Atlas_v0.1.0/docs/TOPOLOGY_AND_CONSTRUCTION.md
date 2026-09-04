# Topology and construction

For the generic SIAF branch, all components are transformed by the same ambient map

\[
D_\lambda(x,y,z)=(\lambda x,\lambda^{-1/2}y,\lambda^{-1/2}z),
\]
then sequential shears
\[
x_1=x+a\sin(2.1y),\qquad y_1=y+b\sin(1.7z),\qquad z_1=z+0.55a\sin(1.3x_1).
\]
Each step is explicitly invertible; their composition is a diffeomorphism of R^3. Translation and positive uniform scaling are applied only for normalization. Hence a valid source embedding cannot change knot/link type under this map.

For torus T(p,q), d=gcd(p,q), p0=p/d, q0=q/d and component j uses
\[
r_j(t)=R+a\cos(q_0t+2\pi j/d),
\]
\[
x_j=r_j\cos(p_0t),\quad y_j=r_j\sin(p_0t),\quad z_j=b\sin(q_0t+2\pi j/d).
\]
The chosen grid satisfies R>a>0 throughout. Pairwise linking is numerically checked against the expected/historical integer pattern.
