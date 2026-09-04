/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, RotateCcw, Activity, ArrowRight, BarChart2, Info } from 'lucide-react';

// --- ELECTRON SCALE DERIVATION DIAGRAM ---
// Based on Paper 1: "A Unified Electron Scale Relation..."
export const ElectronScaleDerivation: React.FC = () => {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
        setStep(s => (s + 1) % 5);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const steps = [
      {
          label: "The Ingredients",
          content: (
            <div className="flex gap-4 items-center justify-center">
                <div className="flex flex-col items-center">
                    <div className="w-14 h-14 rounded-full bg-physics-cyan/10 border border-physics-cyan flex items-center justify-center font-serif font-bold text-physics-cyan shadow-[0_0_15px_rgba(34,211,238,0.3)]">rₑ</div>
                    <span className="text-[10px] mt-2 font-bold uppercase text-physics-muted">Classical Radius</span>
                </div>
                <div className="flex flex-col items-center">
                    <div className="w-14 h-14 rounded-full bg-physics-purple/10 border border-physics-purple flex items-center justify-center font-serif font-bold text-physics-purple shadow-[0_0_15px_rgba(192,132,252,0.3)]">ω꜀</div>
                    <span className="text-[10px] mt-2 font-bold uppercase text-physics-muted">Compton Freq</span>
                </div>
                <div className="flex flex-col items-center">
                    <div className="w-14 h-14 rounded-full bg-physics-gold/10 border border-physics-gold flex items-center justify-center font-serif font-bold text-physics-gold shadow-[0_0_15px_rgba(251,191,36,0.3)]">Eᵦ</div>
                    <span className="text-[10px] mt-2 font-bold uppercase text-physics-muted">Bohr Energy</span>
                </div>
            </div>
          )
      },
      {
          label: "Harmonic Oscillator Ansatz",
          content: (
              <div className="text-center">
                  <p className="font-serif italic text-lg mb-4 text-physics-text">F_max = mₑ ω_*² x_max</p>
                  <p className="text-xs text-physics-muted">
                      Let <span className="font-bold text-physics-purple">ω_* = ω꜀ / α</span> and <span className="font-bold text-physics-cyan">x_max = rₑ</span>
                  </p>
              </div>
          )
      },
      {
          label: "Combine Constants",
          content: (
            <div className="text-center">
                <p className="font-serif text-lg text-physics-text">
                    F_max = mₑ <span className="text-slate-500">(</span> <span className="text-physics-purple font-bold">ω꜀</span>/<span className="text-slate-500">α</span> <span className="text-slate-500">)²</span> <span className="text-physics-cyan font-bold">rₑ</span>
                </p>
                <div className="mt-3 text-xs text-physics-muted">Substitute standard definitions</div>
            </div>
          )
      },
      {
        label: "Resulting Force Scale",
        content: (
          <div className="text-center">
              <p className="font-serif text-xl font-bold text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]">
                  F_max = mₑ² c³ / (α ħ)
              </p>
              <div className="mt-3 text-xs text-physics-muted">A unified force purely from constants</div>
          </div>
        )
      },
      {
          label: "The Energy Identity",
          content: (
            <div className="text-center p-4 bg-physics-gold/10 rounded-lg border border-physics-gold/30 shadow-[0_0_30px_rgba(251,191,36,0.1)]">
                <p className="font-serif text-2xl font-bold text-physics-gold">
                    ½ mₑ c²  =  Eᵦ / α²
                </p>
                <div className="mt-2 text-xs font-bold text-physics-gold uppercase tracking-widest animate-pulse">Exact Match</div>
            </div>
          )
      }
  ];

  return (
    <div className="flex flex-col items-center p-8 bg-physics-card/50 backdrop-blur-md rounded-xl border border-slate-800 my-8 shadow-xl">
      <h3 className="font-serif text-xl mb-4 text-physics-text">Deriving the Identity</h3>
      <p className="text-sm text-physics-muted mb-6 text-center max-w-md">
        Paper 1 demonstrates how independently defined electron scales combine into a dimensionally consistent identity.
      </p>

      <div className="relative w-full max-w-lg h-48 bg-black/40 rounded-lg shadow-inner overflow-hidden mb-6 border border-slate-700/50 flex flex-col items-center justify-center p-4">
        <div key={step} className="animate-fade-in w-full">
            {steps[step].content}
        </div>
      </div>

      <div className="flex gap-2 justify-center w-full">
          {steps.map((_, i) => (
              <div key={i} className={`h-1 rounded-full transition-all duration-300 ${step === i ? 'w-8 bg-physics-cyan shadow-[0_0_10px_#22d3ee]' : 'w-2 bg-slate-700'}`}></div>
          ))}
      </div>
      <div className="mt-3 text-xs font-bold uppercase tracking-wider text-physics-cyan">
          Step {step + 1}: {steps[step].label}
      </div>
    </div>
  );
};

// --- VORTEX RING CALCULATOR ---
// Based on Paper 4: "Energy, Impulse, and Stability of Thin Vortex Loops..."
export const VortexRingCalculator: React.FC = () => {
  // R = Major Radius, a = Core Radius
  const [R, setR] = useState(10); // cm
  const [a_val, setA] = useState(0.5); // cm, named a_val to avoid confusion
  const [gamma, setGamma] = useState(100); // Circulation unit
  
  // Constants based on paper (simplified for viz)
  const rho = 1; // density
  const alpha = 1.75; // 7/4
  const beta = 0.25; // 1/4
  
  const term = Math.log((8 * R) / a_val);
  const Energy = 0.5 * rho * Math.pow(gamma, 2) * R * (term - alpha);
  const Velocity = (gamma / (4 * Math.PI * R)) * (term - beta);
  const Impulse = Math.PI * rho * gamma * Math.pow(R, 2);

  return (
    <div className="flex flex-col items-center p-8 bg-physics-card/80 backdrop-blur-md rounded-xl shadow-2xl border border-slate-800 my-8">
      <h3 className="font-serif text-xl mb-2 text-white">Vortex Ring Dynamics</h3>
      <p className="text-sm text-physics-muted mb-8 text-center max-w-md">
        Adjust the geometry of a thin vortex ring to see how Energy, Impulse, and Translational Velocity scale.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-10 w-full max-w-2xl">
          {/* Controls */}
          <div className="space-y-8">
              <div>
                  <label className="flex justify-between text-xs font-bold text-physics-cyan uppercase mb-2">
                      <span>Ring Radius (R)</span>
                      <span>{R} cm</span>
                  </label>
                  <input 
                    type="range" min="5" max="50" step="1" 
                    value={R} onChange={(e) => setR(Number(e.target.value))}
                    className="w-full accent-physics-cyan bg-slate-700 h-1 rounded-lg appearance-none cursor-pointer"
                  />
              </div>
              <div>
                  <label className="flex justify-between text-xs font-bold text-physics-purple uppercase mb-2">
                      <span>Core Radius (a)</span>
                      <span>{a_val} cm</span>
                  </label>
                  <input 
                    type="range" min="0.1" max="2" step="0.1" 
                    value={a_val} onChange={(e) => setA(Number(e.target.value))}
                    className="w-full accent-physics-purple bg-slate-700 h-1 rounded-lg appearance-none cursor-pointer"
                  />
              </div>
              <div>
                  <label className="flex justify-between text-xs font-bold text-physics-gold uppercase mb-2">
                      <span>Circulation (Γ)</span>
                      <span>{gamma} units</span>
                  </label>
                  <input 
                    type="range" min="10" max="200" step="10" 
                    value={gamma} onChange={(e) => setGamma(Number(e.target.value))}
                    className="w-full accent-physics-gold bg-slate-700 h-1 rounded-lg appearance-none cursor-pointer"
                  />
              </div>
          </div>

          {/* Visualization / Output */}
          <div className="bg-black/40 rounded-lg border border-slate-700 p-6 flex flex-col justify-center gap-6 relative shadow-inner">
             <div className="absolute top-3 right-3 text-physics-cyan animate-pulse">
                 <Activity size={16} />
             </div>
             
             {/* Visual Representation of Ring */}
             <div className="w-full h-24 flex items-center justify-center border-b border-slate-700 pb-6 mb-2">
                 <div 
                    className="rounded-full border-2 border-physics-cyan shadow-[0_0_15px_rgba(34,211,238,0.4)] transition-all duration-300 bg-physics-cyan/5"
                    style={{ 
                        width: `${Math.min(120, R * 3)}px`, 
                        height: `${Math.min(50, R)}px`,
                        borderWidth: `${Math.max(2, a_val * 3)}px`
                    }}
                 ></div>
                 <ArrowRight className="ml-4 text-physics-muted" size={16} />
                 <span className="text-xs text-physics-cyan ml-1 font-mono font-bold">U</span>
             </div>

             <div className="grid grid-cols-2 gap-6">
                 <div>
                     <div className="text-[10px] uppercase font-bold text-physics-muted mb-1">Translational Velocity</div>
                     <div className="font-serif text-xl text-white">{Velocity.toFixed(2)} <span className="text-xs text-physics-cyan">cm/s</span></div>
                 </div>
                 <div>
                     <div className="text-[10px] uppercase font-bold text-physics-muted mb-1">Energy</div>
                     <div className="font-serif text-xl text-white">{(Energy / 1000).toFixed(2)} <span className="text-xs text-physics-purple">k units</span></div>
                 </div>
                 <div>
                     <div className="text-[10px] uppercase font-bold text-physics-muted mb-1">Impulse</div>
                     <div className="font-serif text-xl text-white">{(Impulse / 1000).toFixed(2)} <span className="text-xs text-physics-gold">k units</span></div>
                 </div>
                 <div>
                     <div className="text-[10px] uppercase font-bold text-physics-muted mb-1">Aspect Ratio (R/a)</div>
                     <div className="font-serif text-xl text-white">{(R/a_val).toFixed(1)}</div>
                 </div>
             </div>
          </div>
      </div>
    </div>
  );
};

// --- UNIFIED ENERGY CHART ---
// Based on Paper 1 Numerical Consistency
export const UnifiedEnergyChart: React.FC = () => {
    return (
        <div className="flex flex-col md:flex-row gap-8 items-center p-8 bg-gradient-to-br from-physics-card to-slate-950 rounded-xl my-8 border border-slate-800 shadow-2xl relative overflow-hidden">
            {/* Background Accent */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-physics-purple/10 blur-[80px] rounded-full pointer-events-none"></div>

            <div className="flex-1 min-w-[240px] z-10">
                <h3 className="font-serif text-2xl mb-3 text-white">Numerical Precision</h3>
                <p className="text-physics-muted text-sm mb-6 leading-relaxed">
                    Paper 1 confirms the analytical identity numerically using CODATA values. The "Half Rest Energy" of the electron matches the "Scaled Hydrogen Ground State" to within numerical precision.
                </p>
                <div className="p-4 bg-black/30 rounded border border-slate-700 font-mono text-xs space-y-3">
                    <div className="flex justify-between items-center">
                        <span className="text-physics-muted">mₑc²</span>
                        <span className="text-physics-cyan">≈ 511 keV</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-physics-muted">E_B</span>
                        <span className="text-physics-gold">≈ 13.6 eV</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-physics-muted">α⁻¹</span>
                        <span className="text-physics-purple">≈ 137.036</span>
                    </div>
                </div>
            </div>
            
            <div className="relative w-64 h-64 bg-black/40 rounded-xl border border-slate-700 p-6 flex justify-around items-end z-10 backdrop-blur-sm">
                {/* Background Grid Lines */}
                <div className="absolute inset-0 p-6 flex flex-col justify-between pointer-events-none opacity-20">
                   <div className="w-full h-[1px] bg-slate-500"></div>
                   <div className="w-full h-[1px] bg-slate-500"></div>
                   <div className="w-full h-[1px] bg-slate-500"></div>
                   <div className="w-full h-[1px] bg-slate-500"></div>
                </div>

                {/* Bar 1: 0.5 me c^2 */}
                <div className="w-20 flex flex-col justify-end items-center h-full z-10">
                    <div className="flex-1 w-full flex items-end justify-center relative mb-3">
                        <div className="absolute -top-8 w-full text-center text-[10px] font-mono text-physics-cyan">255.5 keV</div>
                        <motion.div 
                            className="w-full bg-gradient-to-t from-physics-cyan/20 to-physics-cyan rounded-t-sm shadow-[0_0_15px_rgba(34,211,238,0.4)]"
                            initial={{ height: 0 }}
                            whileInView={{ height: '80%' }}
                            viewport={{ once: true }}
                            transition={{ type: "spring", stiffness: 50, damping: 20, delay: 0.2 }}
                        />
                    </div>
                    <div className="h-10 flex flex-col items-center justify-center text-[10px] font-bold text-physics-muted uppercase tracking-wider text-center">
                        <span className="text-white">½ mₑc²</span>
                        <span className="font-normal opacity-50 text-[8px] scale-90">Relativistic</span>
                    </div>
                </div>

                {/* Bar 2: EB / alpha^2 */}
                <div className="w-20 flex flex-col justify-end items-center h-full z-10">
                     <div className="flex-1 w-full flex items-end justify-center relative mb-3">
                        <div className="absolute -top-8 w-full text-center text-[10px] font-mono text-physics-gold font-bold">255.5 keV</div>
                        <motion.div 
                            className="w-full bg-gradient-to-t from-physics-gold/20 to-physics-gold rounded-t-sm shadow-[0_0_20px_rgba(251,191,36,0.5)] relative overflow-hidden"
                            initial={{ height: 0 }}
                            whileInView={{ height: '80%' }}
                            viewport={{ once: true }}
                            transition={{ type: "spring", stiffness: 50, damping: 20, delay: 0.6 }}
                        >
                           <div className="absolute inset-0 bg-white/20"></div>
                        </motion.div>
                    </div>
                     <div className="h-10 flex flex-col items-center justify-center text-[10px] font-bold text-physics-muted uppercase tracking-wider text-center">
                        <span className="text-white">Eᵦ / α²</span>
                        <span className="font-normal opacity-50 text-[8px] scale-90">Atomic</span>
                     </div>
                </div>
            </div>
        </div>
    )
}