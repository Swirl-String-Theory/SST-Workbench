# Changelog

## v0.5.1 — 2026-09-21 (PC04)

- Promotion firewall hardening on tip v0.5.0.
- Adds `pc04_firewall.py` preflight-only mode requiring promotable A034/A037 CAMPAIGN certs.
- Maps SELFTEST → `BLOCKED_UPSTREAM_SELFTEST`, invalid numerics →
  `BLOCKED_UPSTREAM_NUMERICAL_QUALIFICATION`, missing campaign →
  `BLOCKED_UPSTREAM_MISSING_CAMPAIGN`.
- Never collapses those into `FAIL_TREFOIL`.
