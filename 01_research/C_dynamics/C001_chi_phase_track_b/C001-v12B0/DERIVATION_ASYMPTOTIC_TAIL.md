# Derivation: GP/NLSE algebraic tail and `alpha_ring` extraction

## 1. ODE

The unit-winding GP/NLSE vortex envelope satisfies

$$ 
F''+\frac{F'}{r}-\frac{F}{r^2}+F(1-F^2)=0.
 $$ 

The boundary condition is

$$ 
F(0)=0,
\qquad
F(\infty)=1.
 $$ 

## 2. Large-radius expansion

Use

$$ 
F(r)=1+\sum_{k\ge1}a_k r^{-2k}.
 $$ 

Substitution and coefficient matching gives

$$ 
a_1=-\frac12,
\qquad
a_2=-\frac98,
\qquad
a_3=-\frac{161}{16},
\qquad
a_4=-\frac{24661}{128},
\ldots
 $$ 

so

$$ 
F(r)=
1-\frac{1}{2r^2}
-\frac{9}{8r^4}
-\frac{161}{16r^6}
-\frac{24661}{128r^8}
+\cdots .
 $$ 

## 3. Corrected radial energy integrand

For the corrected GP/NLSE convention used in v10B.1 and v11B.0,

$$ 
I(r)=\frac{F^2}{r}+(F')^2r+\frac12(F^2-1)^2r.
 $$ 

The leading term is \(1/r\), giving the logarithmic divergence. Substituting the large-radius expansion gives

$$ 
I(r)-\frac1r
=
-\frac{1}{2r^3}
+\frac1{r^5}
+\frac{11}{r^7}
+\frac{179}{r^9}
+\frac{9109}{2r^{11}}
+\cdots .
 $$ 

## 4. Core constant and asymptotic extraction

Define

$$ 
C(R)=\int_0^R I(r)\,dr-\ln R.
 $$ 

Then

$$ 
C_\infty-C(R)
=
\int_R^\infty\left(I(r)-\frac1r\right)dr.
 $$ 

Therefore

$$ 
C_\infty-C(R)
=
-\frac{1}{4R^2}
+\frac{1}{4R^4}
+\frac{11}{6R^6}
+\frac{179}{8R^8}
+\frac{9109}{20R^{10}}
+\cdots .
 $$ 

Equivalently,

$$ 
C(R)=
C_\infty
+\frac{1}{4R^2}
-\frac{1}{4R^4}
-\frac{11}{6R^6}
-\frac{179}{8R^8}
-\frac{9109}{20R^{10}}
+\cdots .
 $$ 

This proves that the finite-radius extraction law must be algebraic, not exponential. The leading expected fit coefficients are

$$ 
A_2=+\frac14,
\qquad
A_4=-\frac14,
\qquad
A_6=-\frac{11}{6}.
 $$ 

## 5. Ring constants

In the GP/NLSE convention used here,

$$ 
\alpha_{\rm ring}^{\rm GP}=2-C_\infty.
 $$ 

For fixed-core / \(q=0\), v8 gives

$$ 
\beta_{\rm ring}=\alpha_{\rm ring}-1.
 $$ 

Thus the asymptotic GP/NLSE extraction gives a conditional Track-B result for both \(\alpha_{\rm ring}\) and \(\beta_{\rm ring}\), provided the SST core-envelope lock \(A=B=C\) is accepted.