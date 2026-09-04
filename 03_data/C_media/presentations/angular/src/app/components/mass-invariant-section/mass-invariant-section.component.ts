import { Component } from '@angular/core';
import { MathBlockComponent } from '../math-block/math-block.component';

@Component({
  selector: 'app-mass-invariant-section',
  standalone: true,
  imports: [MathBlockComponent],
  templateUrl: './mass-invariant-section.component.html',
})
export class MassInvariantSectionComponent {}
