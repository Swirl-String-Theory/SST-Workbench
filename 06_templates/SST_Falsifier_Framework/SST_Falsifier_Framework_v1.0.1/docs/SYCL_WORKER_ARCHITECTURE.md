# External SYCL worker v2

Device kernels remain outside CPython. The host `.pyd` is C++/OpenMP only; Intel Arc screening uses a standalone DPC++ worker.

Protocol v2 adds:

- explicit protocol version and request ID;
- maximum interaction work guard `N*M <= 250,000,000`;
- finite/core validation;
- device event profiling (`kernel_device_ms`) separate from IPC-inclusive `end_to_end_ms`;
- explicit dtype code and FP32/FP64 authority labelling;
- build fingerprint over source/compiler/flags/protocol version.

On Arc without native FP64, set `SST_SYCL_ALLOW_FP32=1` only for a preregistered screening lane. CPU FP64 remains certification authority unless a falsifier explicitly registers and validates another rule.
