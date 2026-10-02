#include <pybind11/pybind11.h>
#include <sycl/sycl.hpp>
namespace py = pybind11;
class SstProbeDoubleKernel;
PYBIND11_MODULE(_sst_sycl_probe3,m){
  m.def("capability",[](){ sycl::device d(sycl::gpu_selector_v); py::dict r; r["name"]=d.get_info<sycl::info::device::name>(); r["fp64"]=d.has(sycl::aspect::fp64); return r; });
  m.def("run",[](){ sycl::queue q(sycl::gpu_selector_v); auto d=q.get_device(); if(!d.has(sycl::aspect::fp64)) throw std::runtime_error("Selected GPU has no native SYCL aspect::fp64; scientific FULL double kernel refused."); double x=0; {sycl::buffer<double,1>b(&x,sycl::range<1>(1)); q.submit([&](sycl::handler&h){auto a=b.get_access<sycl::access_mode::write>(h);h.single_task<SstProbeDoubleKernel>([=](){a[0]=42.0;});}); q.wait();} return x; });
}
