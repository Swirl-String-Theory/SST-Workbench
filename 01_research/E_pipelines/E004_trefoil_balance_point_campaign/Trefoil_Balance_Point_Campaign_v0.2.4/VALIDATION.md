# Validation — v0.2.4

Artifact-side checks:

- source v0.2.3 output SHA-256: `9872d83a6af3cc4431764f590e823b93311208a65f9ad03cd472a1f6f1a62856`;
- all 20 historical i0 coordinate exports are byte-identical: PASS;
- common i0 SHA-256: `2f163170e0c884a75a0da8e9ce1efab4c9863a7eb3b214da92f1caca225e5ded`;
- design selftest: PASS;
- preregistration lock: PASS;
- KPC syntax: PASS;
- generated: 3 overlap cold starts + 13 extension cold starts + 16 continuations;
- continuation prefixes contain no fitto/refine/centre before first resumed ago;
- source importer tested against supplied v0.2.3 output ZIP: PASS;
- overlap-gate code path tested with exact historical replay: PASS;
- reports explicitly UTF-8;
- actual KnotPlot overlap reproduction and 0->400k dynamics require Windows target.
