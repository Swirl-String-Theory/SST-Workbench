# Canonical freeze — SST Falsifier Framework v1.0.9

Date: 2026-10-17  
Source status: **CANONICAL_FROZEN**  
Target hardware status: **WINDOWS_ARC_A770_PARITY_PENDING** (not claimed from local Linux tests).

v1.0.9 derives directly from the manifest-verified v1.0.8 `LOCAL_VALIDATED_CANDIDATE`, with v1.0.7 preserved as the unchanged historical canonical ancestor. Its distinctive v1.0.8 run-scoped non-overwriting output publication is not removed or regressed. Scientific gates, numerical thresholds, solver cores, C++/SYCL/DD32 kernels and scientific interpretation contracts remain unchanged.

Only the new v1.0.9 source tree is frozen. Do not patch it in place: subsequent changes require v1.0.10 or another versioned successor. Preserve older framework versions and historical instance pins. Perform `run_all.cmd ALL` on the user's Windows machine before relying on v1.0.9 native-backend certification there.

Release checksum: see separate `SST_Falsifier_Framework_v1.0.9.zip.sha256` outside the ZIP. A ZIP cannot include its own digest without a circular dependency.
