# A057 v0.2.0 validation status

This package is a scientific successor, not a result migration.

## Locally validated

- Python syntax compilation for the complete package.
- Existing geometry/energy/Hessian/Jacobian unit tests.
- pybind11 3.x / MSVC source-compatibility regression tests.
- E013 member-contract schema checks.
- Synthetic E013 common-carrier-manifest validation, including rejection of:
  - wrong schema;
  - wrong E011 release;
  - missing join keys;
  - legacy-evidence flag not false.
- Implementation commitment recalculated from the final v0.2.0 source tree.
- Nonced blind/reveal commitments regenerated for v0.2.0.
- Frozen protocol regenerated create-once for the final v0.2.0 protocol bytes.
- Public-tree protected-term scan.

## Requires Windows Workbench confirmation

This build container does not contain the source-native E010/E011 geometry files or the
Windows SST Falsifier Framework installation. Therefore the first actual source reload and
C++/pybind MSVC build remain target-machine acceptance tests.

Expected order:

```bat
run_00_install.cmd
run_all.cmd FREEZE
```

Then register/run through E013. BASIC is a carrier/plumbing diagnostic; FULL and CERTIFY are
the relevant cross-provider science campaigns.
