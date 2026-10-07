#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;

py::array_t<double> induced_velocity(
    py::array_t<double, py::array::c_style | py::array::forcecast> targets,
    py::array_t<double, py::array::c_style | py::array::forcecast> mids,
    py::array_t<double, py::array::c_style | py::array::forcecast> dls,
    py::array_t<double, py::array::c_style | py::array::forcecast> gammas,
    double core) {
  auto T=targets.unchecked<2>(); auto M=mids.unchecked<2>(); auto D=dls.unchecked<2>(); auto G=gammas.unchecked<1>();
  if(T.shape(1)!=3 || M.shape(1)!=3 || D.shape(1)!=3 || M.shape(0)!=D.shape(0) || M.shape(0)!=G.shape(0))
    throw std::runtime_error("shape mismatch");
  py::array_t<double> out({T.shape(0), (py::ssize_t)3}); auto O=out.mutable_unchecked<2>();
  const double inv4pi=1.0/(4.0*3.141592653589793238462643383279502884), a2=core*core;
  #pragma omp parallel for if(T.shape(0)>32)
  for(py::ssize_t i=0;i<T.shape(0);++i){
    double ux=0,uy=0,uz=0;
    for(py::ssize_t j=0;j<M.shape(0);++j){
      const double rx=T(i,0)-M(j,0), ry=T(i,1)-M(j,1), rz=T(i,2)-M(j,2);
      const double cx=D(j,1)*rz-D(j,2)*ry;
      const double cy=D(j,2)*rx-D(j,0)*rz;
      const double cz=D(j,0)*ry-D(j,1)*rx;
      const double den=std::pow(rx*rx+ry*ry+rz*rz+a2,1.5);
      const double f=G(j)/den; ux+=f*cx; uy+=f*cy; uz+=f*cz;
    }
    O(i,0)=inv4pi*ux; O(i,1)=inv4pi*uy; O(i,2)=inv4pi*uz;
  }
  return out;
}

PYBIND11_MODULE(_native,m){
  m.doc()="A054 target-blind regularized Biot-Savart kernel";
  m.def("induced_velocity",&induced_velocity,py::arg("targets"),py::arg("mids"),py::arg("dls"),py::arg("gammas"),py::arg("core"));
#ifdef _OPENMP
  m.attr("openmp_enabled")=true;
#else
  m.attr("openmp_enabled")=false;
#endif
}
