#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "core.hpp"
#include <cstring>
namespace py=pybind11;
using sstpd::Vec3;

static std::vector<Vec3> to_vec(py::array_t<double,py::array::c_style|py::array::forcecast> a){
    auto b=a.request(); if(b.ndim!=2 || b.shape[1]!=3) throw std::runtime_error("expected Nx3 array");
    std::vector<Vec3> x((std::size_t)b.shape[0]); auto*p=(double*)b.ptr;
    for(py::ssize_t i=0;i<b.shape[0];++i)x[(std::size_t)i]={p[3*i],p[3*i+1],p[3*i+2]}; return x;
}
static py::array_t<double> from_vec(const std::vector<Vec3>&x){
    py::array_t<double> out({(py::ssize_t)x.size(),(py::ssize_t)3}); auto b=out.request(); auto*p=(double*)b.ptr;
    for(std::size_t i=0;i<x.size();++i){p[3*i]=x[i][0];p[3*i+1]=x[i][1];p[3*i+2]=x[i][2];} return out;
}
PYBIND11_MODULE(sst_phase_delay_native,m){
    m.attr("BACKEND")="cpp";
    m.def("biot_savart_velocity",[](py::array_t<double> a,double g,double c){return from_vec(sstpd::biot_savart_velocity(to_vec(a),g,c));},py::arg("points"),py::arg("gamma"),py::arg("core"));
    m.def("min_nonadjacent_segment_distance",[](py::array_t<double>a,int ex){return sstpd::min_nonadjacent_segment_distance(to_vec(a),ex);},py::arg("points"),py::arg("exclusion")=2);
    m.def("rk4_step",[](py::array_t<double>a,double dt,double g,double c){return from_vec(sstpd::rk4_step(to_vec(a),dt,g,c));});
    m.def("evolve_pair",[](py::array_t<double>a,py::array_t<double>b,int steps,double dt,double g,double c,int sample_every){
        auto av=to_vec(a); auto bv=to_vec(b);
        py::gil_scoped_release release;
        auto r=sstpd::evolve_pair(av,bv,steps,dt,g,c,sample_every);
        py::gil_scoped_acquire acquire;
        const py::ssize_t ns=(py::ssize_t)r.times.size(), n=(py::ssize_t)r.n;
        py::array_t<double> times({ns}); std::memcpy(times.mutable_data(),r.times.data(),r.times.size()*sizeof(double));
        py::array_t<double> ah({ns,n,(py::ssize_t)3}), bh({ns,n,(py::ssize_t)3});
        std::memcpy(ah.mutable_data(),r.a_hist.data(),r.a_hist.size()*sizeof(double)); std::memcpy(bh.mutable_data(),r.b_hist.data(),r.b_hist.size()*sizeof(double));
        py::dict d; d["times"]=times; d["a"]=ah; d["b"]=bh; d["final_gap_a"]=r.final_gap_a; d["final_gap_b"]=r.final_gap_b; return d;
    },py::arg("a"),py::arg("b"),py::arg("steps"),py::arg("dt"),py::arg("gamma"),py::arg("core"),py::arg("sample_every"));
}
