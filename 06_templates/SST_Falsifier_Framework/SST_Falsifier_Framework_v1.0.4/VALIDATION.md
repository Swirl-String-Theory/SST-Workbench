# SST Falsifier Framework v1.0.4 — Canonical Validation Record

Freeze date: 2026-10-07
Status: **CANONICAL_FROZEN**

## Source of truth

v1.0.4 was created directly from the user-supplied local snapshot `SST_Falsifier_Framework_v1.0.3(1).zip`.

- source snapshot SHA-256: `259161ec2ff73b9ee6cee8086d07a539ff1a1d88daed2e5f5ae716959c05f950`
- transient `.venv`, cache directories, generated `build/` binaries and egg-info were excluded from the canonical source tree.
- target-machine selftest JSON was retained as immutable evidence under `validation/hardware/2026-10-07_arc-a770/`.

## Target-machine backend evidence

`BACKEND_SELFTEST.json` SHA-256: `106c1866557e1cf8c1dc4f91fad84337214ecd452b7694abda20e92b0e86da9c`

- overall pass: **True**
- C++/OpenMP available: **True**
- C++ compiler: `C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx86\x64\cl.exe`
- C++ compiler family: `msvc`
- C++ toolset: `14.44.35207`
- SYCL available: **True**
- SYCL device: `Intel(R) Arc(TM) A770 Graphics`
- native FP64 on selected GPU: **False**
- DD32 supported: **True**
- `libmmd_path`: `C:\Program Files (x86)\Intel\oneAPI\compiler\2026.1\lib\libmmd.lib`
- `msvcrt_path`: `C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\lib\x64\msvcrt.lib`

DD32 directional stress:

- relative L2: `1.4062432345641441e-11`
- FP32 relative L2: `0.0004602091299069074`
- improvement vs FP32: `32726140.015851967`x
- gate pass: **True**

`DD32_PARITY_SMOKE.json` SHA-256: `a40691e96d521154b2f11de06dcb90b4d05aafbf474ce1e75e9ac313319ad3db`; overall pass: **True**.

## Precision authority

- Python/NumPy FP64: reference/oracle.
- C++/OpenMP FP64: `CERTIFICATION`.
- SYCL DD32 / FP32x2: `SCREENING_ONLY` high-precision GPU lane; not IEEE FP64.
- SYCL FP32: `SCREENING_ONLY`.

## Framework semantics retained

- create-once protocol freeze and commitments;
- gate DAG / fail-closed execution;
- strict requested-vs-actual backend authority;
- source/provenance manifests;
- HMAC opaque IDs and nonced reveal commitments;
- automatic LaTeX report rendering/publishing to `<version-folder>_FALSIFIER_REPORT.pdf`;
- G5 separation of synthetic-control replication from independent cross-source replication;
- deterministic output packaging and release contamination checks.

## Canonical policy

Use v1.0.4 for all **new** falsifiers. Historical falsifier releases remain pinned to their original template/framework for reproducibility. Do not edit v1.0.4 in place; increment the framework version for every future change.
