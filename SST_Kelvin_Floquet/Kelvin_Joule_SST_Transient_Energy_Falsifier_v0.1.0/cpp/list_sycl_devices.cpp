// Standalone SYCL device probe (not the pybind module).
// Build: icpx -fsycl -O2 cpp/list_sycl_devices.cpp -o build/list_sycl_devices
#include <sycl/sycl.hpp>
#include <iostream>

int main() {
    std::cout << "[host] SYCL platforms & devices:\n";
    for (const auto& P : sycl::platform::get_platforms()) {
        std::cout << "Platform: " << P.get_info<sycl::info::platform::name>() << "\n";
        for (const auto& D : P.get_devices()) {
            std::cout << "  - Device: " << D.get_info<sycl::info::device::name>()
                      << " | is_gpu=" << D.is_gpu()
                      << " | backend=" << static_cast<int>(D.get_backend()) << "\n";
        }
    }
    return 0;
}
