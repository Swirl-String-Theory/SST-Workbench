from __future__ import annotations

def render_report(*, verdict: str, preset: str, providers: list[dict], cross_provider_ok: bool,
                  branch_ok: bool, handoff_status: str, handoff_blockers: list[str]) -> str:
    lines=["# E012 v0.2.0 run report","",f"Verdict: **{verdict}**","",f"Preset: `{preset}`","",
           "## Provider results",""]
    for p in providers:
        lines.append(f"- `{p.get('provider_group')}`: qualified modes `{p.get('qualified_mode_count')}`, "
                     f"RPO accepted `{p.get('rpo_accepted')}`, numerical branch `{p.get('numerical_branch_ok')}`")
    lines += ["",f"Cross-provider dynamic agreement: `{cross_provider_ok}`",
              f"Dimensionless branch qualified: `{branch_ok}`","",
              "v0.2.0 uses a same-generator RPO qualification and eigenvector-overlap branch tracking. "
              "An accepted RPO is conditioning evidence only; no true Floquet/monodromy claim is made.","",
              f"A052 SI handoff: **{handoff_status}**"]
    if handoff_blockers:
        lines += ["","A052 handoff blockers:"]+[f"- {x}" for x in handoff_blockers]
    return "\n".join(lines)+"\n"
