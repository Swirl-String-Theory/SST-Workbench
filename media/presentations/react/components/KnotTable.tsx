import React from 'react';
import { MathBlock } from './MathBlock';

const Check = () => <span className="text-green-400">✓</span>;
const Cross = () => <span className="text-red-400/50">×</span>;

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

const torusData: KnotData[] = [
  { knot: "3_1 (T(2,3))", d2r: true, d2k: "D4, D6", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2, 3", fsg: "Z2" },
  { knot: "5_1 (T(2,5))", d2r: true, d2k: "D4, D10", z2k: "×", "i": "×", reversible: true, amphichiral: false, dark: "no", periods: "2, 5", fsg: "Z2" },
  { knot: "7_1 (T(2,7))", d2r: true, d2k: "D4, D14", z2k: "×", "i": "×", reversible: true, amphichiral: false, dark: "no", periods: "2, 7", fsg: "Z2" },
];

const hyperbolicData: KnotData[] = [
  { knot: "4_1", d2r: true, d2k: "D4", z2k: "Z4", i: "I8", reversible: true, amphichiral: true, dark: "yes+", periods: "2", fsg: "D8" },
  { knot: "5_2, 6_1, 6_2", d2r: true, d2k: "D4", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2", fsg: "D4" },
  { knot: "6_3", d2r: true, d2k: "D4", z2k: "Z4", i: "×", reversible: true, amphichiral: true, dark: "yes+", periods: "2", fsg: "D8" },
  { knot: "7_2, 7_3", d2r: true, d2k: "D4", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2", fsg: "D4" },
  { knot: "7_4", d2r: true, d2k: "D4", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2", fsg: "D8" },
  { knot: "7_5, 7_6", d2r: true, d2k: "D4", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2", fsg: "D4" },
  { knot: "7_7", d2r: true, d2k: "D4", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2", fsg: "D8" },
  { knot: "8_1, 8_2", d2r: true, d2k: "D4", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2", fsg: "D4" },
  { knot: "8_3", d2r: true, d2k: "D4", z2k: "Z4", i: "I8", reversible: true, amphichiral: true, dark: "yes+", periods: "2", fsg: "D8" },
  { knot: "8_4...8_8", d2r: true, d2k: "D4", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2", fsg: "D4" },
  { knot: "8_9", d2r: true, d2k: "D4", z2k: "×", i: "I4", reversible: true, amphichiral: true, dark: "yes+", periods: "2", fsg: "D8" },
  { knot: "8_10", d2r: true, d2k: "×", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "none", fsg: "D2" },
  { knot: "8_11", d2r: true, d2k: "D4", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2", fsg: "D4" },
  { knot: "8_12", d2r: true, d2k: "D4", z2k: "Z4", i: "×", reversible: true, amphichiral: true, dark: "yes+", periods: "2", fsg: "D8" },
  { knot: "8_13...8_15", d2r: true, d2k: "D4", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2", fsg: "D4" },
  { knot: "8_16", d2r: true, d2k: "×", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "none", fsg: "D2" },
  { knot: "8_17", d2r: false, d2k: "×", z2k: "×", i: "×", reversible: false, amphichiral: true, dark: "yes-", periods: "none", fsg: "D2" },
  { knot: "8_18", d2r: true, d2k: "D4, D8", z2k: "Z8", i: "×", reversible: true, amphichiral: true, dark: "yes+", periods: "2, 4", fsg: "D16" },
  { knot: "8_19", d2r: true, d2k: "D4, D6, D8", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2, 3, 4", fsg: "Z2" },
  { knot: "8_20", d2r: true, d2k: "×", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "none", fsg: "D2" },
  { knot: "8_21", d2r: true, d2k: "D4", z2k: "×", i: "×", reversible: true, amphichiral: false, dark: "no", periods: "2", fsg: "D4" },
  { knot: "12a_1202", d2r: true, d2k: "Z2, Z6", z2k: "×", i: "×", reversible: true, amphichiral: true, dark: "yes+", periods: "", fsg: "D12" },
  { knot: "15331", d2r: false, d2k: "Z2", z2k: "×", i: "×", reversible: false, amphichiral: true, dark: "yes-", periods: "", fsg: "" },
];

const TableHeader = ({ children }: { children: React.ReactNode }) => (
  <th className="px-4 py-3 text-left text-xs font-serif font-bold uppercase tracking-wider text-physics-muted border-b border-slate-700">
    {children}
  </th>
);

const TableCell = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <td className={`px-4 py-3 text-sm text-physics-text border-b border-slate-800/50 font-mono ${className}`}>
    {children}
  </td>
);

const KnotTable = ({ title, data }: { title: string; data: KnotData[] }) => {
  return (
    <div className="my-12 overflow-hidden rounded-xl border border-slate-800 bg-physics-card/50 backdrop-blur-sm">
      <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50">
        <h3 className="font-serif text-xl text-white">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px]">
          <thead>
            <tr>
              <TableHeader>Knot</TableHeader>
              <TableHeader><MathBlock math="D_2(r)" /></TableHeader>
              <TableHeader><MathBlock math="D_{2k}" /></TableHeader>
              <TableHeader><MathBlock math="Z_{2k}" /></TableHeader>
              <TableHeader><MathBlock math="I" /></TableHeader>
              <TableHeader>Rev</TableHeader>
              <TableHeader>Amphi</TableHeader>
              <TableHeader>Dark</TableHeader>
              <TableHeader>Periods</TableHeader>
              <TableHeader>FSG</TableHeader>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} className="hover:bg-white/5 transition-colors">
                <TableCell className="font-bold text-physics-cyan">{row.knot}</TableCell>
                <TableCell>{row.d2r ? <Check /> : <Cross />}</TableCell>
                <TableCell>{row.d2k}</TableCell>
                <TableCell>{row.z2k}</TableCell>
                <TableCell>{row.i}</TableCell>
                <TableCell>{row.reversible ? <Check /> : <Cross />}</TableCell>
                <TableCell>{row.amphichiral ? <Check /> : <Cross />}</TableCell>
                <TableCell>
                  <span className={row.dark.includes('yes') ? 'text-green-400' : 'text-physics-muted'}>
                    {row.dark}
                  </span>
                </TableCell>
                <TableCell>{row.periods}</TableCell>
                <TableCell>{row.fsg}</TableCell>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const Glossary = () => (
  <div className="mt-12 p-6 bg-physics-card/30 border border-slate-800 rounded-xl text-sm text-physics-muted">
    <h4 className="font-serif text-white mb-4 text-lg">Glossary of Symmetry Table Symbols</h4>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <p className="mb-2"><strong className="text-physics-cyan"><MathBlock math="D_2(r)" /></strong>: Order-2 Dihedral (Reflectional) Symmetry. Invariant under 180° rotation and reflection.</p>
        <p className="mb-2"><strong className="text-physics-cyan"><MathBlock math="D_{2k}" /></strong>: Higher-Order Dihedral Symmetry. Invariant under full dihedral group of order 2k.</p>
        <p className="mb-2"><strong className="text-physics-cyan"><MathBlock math="Z_{2k}" /></strong>: Cyclic Symmetry of Order 2k. Rotational symmetry by <MathBlock math="2\pi/(2k)" />.</p>
        <p className="mb-2"><strong className="text-physics-cyan"><MathBlock math="I" /></strong>: Icosahedral Symmetry or Inversion.</p>
      </div>
      <div>
        <p className="mb-2"><strong className="text-physics-cyan">reversible</strong>: Topologically equivalent to itself with orientation reversed.</p>
        <p className="mb-2"><strong className="text-physics-cyan">amphichiral</strong>: Equivalent to its mirror image.</p>
        <p className="mb-2"><strong className="text-physics-cyan">periods</strong>: Integer <MathBlock math="n" /> for which the knot is invariant under <MathBlock math="2\pi/n" /> rotation.</p>
        <p className="mb-2"><strong className="text-physics-cyan">FSG</strong>: Full Symmetry Group.</p>
      </div>
    </div>
  </div>
);

export const TorusKnotsTable = () => <KnotTable title="Table 3: Torus Knots (Lepton Sector)" data={torusData} />;
export const HyperbolicKnotsTable = () => <KnotTable title="Table 4: Hyperbolic Knots (Quark Sector)" data={hyperbolicData} />;
