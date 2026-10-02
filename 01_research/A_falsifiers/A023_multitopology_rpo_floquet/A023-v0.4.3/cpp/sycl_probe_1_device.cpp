#include <pybind11/pybind11.h>
#include <sycl/sycl.hpp>
namespace py = pybind11;
PYBIND11_MODULE(_sst_sycl_probe1,m){
  m.def("device",[](){ sycl::device d(sycl::gpu_selector_v); py::dict r; r["name"]=d.get_info<sycl::info::device::name>(); r["is_gpu"]=d.is_gpu(); r["fp64"]=d.has(sycl::aspect::fp64); return r; });
}
