#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <stdexcept>

namespace py = pybind11;
using index_t = py::ssize_t;

namespace {
constexpr double kPi = 3.141592653589793238462643383279502884;
}

static void inverse3(const double F[3][3], double inv[3][3], double &det) {
    det =
        F[0][0]*(F[1][1]*F[2][2]-F[1][2]*F[2][1]) -
        F[0][1]*(F[1][0]*F[2][2]-F[1][2]*F[2][0]) +
        F[0][2]*(F[1][0]*F[2][1]-F[1][1]*F[2][0]);
    if (std::abs(det) < 1e-15) throw std::runtime_error("singular deformation");
    const double id = 1.0/det;
    inv[0][0] =  (F[1][1]*F[2][2]-F[1][2]*F[2][1])*id;
    inv[0][1] = -(F[0][1]*F[2][2]-F[0][2]*F[2][1])*id;
    inv[0][2] =  (F[0][1]*F[1][2]-F[0][2]*F[1][1])*id;
    inv[1][0] = -(F[1][0]*F[2][2]-F[1][2]*F[2][0])*id;
    inv[1][1] =  (F[0][0]*F[2][2]-F[0][2]*F[2][0])*id;
    inv[1][2] = -(F[0][0]*F[1][2]-F[0][2]*F[1][0])*id;
    inv[2][0] =  (F[1][0]*F[2][1]-F[1][1]*F[2][0])*id;
    inv[2][1] = -(F[0][0]*F[2][1]-F[0][1]*F[2][0])*id;
    inv[2][2] =  (F[0][0]*F[1][1]-F[0][1]*F[1][0])*id;
}

double energy_ratio_general(
    py::array_t<double, py::array::c_style | py::array::forcecast> nvec,
    py::array_t<double, py::array::c_style | py::array::forcecast> omega,
    py::array_t<double, py::array::c_style | py::array::forcecast> deformation
) {
    auto N = nvec.unchecked<2>(); auto W = omega.unchecked<2>(); auto Fv = deformation.unchecked<2>();
    if (N.shape(1)!=3 || W.shape(1)!=3 || N.shape(0)!=W.shape(0)) throw std::runtime_error("nvec and omega must have shape (N,3)");
    if (Fv.shape(0)!=3 || Fv.shape(1)!=3) throw std::runtime_error("deformation must have shape (3,3)");
    double F[3][3]; for(int i=0;i<3;++i) for(int j=0;j<3;++j) F[i][j]=Fv(i,j);
    double Finv[3][3], det; inverse3(F,Finv,det);
    if (std::abs(det-1.0)>1e-10) throw std::runtime_error("deformation must be volume preserving");
    const index_t count=N.shape(0); double sum=0.0;
#ifdef _OPENMP
#pragma omp parallel for reduction(+:sum)
#endif
    for(index_t q=0;q<count;++q){
        double wp[3]={0,0,0},kp[3]={0,0,0};
        for(int i=0;i<3;++i) for(int j=0;j<3;++j){wp[i]+=F[i][j]*W(q,j); kp[i]+=Finv[j][i]*N(q,j);}
        double num=0,den=0; for(int i=0;i<3;++i){num+=wp[i]*wp[i];den+=kp[i]*kp[i];} sum+=num/den;
    }
    return sum/static_cast<double>(count);
}

py::array_t<double> cross_product(
    py::array_t<double, py::array::c_style | py::array::forcecast> a,
    py::array_t<double, py::array::c_style | py::array::forcecast> b
){
    auto A=a.unchecked<2>(); auto B=b.unchecked<2>();
    if(A.shape(1)!=3||B.shape(1)!=3||A.shape(0)!=B.shape(0)) throw std::runtime_error("a and b must have shape (N,3)");
    py::array_t<double> out({A.shape(0),index_t(3)}); auto O=out.mutable_unchecked<2>(); const index_t count=A.shape(0);
#ifdef _OPENMP
#pragma omp parallel for
#endif
    for(index_t q=0;q<count;++q){
        O(q,0)=A(q,1)*B(q,2)-A(q,2)*B(q,1);
        O(q,1)=A(q,2)*B(q,0)-A(q,0)*B(q,2);
        O(q,2)=A(q,0)*B(q,1)-A(q,1)*B(q,0);
    }
    return out;
}

double filament_energy(
    py::array_t<double, py::array::c_style | py::array::forcecast> points,
    py::array_t<double, py::array::c_style | py::array::forcecast> circulations,
    double core_radius
){
    auto P=points.unchecked<3>(); auto G=circulations.unchecked<1>();
    const index_t L=P.shape(0), N=P.shape(1);
    if(P.shape(2)!=3 || G.shape(0)!=L) throw std::runtime_error("points must be (L,N,3) and circulations (L)");
    if(core_radius<=0.0) throw std::runtime_error("core_radius must be positive");
    const index_t S=L*N; double sum=0.0;
#ifdef _OPENMP
#pragma omp parallel for reduction(+:sum) schedule(static)
#endif
    for(index_t si=0; si<S; ++si){
        const index_t li=si/N, ii=si%N, in=(ii+1)%N;
        double mi[3], di[3];
        for(int c=0;c<3;++c){di[c]=P(li,in,c)-P(li,ii,c); mi[c]=0.5*(P(li,in,c)+P(li,ii,c));}
        for(index_t sj=0; sj<S; ++sj){
            const index_t lj=sj/N, jj=sj%N, jn=(jj+1)%N;
            double mj[3], dj[3];
            for(int c=0;c<3;++c){dj[c]=P(lj,jn,c)-P(lj,jj,c); mj[c]=0.5*(P(lj,jn,c)+P(lj,jj,c));}
            double dot=0.0,r2=core_radius*core_radius;
            for(int c=0;c<3;++c){dot+=di[c]*dj[c]; const double d=mi[c]-mj[c]; r2+=d*d;}
            sum += G(li)*G(lj)*dot/std::sqrt(r2);
        }
    }
    return sum/(8.0*kPi);
}

PYBIND11_MODULE(vortex_shear_native,m){
    m.doc()="C++17/OpenMP Euler-vorticity and regularized filament kernels for A049 v0.4.1";
    m.def("energy_ratio_general",&energy_ratio_general);
    m.def("cross_product",&cross_product);
    m.def("filament_energy",&filament_energy);
}
