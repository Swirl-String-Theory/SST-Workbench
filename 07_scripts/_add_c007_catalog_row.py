"""Register C007 and record the realignment in CATALOG_v0.1.md.

The U(q) twisted vortex ring experiment was added after the 2026-09-04 freeze, when
GUI/additional for Vlab turned out to be a self-contained physics experiment rather
than an app asset. It first landed on C006, which the catalog assigns to
kelvin_floquet_workbench, so it takes the next free number.
"""
from __future__ import annotations

from pathlib import Path

CATALOG = (
    Path(__file__).resolve().parents[1]
    / ".cursor" / "plans" / "restructure" / "CATALOG_v0.1.md"
)

C006_LINE_PREFIX = "| C006 | `kelvin_floquet_workbench`"

C007_ROW = (
    "| C007 | `uq_twisted_vortex_ring` | U(q) Twisted Vortex Ring Speed Deficit "
    "Experiment | `GUI/additional for Vlab/` | 2026-07-25 | confirmed |\n"
)

NOTE = """
**C007 was added after the freeze.** `GUI/additional for Vlab/` is not an app asset: it
is a self-contained physics experiment that integrates the axisymmetric Euler equations
with swirl on a 256x512 grid to fix the Kirchhoff twist-stiffness prefactor `C_eff` and
tell a Rankine core from a hollow one. The frozen tables classified `GUI/` as apps, so
it never surfaced there. It briefly occupied C006, which belongs to
`kelvin_floquet_workbench`, and moved to the next free number.
"""


def main() -> None:
    lines = CATALOG.read_text(encoding="utf-8").splitlines(keepends=True)
    if any(line.startswith("| C007 |") for line in lines):
        print("C007 already present")
        return

    out: list[str] = []
    for line in lines:
        out.append(line)
        if line.startswith(C006_LINE_PREFIX):
            out.append(C007_ROW)
            out.append(NOTE)
    CATALOG.write_text("".join(out), encoding="utf-8")
    print("C007 registered")


if __name__ == "__main__":
    main()
