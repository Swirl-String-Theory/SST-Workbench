import { Component } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';

@Component({
  selector: 'app-unified-energy-chart',
  standalone: true,
  animations: [
    trigger('barGrow', [
      transition(':enter', [
        style({ height: '0%' }),
        animate('800ms 200ms cubic-bezier(0.34, 1.56, 0.64, 1)', style({ height: '80%' })),
      ]),
    ]),
  ],
  templateUrl: './unified-energy-chart.component.html',
})
export class UnifiedEnergyChartComponent {}
