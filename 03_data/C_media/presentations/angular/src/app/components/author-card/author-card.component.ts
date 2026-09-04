import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-author-card',
  standalone: true,
  template: `
    <div
      class="flex flex-col group animate-fade-in-up items-center p-8 bg-physics-card border border-slate-800 rounded-xl shadow-lg hover:shadow-physics-cyan/10 transition-all duration-500 w-full max-w-xs hover:border-physics-cyan/50 relative overflow-hidden"
      [style.animation-delay]="delay"
    >
      <div
        class="absolute inset-0 bg-gradient-to-b from-physics-cyan/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"
      ></div>
      <h3 class="font-serif text-2xl text-white text-center mb-3 relative z-10">{{ name }}</h3>
      <div class="w-12 h-0.5 bg-physics-cyan mb-4 opacity-60 shadow-[0_0_8px_#22d3ee]"></div>
      <p
        class="text-xs text-physics-muted font-bold uppercase tracking-widest text-center leading-relaxed relative z-10"
      >
        {{ role }}
      </p>
    </div>
  `,
})
export class AuthorCardComponent {
  @Input() name = '';
  @Input() role = '';
  @Input() delay = '0s';
}
