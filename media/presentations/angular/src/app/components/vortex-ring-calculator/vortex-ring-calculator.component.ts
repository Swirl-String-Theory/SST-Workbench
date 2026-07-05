import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule, Activity, ArrowRight } from 'lucide-angular';

@Component({
  selector: 'app-vortex-ring-calculator',
  standalone: true,
  imports: [FormsModule, LucideAngularModule.pick({ Activity, ArrowRight })],
  templateUrl: './vortex-ring-calculator.component.html',
})
export class VortexRingCalculatorComponent {
  readonly R = signal(10);
  readonly aVal = signal(0.5);
  readonly gamma = signal(100);

  readonly icons = { Activity, ArrowRight };

  readonly velocity = computed(() => {
    const R = this.R();
    const a = this.aVal();
    const gamma = this.gamma();
    const term = Math.log((8 * R) / a);
    return (gamma / (4 * Math.PI * R)) * (term - 0.25);
  });

  readonly energy = computed(() => {
    const R = this.R();
    const a = this.aVal();
    const gamma = this.gamma();
    const term = Math.log((8 * R) / a);
    return 0.5 * Math.pow(gamma, 2) * R * (term - 1.75);
  });

  readonly impulse = computed(() => {
    const R = this.R();
    const gamma = this.gamma();
    return Math.PI * gamma * Math.pow(R, 2);
  });

  readonly aspectRatio = computed(() => this.R() / this.aVal());
}
