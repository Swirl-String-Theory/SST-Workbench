# Version retention policy

This SST-Workbench family uses append-only scientific versioning.

- Keep every released version directory (`A051-vX.Y.Z`).
- Patches and new scientific versions are added as new version directories; older versions are not deleted or overwritten.
- Preserve historical blind/revealed outputs and checksums alongside the version that produced them.
- Never replace historical raw results after reveal; corrections require a new version or a clearly identified additive patch artifact.
- `FAMILY.yaml` may advance `latest`, but `physical_versions` must retain the earlier released versions.

Recorded at user request on 2026-10-02.
