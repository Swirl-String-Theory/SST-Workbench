import { Component, Input } from '@angular/core';
import { MathBlockComponent } from '../math-block/math-block.component';

interface KnotData {
  knot: string;
  d2r: boolean;
  d2k: string;
  z2k: string;
  i: string;
  reversible: boolean;
  amphichiral: boolean;
  dark: string;
  periods: string;
  fsg: string;
}

const TORUS_DATA: KnotData[] = [
  { knot: '3_1 (T(2,3))', d2r: true, d2k: 'D4, D6', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2, 3', fsg: 'Z2' },
  { knot: '5_1 (T(2,5))', d2r: true, d2k: 'D4, D10', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2, 5', fsg: 'Z2' },
  { knot: '7_1 (T(2,7))', d2r: true, d2k: 'D4, D14', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2, 7', fsg: 'Z2' },
];

const HYPERBOLIC_DATA: KnotData[] = [
  { knot: '4_1', d2r: true, d2k: 'D4', z2k: 'Z4', i: 'I8', reversible: true, amphichiral: true, dark: 'yes+', periods: '2', fsg: 'D8' },
  { knot: '5_2, 6_1, 6_2', d2r: true, d2k: 'D4', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2', fsg: 'D4' },
  { knot: '6_3', d2r: true, d2k: 'D4', z2k: 'Z4', i: '×', reversible: true, amphichiral: true, dark: 'yes+', periods: '2', fsg: 'D8' },
  { knot: '7_2, 7_3', d2r: true, d2k: 'D4', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2', fsg: 'D4' },
  { knot: '7_4', d2r: true, d2k: 'D4', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2', fsg: 'D8' },
  { knot: '7_5, 7_6', d2r: true, d2k: 'D4', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2', fsg: 'D4' },
  { knot: '7_7', d2r: true, d2k: 'D4', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2', fsg: 'D8' },
  { knot: '8_1, 8_2', d2r: true, d2k: 'D4', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2', fsg: 'D4' },
  { knot: '8_3', d2r: true, d2k: 'D4', z2k: 'Z4', i: 'I8', reversible: true, amphichiral: true, dark: 'yes+', periods: '2', fsg: 'D8' },
  { knot: '8_4...8_8', d2r: true, d2k: 'D4', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2', fsg: 'D4' },
  { knot: '8_9', d2r: true, d2k: 'D4', z2k: '×', i: 'I4', reversible: true, amphichiral: true, dark: 'yes+', periods: '2', fsg: 'D8' },
  { knot: '8_10', d2r: true, d2k: '×', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: 'none', fsg: 'D2' },
  { knot: '8_11', d2r: true, d2k: 'D4', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2', fsg: 'D4' },
  { knot: '8_12', d2r: true, d2k: 'D4', z2k: 'Z4', i: '×', reversible: true, amphichiral: true, dark: 'yes+', periods: '2', fsg: 'D8' },
  { knot: '8_13...8_15', d2r: true, d2k: 'D4', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2', fsg: 'D4' },
  { knot: '8_16', d2r: true, d2k: '×', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: 'none', fsg: 'D2' },
  { knot: '8_17', d2r: false, d2k: '×', z2k: '×', i: '×', reversible: false, amphichiral: true, dark: 'yes-', periods: 'none', fsg: 'D2' },
  { knot: '8_18', d2r: true, d2k: 'D4, D8', z2k: 'Z8', i: '×', reversible: true, amphichiral: true, dark: 'yes+', periods: '2, 4', fsg: 'D16' },
  { knot: '8_19', d2r: true, d2k: 'D4, D6, D8', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2, 3, 4', fsg: 'Z2' },
  { knot: '8_20', d2r: true, d2k: '×', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: 'none', fsg: 'D2' },
  { knot: '8_21', d2r: true, d2k: 'D4', z2k: '×', i: '×', reversible: true, amphichiral: false, dark: 'no', periods: '2', fsg: 'D4' },
  { knot: '12a_1202', d2r: true, d2k: 'Z2, Z6', z2k: '×', i: '×', reversible: true, amphichiral: true, dark: 'yes+', periods: '', fsg: 'D12' },
  { knot: '15331', d2r: false, d2k: 'Z2', z2k: '×', i: '×', reversible: false, amphichiral: true, dark: 'yes-', periods: '', fsg: '' },
];

@Component({
  selector: 'app-torus-knots-table',
  standalone: true,
  imports: [KnotTableInnerComponent],
  template: `<app-knot-table-inner title="Table 3: Torus Knots (Lepton Sector)" [data]="torusData" />`,
})
export class TorusKnotsTableComponent {
  readonly torusData = TORUS_DATA;
}

@Component({
  selector: 'app-hyperbolic-knots-table',
  standalone: true,
  imports: [KnotTableInnerComponent],
  template: `<app-knot-table-inner title="Table 4: Hyperbolic Knots (Quark Sector)" [data]="hyperbolicData" />`,
})
export class HyperbolicKnotsTableComponent {
  readonly hyperbolicData = HYPERBOLIC_DATA;
}

@Component({
  selector: 'app-knot-glossary',
  standalone: true,
  imports: [MathBlockComponent],
  templateUrl: './knot-glossary.component.html',
})
export class KnotGlossaryComponent {}

@Component({
  selector: 'app-knot-table-inner',
  standalone: true,
  imports: [MathBlockComponent],
  templateUrl: './knot-table-inner.component.html',
})
export class KnotTableInnerComponent {
  @Input({ required: true }) title!: string;
  @Input({ required: true }) data: KnotData[] = [];
}
