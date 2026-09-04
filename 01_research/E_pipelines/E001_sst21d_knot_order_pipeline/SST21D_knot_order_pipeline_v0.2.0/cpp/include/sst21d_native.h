#pragma once
#include <cstddef>
#if defined(_WIN32)
  #define SST21D_API __declspec(dllexport)
#else
  #define SST21D_API __attribute__((visibility("default")))
#endif
extern "C" {
SST21D_API int sst21d_native_version();
SST21D_API double sst21d_sampled_dcsd(const double* xyz, std::size_t n, int neighbor_skip);
SST21D_API double sst21d_inter_component_min_segment_distance(const double* a, std::size_t na, const double* b, std::size_t nb);
SST21D_API void sst21d_writhe_acn_midpoint(const double* xyz, std::size_t n, int neighbor_skip, double* writhe, double* acn);
SST21D_API void sst21d_linking_acn_midpoint(const double* a, std::size_t na, const double* b, std::size_t nb, double* linking, double* acn);
}
