# Optional SYCL GPU screening template

PKLSA generation itself does **not** require a GPU. The 2352-carrier dynamics campaign can benefit strongly from GPU screening because regularized Biot–Savart is all-pairs, O(N^2).

This folder is an integration template, not part of atlas validity. `sycl_biot_screen.cpp` performs a device smoke-test and a regularized all-pairs filament-velocity pass for one closed component. For scientific use, keep CPU C++/pybind11 as the reference backend and require CPU↔GPU parity on finalists. Record device name, compiler, backend, precision, kernel hash and launch parameters in every campaign output.

Intel Arc: build with a oneAPI/DPC++ compiler, e.g. `icx /std:c++17 /EHsc /fsycl sycl_biot_screen.cpp /Fe:sycl_biot_screen.exe` on Windows or `icpx -O3 -fsycl -std=c++17 sycl_biot_screen.cpp -o sycl_biot_screen`.
