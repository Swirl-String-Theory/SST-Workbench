import React from 'react';
import { MathBlock } from './MathBlock';

export const MassInvariantSection = () => {
  return (
    <section className="py-24 bg-physics-bg border-t border-slate-800">
      <div className="container mx-auto px-6 max-w-4xl">
        <div className="mb-12">
          <div className="inline-block mb-3 text-[10px] font-bold tracking-[0.2em] text-physics-gold uppercase">Theory</div>
          <h2 className="font-serif text-3xl md:text-4xl mb-6 text-white leading-tight">
            SST Invariant Master Mass Kernel from Knot Taxonomy
          </h2>
          <p className="text-lg text-physics-muted leading-relaxed mb-8 font-light">
            In Swirl-String Theory (SST), the rest mass of a particle-like excitation realised as a knotted swirl string of type <MathBlock math="K" /> is obtained from a single <em>invariant kernel</em> that depends only on the knot-theoretic data tabulated in this document, together with a geometry-dependent ropelength <MathBlock math="L_{tot}(T)" /> for the physical realisation <MathBlock math="T" />.
          </p>
        </div>

        <div className="space-y-12">
          <div>
            <h3 className="font-serif text-2xl text-white mb-6">Universal scale and mass invariant</h3>
            <p className="text-physics-muted mb-4">Let the swirl energy density be</p>
            <MathBlock block math="u = \frac{1}{2} \rho_{core} \|\mathbf{v}_\circlearrowleft\|^2" />
            
            <p className="text-physics-muted mb-4 mt-8">and define the universal SST mass scale</p>
            <MathBlock block math="\Lambda_0 = \frac{4}{\alpha} u \frac{\pi r_c^3}{c^2} = \frac{4}{\alpha} \frac{1}{2} \rho_{core} \|\mathbf{v}_\circlearrowleft\|^2 \frac{\pi r_c^3}{c^2}" />
            
            <p className="text-physics-muted mb-4 mt-8">
              Using the canonical constants (<MathBlock math="\alpha" /> the fine-structure constant, <MathBlock math="\rho_{core} = 3.8934 \times 10^{18} \text{ kg m}^{-3}" />, <MathBlock math="\|\mathbf{v}_\circlearrowleft\| = 1.0938 \times 10^6 \text{ m s}^{-1}" />, <MathBlock math="r_c = 1.4089 \times 10^{-15} \text{ m}" />, <MathBlock math="c = 2.9979 \times 10^8 \text{ m s}^{-1}" />), one finds numerically
            </p>
            <MathBlock block math="\Lambda_0 \approx 1.2483 \times 10^{-28} \text{ kg}" />

            <p className="text-physics-muted mb-4 mt-8">
              For a knot type <MathBlock math="K" /> with braid index <MathBlock math="b(K)" />, genus <MathBlock math="g(K)" />, and number of components <MathBlock math="n(K)" />, the dimensionless <em>mass invariant</em> is
            </p>
            <div className="p-6 bg-physics-card border border-physics-gold/20 rounded-xl shadow-[0_0_30px_rgba(251,191,36,0.05)]">
              <MathBlock block math="\mathcal{I}_M(K) := b(K)^{-3/2} \varphi^{-g(K)} n(K)^{-1/\varphi}" />
            </div>
            <p className="text-sm text-physics-muted mt-4 italic">
              where we use the <strong>Golden (hyperbolic)</strong>: <MathBlock math="\ln \varphi = \text{asinh}(\frac{1}{2})" />, hence <MathBlock math="\varphi = \exp(\text{asinh}(\frac{1}{2}))" />. (Algebraic form <MathBlock math="\varphi = (1 + \sqrt{5})/2" /> is equivalent.)
            </p>
          </div>

          <div>
            <h3 className="font-serif text-2xl text-white mb-6">Master mass relation</h3>
            <p className="text-physics-muted mb-4">
              Given a physical realisation <MathBlock math="T" /> of knot type <MathBlock math="K(T)" /> with total dimensionless ropelength <MathBlock math="L_{tot}(T)" />, the SST master mass relation is
            </p>
            <MathBlock block math="M(T) = \Lambda_0 \mathcal{I}_M(K(T)) L_{tot}(T)" />
            
            <p className="text-physics-muted mb-4 mt-8">Equivalently, expanding <MathBlock math="\Lambda_0" /> and <MathBlock math="\mathcal{I}_M" />,</p>
            <MathBlock block math="M(T) = \frac{4}{\alpha} b(T)^{-3/2} \varphi^{-g(T)} n(T)^{-1/\varphi} \frac{1}{2} \rho_{core} \|\mathbf{v}_\circlearrowleft\|^2 \frac{\pi r_c^3 L_{tot}(T)}{c^2}" />
            
            <p className="text-physics-muted mt-8">
              This matches the code kernel (up to the choice of mode for <MathBlock math="L_{tot}" />). Here:
            </p>
            <ul className="list-disc pl-6 mt-4 space-y-2 text-physics-muted">
              <li><MathBlock math="b(T), g(T), n(T)" /> are read directly from the <strong>knot taxonomy</strong> tables.</li>
              <li><MathBlock math="\rho_{core}, \mathbf{v}_\circlearrowleft, r_c" /> and <MathBlock math="\alpha" /> are fixed SST Canon scales.</li>
              <li><MathBlock math="L_{tot}(T)" /> encodes the geometry of the specific ropelength realisation.</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
};
