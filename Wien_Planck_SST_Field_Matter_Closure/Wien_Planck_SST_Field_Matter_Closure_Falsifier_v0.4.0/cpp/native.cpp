#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>
#include <stdexcept>
namespace py = pybind11;

static inline void cross3(const double a[3], const double b[3], double o[3]) {
    o[0]=a[1]*b[2]-a[2]*b[1]; o[1]=a[2]*b[0]-a[0]*b[2]; o[2]=a[0]*b[1]-a[1]*b[0];
}

py::array_t<double> velocity(py::array_t<double, py::array::c_style|py::array::forcecast> pts,
                             py::array_t<long long, py::array::c_style|py::array::forcecast> offs,
                             double gamma, double core) {
    auto P=pts.unchecked<2>(); auto O=offs.unchecked<1>();
    if(P.shape(1)!=3) throw std::runtime_error("points must be Nx3");
    py::array_t<double> out({P.shape(0), (py::ssize_t)3}); auto V=out.mutable_unchecked<2>();
    for(py::ssize_t i=0;i<P.shape(0);++i){V(i,0)=V(i,1)=V(i,2)=0.0;}
    const double PI=3.141592653589793238462643383279502884;
    const double pref=gamma/(4.0*PI);
    for(py::ssize_t ci=0; ci+1<O.shape(0); ++ci){
        long long a=O(ci), b=O(ci+1); if(b-a<3) continue;
        for(long long j=a;j<b;++j){ long long k=(j+1<b)?j+1:a;
            double dl[3]={P(k,0)-P(j,0),P(k,1)-P(j,1),P(k,2)-P(j,2)};
            double m[3]={0.5*(P(k,0)+P(j,0)),0.5*(P(k,1)+P(j,1)),0.5*(P(k,2)+P(j,2))};
            for(py::ssize_t i=0;i<P.shape(0);++i){
                double r[3]={P(i,0)-m[0],P(i,1)-m[1],P(i,2)-m[2]}, cr[3]; cross3(dl,r,cr);
                double den=std::pow(r[0]*r[0]+r[1]*r[1]+r[2]*r[2]+core*core,1.5);
                if(den>0){ V(i,0)+=pref*cr[0]/den; V(i,1)+=pref*cr[1]/den; V(i,2)+=pref*cr[2]/den; }
            }
        }
    }
    return out;
}

double energy_sum(py::array_t<double, py::array::c_style|py::array::forcecast> pts,
                  py::array_t<long long, py::array::c_style|py::array::forcecast> offs,
                  double core) {
    auto P=pts.unchecked<2>(); auto O=offs.unchecked<1>();
    struct Seg{double m[3], dl[3];}; std::vector<Seg> s;
    for(py::ssize_t ci=0; ci+1<O.shape(0); ++ci){ long long a=O(ci),b=O(ci+1); for(long long j=a;j<b;++j){long long k=(j+1<b)?j+1:a; Seg q;
        for(int d=0;d<3;++d){q.dl[d]=P(k,d)-P(j,d); q.m[d]=0.5*(P(k,d)+P(j,d));} s.push_back(q);}}
    double sum=0.0;
    for(size_t i=0;i<s.size();++i) for(size_t j=0;j<s.size();++j){
        double dx=s[i].m[0]-s[j].m[0],dy=s[i].m[1]-s[j].m[1],dz=s[i].m[2]-s[j].m[2];
        double den=std::sqrt(dx*dx+dy*dy+dz*dz+core*core);
        double dot=s[i].dl[0]*s[j].dl[0]+s[i].dl[1]*s[j].dl[1]+s[i].dl[2]*s[j].dl[2];
        sum += dot/den;
    }
    return sum;
}

PYBIND11_MODULE(_native,m){m.doc()="SST Wien-Planck v0.2 native kernels";m.def("velocity",&velocity);m.def("energy_sum",&energy_sum);}
