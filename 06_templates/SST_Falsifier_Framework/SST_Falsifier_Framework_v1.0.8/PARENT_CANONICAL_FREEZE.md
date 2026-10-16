# Canonical freeze — SST Falsifier Framework v1.0.7

Freeze date: 2026-10-07  
Status: **CANONICAL_FROZEN**

v1.0.7 is a minimal maintenance successor to the user-supplied canonical v1.0.6 archive. The only functional change is ownership-aware blind scanning: third-party/runtime/build trees are excluded from forbidden-term scans, while falsifier-owned scientific source and blind outputs remain strictly scanned.

Canonical Workbench location:

```text
06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.7
```

Immediate parent archive SHA-256:

```text
24629848e3befcde67c02a935fc78347560ac42107043fbc14aaabdf146ee60d
```

No numerical backend, precision threshold, gate semantics, commitment format, reveal policy, framework bootstrap or report contract changed from v1.0.6. Historical falsifiers remain pinned to their original framework for reproducibility.
