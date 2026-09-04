
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/

import React, { useState, useEffect } from 'react';
import { HeroScene, RotatingFluidScene } from './components/QuantumScene';
import { ElectronScaleDerivation, VortexRingCalculator, UnifiedEnergyChart } from './components/Diagrams';
import { ArrowDown, Menu, X, FileText } from 'lucide-react';
import { CmsProvider, useCms } from './components/CmsContext';
import { AdminDashboard } from './components/AdminDashboard';
import { TorusKnotsTable, HyperbolicKnotsTable, Glossary } from './components/KnotTable';
import { MassInvariantSection } from './components/MassInvariantSection';
import { StarshipCoilSimulator } from './components/StarshipCoilSimulator';

const AuthorCard = ({ name, role, delay }: { name: string, role: string, delay: string }) => {
  return (
    <div className="flex flex-col group animate-fade-in-up items-center p-8 bg-physics-card border border-slate-800 rounded-xl shadow-lg hover:shadow-physics-cyan/10 transition-all duration-500 w-full max-w-xs hover:border-physics-cyan/50 relative overflow-hidden" style={{ animationDelay: delay }}>
      <div className="absolute inset-0 bg-gradient-to-b from-physics-cyan/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
      <h3 className="font-serif text-2xl text-white text-center mb-3 relative z-10">{name}</h3>
      <div className="w-12 h-0.5 bg-physics-cyan mb-4 opacity-60 shadow-[0_0_8px_#22d3ee]"></div>
      <p className="text-xs text-physics-muted font-bold uppercase tracking-widest text-center leading-relaxed relative z-10">{role}</p>
    </div>
  );
};

const AppContent: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const { content } = useCms();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    setMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      const headerOffset = 100;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth"
      });
    }
  };

  return (
    <div className="min-h-screen bg-physics-bg text-physics-text selection:bg-physics-cyan selection:text-physics-bg overflow-x-hidden">
      <AdminDashboard />
      
      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-physics-bg/80 backdrop-blur-md border-b border-slate-800 py-4' : 'bg-transparent py-6'}`}>
        <div className="container mx-auto px-6 flex justify-between items-center">
          <div className="flex items-center gap-4 cursor-pointer group" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="w-10 h-10 bg-physics-cyan/10 border border-physics-cyan rounded-full flex items-center justify-center text-physics-cyan font-serif font-bold text-xl shadow-[0_0_15px_rgba(34,211,238,0.2)] group-hover:shadow-[0_0_20px_rgba(34,211,238,0.5)] transition-all duration-300">Ω</div>
            <span className={`font-serif font-bold text-lg tracking-wide transition-opacity text-white`}>
              {content.author.name.split(' ')[1].toUpperCase()} <span className="font-normal text-physics-cyan">2025</span>
            </span>
          </div>
          
          <div className="hidden md:flex items-center gap-8 text-sm font-medium tracking-wide text-physics-muted">
            <a href="#introduction" onClick={scrollToSection('introduction')} className="hover:text-white hover:shadow-[0_0_10px_rgba(255,255,255,0.3)] transition-all cursor-pointer uppercase text-xs tracking-widest">Introduction</a>
            <a href="#unification" onClick={scrollToSection('unification')} className="hover:text-physics-cyan hover:shadow-[0_0_10px_rgba(34,211,238,0.3)] transition-all cursor-pointer uppercase text-xs tracking-widest">Electron Scale</a>
            <a href="#taxonomy" onClick={scrollToSection('taxonomy')} className="hover:text-physics-gold hover:shadow-[0_0_10px_rgba(251,191,36,0.3)] transition-all cursor-pointer uppercase text-xs tracking-widest">Taxonomy</a>
            <a href="#simulator" onClick={scrollToSection('simulator')} className="hover:text-physics-cyan hover:shadow-[0_0_10px_rgba(34,211,238,0.3)] transition-all cursor-pointer uppercase text-xs tracking-widest">Simulator</a>
            <a href="#fluids" onClick={scrollToSection('fluids')} className="hover:text-physics-purple hover:shadow-[0_0_10px_rgba(192,132,252,0.3)] transition-all cursor-pointer uppercase text-xs tracking-widest">Fluid Analogues</a>
            <a href="#papers" onClick={scrollToSection('papers')} className="hover:text-physics-gold hover:shadow-[0_0_10px_rgba(251,191,36,0.3)] transition-all cursor-pointer uppercase text-xs tracking-widest">Papers</a>
            <div className="w-px h-4 bg-slate-700"></div>
            <span className="text-slate-600 text-[10px] font-mono">GRONINGEN, NL</span>
          </div>

          <button className="md:hidden text-white p-2" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X /> : <Menu />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="fixed inset-0 z-40 bg-physics-bg flex flex-col items-center justify-center gap-8 text-xl font-serif animate-fade-in text-white">
            <a href="#introduction" onClick={scrollToSection('introduction')} className="hover:text-physics-cyan transition-colors cursor-pointer uppercase">Introduction</a>
            <a href="#unification" onClick={scrollToSection('unification')} className="hover:text-physics-cyan transition-colors cursor-pointer uppercase">Electron Scale</a>
            <a href="#taxonomy" onClick={scrollToSection('taxonomy')} className="hover:text-physics-gold transition-colors cursor-pointer uppercase">Taxonomy</a>
            <a href="#simulator" onClick={scrollToSection('simulator')} className="hover:text-physics-cyan transition-colors cursor-pointer uppercase">Simulator</a>
            <a href="#fluids" onClick={scrollToSection('fluids')} className="hover:text-physics-cyan transition-colors cursor-pointer uppercase">Fluid Analogues</a>
            <a href="#papers" onClick={scrollToSection('papers')} className="hover:text-physics-cyan transition-colors cursor-pointer uppercase">Papers</a>
        </div>
      )}

      {/* Hero Section */}
      <header className="relative h-screen flex items-center justify-center overflow-hidden">
        <HeroScene />
        <div className="absolute inset-0 z-0 pointer-events-none bg-[radial-gradient(circle_at_center,transparent_0%,#020617_90%)]" />

        <div className="relative z-10 container mx-auto px-6 text-center">
          <div className="inline-block mb-6 px-4 py-1.5 border border-physics-cyan/30 text-physics-cyan text-[10px] tracking-[0.3em] uppercase font-bold rounded-full backdrop-blur-md bg-physics-cyan/5 shadow-[0_0_15px_rgba(34,211,238,0.15)] animate-glow">
            {content.hero.badge}
          </div>
          <h1 className="font-serif text-5xl md:text-7xl lg:text-9xl font-medium leading-tight md:leading-[0.9] mb-8 text-white drop-shadow-[0_0_30px_rgba(255,255,255,0.1)]">
            {content.hero.title} <br/><span className="italic font-normal text-transparent bg-clip-text bg-gradient-to-r from-physics-cyan via-white to-physics-purple text-3xl md:text-5xl block mt-4 pb-2">& {content.hero.subtitle}</span>
          </h1>
          <p className="max-w-2xl mx-auto text-lg md:text-xl text-physics-muted font-light leading-relaxed mb-12">
            {content.hero.description}
          </p>
          
          <div className="flex justify-center">
             <a href="#introduction" onClick={scrollToSection('introduction')} className="group flex flex-col items-center gap-3 text-xs font-bold tracking-widest text-physics-muted hover:text-white transition-colors cursor-pointer uppercase">
                <span>Explore Research</span>
                <span className="p-3 border border-slate-700 rounded-full group-hover:border-physics-cyan group-hover:bg-physics-cyan/10 transition-all shadow-[0_0_0_rgba(34,211,238,0)] group-hover:shadow-[0_0_15px_rgba(34,211,238,0.3)]">
                    <ArrowDown size={16} />
                </span>
             </a>
          </div>
        </div>
      </header>

      <main>
        {/* Introduction */}
        <section id="introduction" className="py-32 bg-physics-bg relative">
          <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent"></div>
          
          <div className="container mx-auto px-6 md:px-12 grid grid-cols-1 md:grid-cols-12 gap-12 items-start">
            <div className="md:col-span-4 sticky top-32">
              <div className="inline-block mb-3 text-[10px] font-bold tracking-[0.2em] text-physics-cyan uppercase">Introduction</div>
              <h2 className="font-serif text-4xl md:text-5xl mb-6 leading-tight text-white">{content.intro.title}</h2>
              <div className="w-20 h-1 bg-gradient-to-r from-physics-cyan to-transparent mb-6"></div>
            </div>
            <div className="md:col-span-8 text-lg text-physics-muted leading-relaxed space-y-8 font-light">
              <p>
                <span className="text-6xl float-left mr-4 mt-[-10px] font-serif text-physics-cyan opacity-80">
                  {content.intro.body[0].charAt(0)}
                </span>
                {content.intro.body[0].slice(1)}
              </p>
              {content.intro.body.slice(1).map((text, i) => (
                <p key={i}>{text}</p>
              ))}
              <div className="p-6 bg-physics-card border border-slate-800 rounded-xl mt-8">
                <h4 className="font-serif text-white mb-2">Abstract</h4>
                <p className="text-sm italic">
                  This note develops a definitive symmetry and topological taxonomy of knots as candidate swirl-string configurations in Swirl-String Theory (SST). Building on standard knot tables, we organise prime knots (with emphasis on torus and hyperbolic knots up to eight crossings) by their discrete symmetry groups.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Paper 1: Electron Scale */}
        <section id="unification" className="py-32 relative bg-[#050b1d]">
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-physics-purple/5 blur-[120px] rounded-full pointer-events-none"></div>

            <div className="container mx-auto px-6 relative z-10">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-physics-purple/10 text-physics-purple text-[10px] font-bold tracking-widest uppercase rounded-full mb-6 border border-physics-purple/20 shadow-[0_0_10px_rgba(192,132,252,0.15)]">
                            {content.papers[0]?.tag || "PAPER I"}
                        </div>
                        <h2 className="font-serif text-4xl md:text-5xl mb-8 text-white">{content.papers[0]?.title || "The Electron Scale Identity"}</h2>
                        <p className="text-lg text-physics-muted mb-6 leading-relaxed">
                           We construct a classical harmonic oscillator using the electron mass, a Compton-rescaled frequency, and the classical electron radius as amplitude.
                        </p>
                        <p className="text-lg text-physics-muted mb-6 leading-relaxed">
                            Remarkably, the resulting maximal force depends only on fundamental constants, and the energy at a specific Compton-scale radius matches exactly half the electron rest energy.
                        </p>
                    </div>
                    <div>
                        <ElectronScaleDerivation />
                    </div>
                </div>
            </div>
        </section>

        <MassInvariantSection />

        <section id="taxonomy" className="py-32 bg-physics-bg border-t border-slate-800">
          <div className="container mx-auto px-6">
            <div className="mb-12 text-center">
              <div className="inline-block mb-3 text-[10px] font-bold tracking-[0.2em] text-physics-gold uppercase">Taxonomy</div>
              <h2 className="font-serif text-4xl md:text-5xl mb-6 text-white">Knot Symmetry Classification</h2>
              <p className="text-physics-muted max-w-2xl mx-auto">
                A definitive symmetry and topological taxonomy of knots as candidate swirl-string configurations.
              </p>
            </div>
            <TorusKnotsTable />
            <HyperbolicKnotsTable />
            <Glossary />
          </div>
        </section>

        <section id="simulator" className="py-32 bg-[#050505] border-t border-slate-800">
          <div className="container mx-auto px-6">
            <div className="mb-12 text-center">
              <div className="inline-block mb-3 text-[10px] font-bold tracking-[0.2em] text-physics-cyan uppercase">Simulation</div>
              <h2 className="font-serif text-4xl md:text-5xl mb-6 text-white">SST Starship Coil</h2>
              <p className="text-physics-muted max-w-2xl mx-auto">
                Interactive simulation of Topological Vorticity Confinement. Adjust frequency to find resonance.
              </p>
            </div>
            <StarshipCoilSimulator />
          </div>
        </section>

        <section className="py-16 bg-physics-bg">
             <div className="container mx-auto px-6">
                 <UnifiedEnergyChart />
             </div>
        </section>

        <section className="py-32 bg-[#020617] text-white overflow-hidden relative border-t border-slate-900">
            <div className="absolute top-0 left-0 w-full h-full opacity-30 pointer-events-none">
                <div className="w-[800px] h-[800px] rounded-full bg-physics-cyan/5 blur-[150px] absolute top-[-200px] left-[-200px]"></div>
            </div>

            <div className="container mx-auto px-6 relative z-10">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
                     <div className="order-2 lg:order-1">
                        <VortexRingCalculator />
                     </div>
                     <div className="order-1 lg:order-2">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-physics-cyan/10 text-physics-cyan text-[10px] font-bold tracking-widest uppercase rounded-full mb-6 border border-physics-cyan/20 shadow-[0_0_10px_rgba(34,211,238,0.15)]">
                            {content.papers[3]?.tag || "PAPER IV"}
                        </div>
                        <h2 className="font-serif text-4xl md:text-5xl mb-8 text-white">{content.papers[3]?.title || "Vortex Loops"}</h2>
                        <p className="text-lg text-physics-muted mb-6 leading-relaxed">
                            Vortex rings in incompressible fluids behave like localized particles. They carry finite energy, impulse, and helicity.
                        </p>
                        <p className="text-lg text-physics-muted leading-relaxed">
                            This research organizes classical results for thin-core circular vortex rings and extends the discussion to knotted filaments. The "effective mass" of the ring is derived from the ratio of Impulse to Velocity.
                        </p>
                     </div>
                </div>
            </div>
        </section>

        <section id="fluids" className="py-32 bg-gradient-to-b from-[#050b1d] to-[#020617] border-t border-slate-800/50">
             <div className="container mx-auto px-6 grid grid-cols-1 md:grid-cols-12 gap-16">
                <div className="md:col-span-5 relative">
                    <div className="aspect-square bg-physics-card rounded-2xl overflow-hidden relative border border-slate-800 shadow-2xl">
                        <RotatingFluidScene />
                        <div className="absolute bottom-6 left-0 right-0 text-center text-xs text-physics-muted/60 font-serif italic tracking-wider">Simulation of a Rotating Fluid Experiment</div>
                    </div>
                </div>
                <div className="md:col-span-7 flex flex-col justify-center">
                    <div className="inline-block mb-4 text-[10px] font-bold tracking-widest text-physics-gold uppercase">PAPERS V & VI</div>
                    <h2 className="font-serif text-4xl md:text-5xl mb-8 text-white">Fluid Analogues for Gravity</h2>
                    <p className="text-lg text-physics-muted mb-6 leading-relaxed">
                        In swirling flows, pressure gradients balance centripetal acceleration. We show that for a specific azimuthal velocity profile (v ~ 1/√r), the pressure field mimics a Newtonian gravitational potential (-GM/r).
                    </p>
                    <p className="text-lg text-physics-muted mb-8 leading-relaxed">
                        Additionally, we derive an effective mass density from rotational kinetic energy and show how circulation in a rigid rotation provides a fluid-mechanical representation of kinematic time dilation.
                    </p>
                    
                    <div className="p-8 bg-physics-card/30 border border-slate-800 rounded-lg border-l-2 border-l-physics-gold backdrop-blur-sm relative overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-r from-physics-gold/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                        <p className="font-serif italic text-xl text-physics-text mb-4 relative z-10">
                            "The analysis remains strictly within the framework of classical incompressible Euler flow... providing a pedagogical link between relativistic kinematics and classical rotational flows."
                        </p>
                        <span className="text-[10px] font-bold text-physics-muted tracking-wider uppercase relative z-10">— {content.author.name}, 2025</span>
                    </div>
                </div>
             </div>
        </section>

        {/* Papers List */}
        <section id="papers" className="py-32 bg-physics-bg relative">
           <div className="absolute top-0 left-0 w-full h-px bg-slate-800"></div>
           <div className="container mx-auto px-6">
                <div className="text-center mb-20">
                    <div className="inline-block mb-3 text-[10px] font-bold tracking-widest text-physics-muted uppercase">PUBLICATIONS</div>
                    <h2 className="font-serif text-4xl md:text-6xl mb-4 text-white">The 2025 Series</h2>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {content.papers.map((paper, i) => (
                        <div key={paper.id} className="bg-physics-card p-8 rounded-xl border border-slate-800 hover:border-physics-cyan/30 transition-all cursor-pointer group hover:bg-slate-900 shadow-lg hover:shadow-physics-cyan/5 hover:-translate-y-1 animate-fade-in">
                            <div className="flex items-start justify-between mb-6">
                                <span className={`text-[10px] font-bold ${paper.color} uppercase tracking-widest border border-slate-700 px-2 py-1 rounded bg-black/20`}>{paper.tag}</span>
                                <FileText size={16} className="text-slate-600 group-hover:text-white transition-colors" />
                            </div>
                            <h3 className="font-serif text-lg text-slate-200 leading-snug group-hover:text-white transition-colors">{paper.title}</h3>
                        </div>
                    ))}
                </div>
                
                <div className="mt-24 flex justify-center">
                    <AuthorCard 
                        name={content.author.name} 
                        role={content.author.role} 
                        delay="0s" 
                    />
                </div>
           </div>
        </section>

      </main>

      <footer className="bg-[#010409] text-physics-muted py-20 border-t border-slate-900">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-10">
            <div className="text-center md:text-left">
                <div className="text-white font-serif font-bold text-2xl mb-2">{content.author.name}</div>
                <p className="text-sm text-slate-400">{content.author.location}</p>
                <p className="text-xs mt-3 text-slate-600 font-mono">{content.author.email}</p>
            </div>
            <div className="flex gap-8 text-[10px] font-bold tracking-widest uppercase">
                <a href="#unification" className="hover:text-physics-cyan transition-colors">Electron Scale</a>
                <a href="#fluids" className="hover:text-physics-purple transition-colors">Fluid Analogues</a>
                <a href="#papers" className="hover:text-physics-gold transition-colors">Publications</a>
            </div>
        </div>
        <div className="text-center mt-16 text-[10px] text-slate-700 font-mono uppercase tracking-wider">
            © 2025 {content.author.name}. CMS Powered.
        </div>
      </footer>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <CmsProvider>
      <AppContent />
    </CmsProvider>
  );
};

export default App;
