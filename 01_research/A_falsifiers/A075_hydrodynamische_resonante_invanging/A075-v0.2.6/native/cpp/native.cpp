#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <stdexcept>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
using Vec=py::array_t<double, py::array::c_style | py::array::forcecast>;
Vec cross3(Vec a, Vec b){
    auto ai=a.request(),bi=b.request();
    if(ai.ndim!=4||bi.ndim!=4||ai.shape[3]!=3)throw std::invalid_argument("cross3 requires contiguous NxNxNx3 arrays");
    for(int i=0;i<4;++i)if(ai.shape[i]!=bi.shape[i])throw std::invalid_argument("shape mismatch");
    Vec out(ai.shape);
    auto ao=out.request();
    const auto *x=static_cast<const double*>(ai.ptr),*y=static_cast<const double*>(bi.ptr);
    auto *z=static_cast<double*>(ao.ptr);
    const py::ssize_t total=static_cast<py::ssize_t>(ai.size/3);
    py::gil_scoped_release release;
    #pragma omp parallel for schedule(static)
    for(py::ssize_t j=0;j<total;++j){
        const auto k=3*j;
        z[k]=x[k+1]*y[k+2]-x[k+2]*y[k+1];
        z[k+1]=x[k+2]*y[k]-x[k]*y[k+2];
        z[k+2]=x[k]*y[k+1]-x[k+1]*y[k];
    }
    return out;
}
int omp_enabled(){
#ifdef _OPENMP
return 1;
#else
return 0;
#endif
}
int omp_threads(){
#ifdef _OPENMP
return omp_get_max_threads();
#else
return 1;
#endif
}
PYBIND11_MODULE(_sst_native,m){
    m.doc()="A075 native OpenMP rotational Euler nonlinear kernel";
    m.def("cross3",&cross3);m.def("openmp_enabled",&omp_enabled);m.def("openmp_threads",&omp_threads);
}
