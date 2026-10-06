from __future__ import annotations

def render_report(*, version: str, verdict: str, seed_id: str | None, provider: str | None,
                  c006_version: str, preset: str, sample_count: int, branch_ok: bool,
                  handoff_status: str, handoff_blockers: list[str]) -> str:
    lines=[
        f"# E012 v{version} run report","",
        f"Verdict: **{verdict}**","",
        f"E011 seed: `{seed_id}` ({provider})",
        f"C006: `v{c006_version}`",
        f"Preset: `{preset}`",
        f"Resolved mode samples: `{sample_count}`",
        f"Dimensionless branch converged: `{branch_ok}`","",
        "The branch is a frozen-local C006 Kelvin-generator result.  It is not a true Floquet branch and is not identified as a photon.","",
        f"A052 SI handoff: **{handoff_status}**",
    ]
    if handoff_blockers:
        lines += ["", "A052 handoff blockers:"] + [f"- {x}" for x in handoff_blockers]
    return "\n".join(lines)+"\n"
