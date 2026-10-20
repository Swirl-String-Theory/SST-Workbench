GPE GPU v0.1.1 -- PRE-FREEZE preflight PATHFIX

Probleem: preflight_report.py gebruikt ROOT=Path(__file__).resolve().parents[1].
Fix: ROOT=Path(__file__).resolve().parent.

1. Pak deze ZIP uit op een tijdelijke plek.
2. Start apply_patch.cmd.
3. Ga naar de bestaande GPE_EXT_001_GPE_GPU_Benchmark_v0.1.1 instantie.
4. Run: run_all.cmd BASIC (daarna eventueel run_all.cmd FULL).

LET OP: De fix moet worden uitgevoerd op v0.1.1, NIET op de v0.1.0
installer of een bevroren protocol. De patch weigert wijzigingen als
preregistration/FROZEN_PROTOCOL.json bestaat.

De lokale test heeft de echte preflight-rapportgeneratiecode gebruikt,
met een gemockte frameworkbootstrap. De volledige Windows/Arc-A770
uitvoering blijft onafhankelijk op de doelcomputer te kwalificeren.
