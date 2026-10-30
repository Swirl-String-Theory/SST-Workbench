# E010 v0.3.6 multi-ZIP distribution

Extract the CORE ZIP and all seven data ZIP archives into the same destination directory. Each ZIP uses the same internal path prefix for generated output files, so Windows `Expand-Archive` safely assembles the complete atlas.

- KNOTS_01: T(2,3), T(3,2), T(2,5), T(2,7), T(3,4), T(3,5)
- KNOTS_02: T(3,7), T(4,3), T(4,5), T(5,2), T(5,3), T(5,4)
- KNOTS_03: T(2,9), T(2,11), T(2,13), T(2,15), T(3,8), T(3,10)
- KNOTS_04: T(4,7), T(4,9), T(5,6), T(5,7), T(6,7), T(7,2)
- LINKS_01: T(3,3), T(3,6)
- LINKS_02: T(3,9), T(6,15)
- LINKS_03: T(6,21), T(6,9)

The ROOT-level SHA-256 listing `E010_v0.3.6_RELEASE_ARCHIVES.sha256` covers the core and seven data ZIPs. The atlas `MANIFEST_SHA256.txt` covers the 10,164 XYZ files and the 5 metadata files (not itself). Use `E010-v0.3.6/assemble_atlas.ps1` for checksummed extraction.

**Note:** These ZIPs contain analytic geometry and pending *scenarios*, not computed dynamics; the six link identifiers retain only their historical VortexLab `stalled-not-converged` label.
