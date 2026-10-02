#include <pybind11/pybind11.h>
#include <sycl/sycl.hpp>
namespace py = pybind11;
class SstProbeFloatKernel;
PYBIND11_MODULE(_sst_sycl_probe2,m){
  m.def("run",[](){ sycl::queue q(sycl::gpu_selector_v); float x=0; {sycl::buffer<float,1>b(&x,sycl::range<1>(1)); q.submit([&](sycl::handler&h){auto a=b.get_access<sycl::access_mode::write>(h);h.single_task<SstProbeFloatKernel>([=](){a[0]=42.0f;});}); q.wait();} return x; });
}
