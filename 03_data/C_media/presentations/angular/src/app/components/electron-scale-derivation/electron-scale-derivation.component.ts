import { Component, OnDestroy, OnInit, signal } from '@angular/core';

interface DerivationStep {
  label: string;
  html: string;
}

@Component({
  selector: 'app-electron-scale-derivation',
  standalone: true,
  templateUrl: './electron-scale-derivation.component.html',
})
export class ElectronScaleDerivationComponent implements OnInit, OnDestroy {
  readonly step = signal(0);

  readonly steps: DerivationStep[] = [
    {
      label: 'The Ingredients',
      html: `
        <div class="flex gap-4 items-center justify-center">
          <div class="flex flex-col items-center">
            <div class="w-14 h-14 rounded-full bg-physics-cyan/10 border border-physics-cyan flex items-center justify-center font-serif font-bold text-physics-cyan shadow-[0_0_15px_rgba(34,211,238,0.3)]">rₑ</div>
            <span class="text-[10px] mt-2 font-bold uppercase text-physics-muted">Classical Radius</span>
          </div>
          <div class="flex flex-col items-center">
            <div class="w-14 h-14 rounded-full bg-physics-purple/10 border border-physics-purple flex items-center justify-center font-serif font-bold text-physics-purple shadow-[0_0_15px_rgba(192,132,252,0.3)]">ω꜀</div>
            <span class="text-[10px] mt-2 font-bold uppercase text-physics-muted">Compton Freq</span>
          </div>
          <div class="flex flex-col items-center">
            <div class="w-14 h-14 rounded-full bg-physics-gold/10 border border-physics-gold flex items-center justify-center font-serif font-bold text-physics-gold shadow-[0_0_15px_rgba(251,191,36,0.3)]">Eᵦ</div>
            <span class="text-[10px] mt-2 font-bold uppercase text-physics-muted">Bohr Energy</span>
          </div>
        </div>`,
    },
    {
      label: 'Harmonic Oscillator Ansatz',
      html: `<div class="text-center">
        <p class="font-serif italic text-lg mb-4 text-physics-text">F_max = mₑ ω_*² x_max</p>
        <p class="text-xs text-physics-muted">Let <span class="font-bold text-physics-purple">ω_* = ω꜀ / α</span> and <span class="font-bold text-physics-cyan">x_max = rₑ</span></p>
      </div>`,
    },
    {
      label: 'Combine Constants',
      html: `<div class="text-center">
        <p class="font-serif text-lg text-physics-text">F_max = mₑ <span class="text-slate-500">(</span> <span class="text-physics-purple font-bold">ω꜀</span>/<span class="text-slate-500">α</span> <span class="text-slate-500">)²</span> <span class="text-physics-cyan font-bold">rₑ</span></p>
      </div>`,
    },
    {
      label: 'Resulting Force Scale',
      html: `<div class="text-center">
        <p class="font-serif text-xl font-bold text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]">F_max = mₑ² c³ / (α ħ)</p>
      </div>`,
    },
    {
      label: 'The Energy Identity',
      html: `<div class="text-center p-4 bg-physics-gold/10 rounded-lg border border-physics-gold/30 shadow-[0_0_30px_rgba(251,191,36,0.1)]">
        <p class="font-serif text-2xl font-bold text-physics-gold">½ mₑ c²  =  Eᵦ / α²</p>
        <div class="mt-2 text-xs font-bold text-physics-gold uppercase tracking-widest animate-pulse">Exact Match</div>
      </div>`,
    },
  ];

  private intervalId?: ReturnType<typeof setInterval>;

  ngOnInit(): void {
    this.intervalId = setInterval(() => {
      this.step.update((s) => (s + 1) % this.steps.length);
    }, 4000);
  }

  ngOnDestroy(): void {
    if (this.intervalId) clearInterval(this.intervalId);
  }
}
