#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <complex>
#include <cmath>
#include <vector>
#include <array>
#include <stdexcept>
#include <algorithm>
#include <numeric>
#include <limits>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
using cdouble = std::complex<double>;
constexpr double PI = 3.141592653589793238462643383279502884;

static std::vector<py::ssize_t> prefix_shape(const py::buffer_info& info, py::ssize_t last_expected) {
    if (info.ndim < 2 || info.shape.back() != last_expected) {
        throw std::invalid_argument("array has unexpected final dimension");
    }
    return std::vector<py::ssize_t>(info.shape.begin(), info.shape.end() - 1);
}

static std::vector<py::ssize_t> append_shape(std::vector<py::ssize_t> shape, py::ssize_t x) {
    shape.push_back(x);
    return shape;
}

static inline double clampd(double x, double lo, double hi) {
    return std::max(lo, std::min(hi, x));
}

static inline std::array<double,3> cross3(const std::array<double,3>& a, const std::array<double,3>& b) {
    return {a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]};
}
static inline double dot3(const std::array<double,3>& a, const std::array<double,3>& b) {
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
}
static inline double norm3(const std::array<double,3>& a) { return std::sqrt(dot3(a,a)); }
static inline std::array<double,3> sub3(const std::array<double,3>& a, const std::array<double,3>& b) {
    return {a[0]-b[0], a[1]-b[1], a[2]-b[2]};
}
static inline std::array<double,3> add3(const std::array<double,3>& a, const std::array<double,3>& b) {
    return {a[0]+b[0], a[1]+b[1], a[2]+b[2]};
}
static inline std::array<double,3> mul3(const std::array<double,3>& a, double s) {
    return {a[0]*s,a[1]*s,a[2]*s};
}
static inline std::array<double,3> normalized3(const std::array<double,3>& a) {
    double n = norm3(a); if (!(n>0)) throw std::invalid_argument("zero vector"); return mul3(a,1.0/n);
}

py::tuple normalize_spinor(py::array_t<cdouble, py::array::c_style | py::array::forcecast> phi, double epsilon) {
    auto in = phi.request();
    auto shp = prefix_shape(in, 2);
    const auto count = static_cast<std::size_t>(in.size / 2);
    py::array_t<cdouble> psi(in.shape);
    py::array_t<double> norm2(shp);
    py::array_t<bool> defects(shp);
    const cdouble* src = static_cast<const cdouble*>(in.ptr);
    cdouble* dst = static_cast<cdouble*>(psi.request().ptr);
    double* nout = static_cast<double*>(norm2.request().ptr);
    bool* dout = static_cast<bool*>(defects.request().ptr);
    {
        py::gil_scoped_release release;
        #pragma omp parallel for schedule(static)
        for (long long ii=0; ii<static_cast<long long>(count); ++ii) {
            std::size_t i=static_cast<std::size_t>(ii);
            double n = std::norm(src[2*i]) + std::norm(src[2*i+1]);
            bool defect = !(n > epsilon) || !std::isfinite(n);
            nout[i]=n; dout[i]=defect;
            if (defect) { dst[2*i]=cdouble(0,0); dst[2*i+1]=cdouble(0,0); }
            else { double s=1.0/std::sqrt(n); dst[2*i]=src[2*i]*s; dst[2*i+1]=src[2*i+1]*s; }
        }
    }
    return py::make_tuple(psi,norm2,defects);
}

py::array_t<double> hopf_map(py::array_t<cdouble, py::array::c_style | py::array::forcecast> psi) {
    auto in=psi.request();
    auto shp=prefix_shape(in,2);
    const auto count=static_cast<std::size_t>(in.size/2);
    py::array_t<double> out(append_shape(shp,3));
    const cdouble* p=static_cast<const cdouble*>(in.ptr);
    double* q=static_cast<double*>(out.request().ptr);
    {
        py::gil_scoped_release release;
        #pragma omp parallel for schedule(static)
        for(long long ii=0; ii<static_cast<long long>(count); ++ii){
            std::size_t i=static_cast<std::size_t>(ii);
            cdouble z=std::conj(p[2*i])*p[2*i+1];
            q[3*i]=2.0*z.real(); q[3*i+1]=2.0*z.imag(); q[3*i+2]=std::norm(p[2*i])-std::norm(p[2*i+1]);
        }
    }
    return out;
}

double spinor_norm_residual(py::array_t<cdouble, py::array::c_style | py::array::forcecast> psi) {
    auto in=psi.request(); prefix_shape(in,2);
    const cdouble* p=static_cast<const cdouble*>(in.ptr); std::size_t count=static_cast<std::size_t>(in.size/2);
    double mx=0.0;
    {
        py::gil_scoped_release release;
        #pragma omp parallel for reduction(max:mx)
        for(long long ii=0; ii<static_cast<long long>(count); ++ii){ std::size_t i=ii; double r=std::abs(std::norm(p[2*i])+std::norm(p[2*i+1])-1.0); if(r>mx) mx=r; }
    }
    return mx;
}

double director_norm_residual(py::array_t<double, py::array::c_style | py::array::forcecast> n) {
    auto in=n.request(); prefix_shape(in,3);
    const double* p=static_cast<const double*>(in.ptr); std::size_t count=static_cast<std::size_t>(in.size/3);
    double mx=0.0;
    {
        py::gil_scoped_release release;
        #pragma omp parallel for reduction(max:mx)
        for(long long ii=0; ii<static_cast<long long>(count); ++ii){ std::size_t i=ii; double s=p[3*i]*p[3*i]+p[3*i+1]*p[3*i+1]+p[3*i+2]*p[3*i+2]; double r=std::abs(s-1.0); if(r>mx) mx=r; }
    }
    return mx;
}

py::array_t<cdouble> analytic_hopf_spinor(
    py::array_t<double, py::array::c_style | py::array::forcecast> x,
    py::array_t<double, py::array::c_style | py::array::forcecast> y,
    py::array_t<double, py::array::c_style | py::array::forcecast> z,
    double scale) {
    if (!(scale>0) || !std::isfinite(scale)) throw std::invalid_argument("scale must be finite and >0");
    auto ix=x.request(), iy=y.request(), iz=z.request();
    if(ix.shape!=iy.shape || ix.shape!=iz.shape) throw std::invalid_argument("x/y/z shapes differ");
    auto shape=std::vector<py::ssize_t>(ix.shape.begin(),ix.shape.end()); shape.push_back(2);
    py::array_t<cdouble> out(shape);
    const double *px=(double*)ix.ptr,*pyy=(double*)iy.ptr,*pz=(double*)iz.ptr; cdouble* q=(cdouble*)out.request().ptr;
    std::size_t count=static_cast<std::size_t>(ix.size);
    {
        py::gil_scoped_release release;
        #pragma omp parallel for schedule(static)
        for(long long ii=0;ii<static_cast<long long>(count);++ii){ std::size_t i=ii; double xs=px[i]/scale,ys=pyy[i]/scale,zs=pz[i]/scale; double r2=xs*xs+ys*ys+zs*zs, den=1.0+r2; q[2*i]=cdouble(2*xs/den,2*ys/den); q[2*i+1]=cdouble(2*zs/den,(r2-1.0)/den); }
    }
    return out;
}

static inline std::size_t idx4(std::size_t i,std::size_t j,std::size_t k,std::size_t c,std::size_t ny,std::size_t nz,std::size_t nc){ return (((i*ny+j)*nz+k)*nc+c); }

static inline cdouble deriv_c(const cdouble* p,std::size_t i,std::size_t j,std::size_t k,std::size_t c,int axis,std::size_t nx,std::size_t ny,std::size_t nz,double h){
    auto at=[&](std::size_t a,std::size_t b,std::size_t d){return p[idx4(a,b,d,c,ny,nz,2)];};
    if(axis==0){ if(i==0) return (-3.0*at(0,j,k)+4.0*at(1,j,k)-at(2,j,k))/(2*h); if(i+1==nx) return (3.0*at(nx-1,j,k)-4.0*at(nx-2,j,k)+at(nx-3,j,k))/(2*h); return (at(i+1,j,k)-at(i-1,j,k))/(2*h); }
    if(axis==1){ if(j==0) return (-3.0*at(i,0,k)+4.0*at(i,1,k)-at(i,2,k))/(2*h); if(j+1==ny) return (3.0*at(i,ny-1,k)-4.0*at(i,ny-2,k)+at(i,ny-3,k))/(2*h); return (at(i,j+1,k)-at(i,j-1,k))/(2*h); }
    if(k==0) return (-3.0*at(i,j,0)+4.0*at(i,j,1)-at(i,j,2))/(2*h); if(k+1==nz) return (3.0*at(i,j,nz-1)-4.0*at(i,j,nz-2)+at(i,j,nz-3))/(2*h); return (at(i,j,k+1)-at(i,j,k-1))/(2*h);
}

static inline double deriv_v(const double* p,std::size_t i,std::size_t j,std::size_t k,std::size_t c,int axis,std::size_t nx,std::size_t ny,std::size_t nz,double h){
    auto at=[&](std::size_t a,std::size_t b,std::size_t d){return p[idx4(a,b,d,c,ny,nz,3)];};
    if(axis==0){ if(i==0) return (-3*at(0,j,k)+4*at(1,j,k)-at(2,j,k))/(2*h); if(i+1==nx) return (3*at(nx-1,j,k)-4*at(nx-2,j,k)+at(nx-3,j,k))/(2*h); return (at(i+1,j,k)-at(i-1,j,k))/(2*h); }
    if(axis==1){ if(j==0) return (-3*at(i,0,k)+4*at(i,1,k)-at(i,2,k))/(2*h); if(j+1==ny) return (3*at(i,ny-1,k)-4*at(i,ny-2,k)+at(i,ny-3,k))/(2*h); return (at(i,j+1,k)-at(i,j-1,k))/(2*h); }
    if(k==0) return (-3*at(i,j,0)+4*at(i,j,1)-at(i,j,2))/(2*h); if(k+1==nz) return (3*at(i,j,nz-1)-4*at(i,j,nz-2)+at(i,j,nz-3))/(2*h); return (at(i,j,k+1)-at(i,j,k-1))/(2*h);
}

static inline double deriv_v4(const double* p,std::size_t i,std::size_t j,std::size_t k,std::size_t c,int axis,std::size_t nx,std::size_t ny,std::size_t nz,double h){
    auto at=[&](std::size_t a,std::size_t b,std::size_t d){return p[idx4(a,b,d,c,ny,nz,3)];};
    if(axis==0 && nx>=5 && i>=2 && i+2<nx) return (-at(i+2,j,k)+8.0*at(i+1,j,k)-8.0*at(i-1,j,k)+at(i-2,j,k))/(12.0*h);
    if(axis==1 && ny>=5 && j>=2 && j+2<ny) return (-at(i,j+2,k)+8.0*at(i,j+1,k)-8.0*at(i,j-1,k)+at(i,j-2,k))/(12.0*h);
    if(axis==2 && nz>=5 && k>=2 && k+2<nz) return (-at(i,j,k+2)+8.0*at(i,j,k+1)-8.0*at(i,j,k-1)+at(i,j,k-2))/(12.0*h);
    return deriv_v(p,i,j,k,c,axis,nx,ny,nz,h);
}

py::array_t<double> connection_from_spinor(py::array_t<cdouble, py::array::c_style | py::array::forcecast> psi,double h){
    if(!(h>0)) throw std::invalid_argument("spacing must be >0"); auto in=psi.request(); if(in.ndim!=4||in.shape[3]!=2) throw std::invalid_argument("psi must shape (nx,ny,nz,2)");
    std::size_t nx=in.shape[0],ny=in.shape[1],nz=in.shape[2]; if(nx<3||ny<3||nz<3) throw std::invalid_argument("grid dimensions must be >=3");
    py::array_t<double> out(std::vector<py::ssize_t>{static_cast<py::ssize_t>(nx), static_cast<py::ssize_t>(ny), static_cast<py::ssize_t>(nz), py::ssize_t{3}}); const cdouble* p=(cdouble*)in.ptr; double* q=(double*)out.request().ptr;
    {
        py::gil_scoped_release release;
        const long long total = static_cast<long long>(nx * ny * nz);
        #pragma omp parallel for schedule(static)
        for(long long flat=0; flat<total; ++flat){
            const std::size_t u=static_cast<std::size_t>(flat);
            const std::size_t k=u%nz, tmp=u/nz, j=tmp%ny, i=tmp/ny;
            const std::size_t base=idx4(i,j,k,0,ny,nz,2), obase=idx4(i,j,k,0,ny,nz,3);
            for(int a=0;a<3;++a){ cdouble d0=deriv_c(p,i,j,k,0,a,nx,ny,nz,h),d1=deriv_c(p,i,j,k,1,a,nx,ny,nz,h); cdouble z=std::conj(p[base])*d0+std::conj(p[base+1])*d1; q[obase+a]=z.imag(); }
        }
    }
    return out;
}

py::array_t<double> curl_field(py::array_t<double, py::array::c_style | py::array::forcecast> field,double h){
    auto in=field.request(); if(in.ndim!=4||in.shape[3]!=3) throw std::invalid_argument("field must shape (nx,ny,nz,3)"); std::size_t nx=in.shape[0],ny=in.shape[1],nz=in.shape[2]; if(nx<3||ny<3||nz<3) throw std::invalid_argument("grid dimensions must be >=3");
    py::array_t<double> out(in.shape); const double* p=(double*)in.ptr; double* q=(double*)out.request().ptr;
    {
        py::gil_scoped_release release;
        const long long total = static_cast<long long>(nx * ny * nz);
        #pragma omp parallel for schedule(static)
        for(long long flat=0; flat<total; ++flat){
            const std::size_t u=static_cast<std::size_t>(flat);
            const std::size_t k=u%nz, tmp=u/nz, j=tmp%ny, i=tmp/ny, b=idx4(i,j,k,0,ny,nz,3);
            q[b]=deriv_v(p,i,j,k,2,1,nx,ny,nz,h)-deriv_v(p,i,j,k,1,2,nx,ny,nz,h);
            q[b+1]=deriv_v(p,i,j,k,0,2,nx,ny,nz,h)-deriv_v(p,i,j,k,2,0,nx,ny,nz,h);
            q[b+2]=deriv_v(p,i,j,k,1,0,nx,ny,nz,h)-deriv_v(p,i,j,k,0,1,nx,ny,nz,h);
        }
    }
    return out;
}

py::array_t<double> divergence_field(py::array_t<double, py::array::c_style | py::array::forcecast> field,double h){
    auto in=field.request();
    if(in.ndim!=4||in.shape[3]!=3) throw std::invalid_argument("field must shape (nx,ny,nz,3)");
    std::size_t nx=in.shape[0],ny=in.shape[1],nz=in.shape[2];
    py::array_t<double> out(std::vector<py::ssize_t>{static_cast<py::ssize_t>(nx), static_cast<py::ssize_t>(ny), static_cast<py::ssize_t>(nz)});
    const double* p=(double*)in.ptr; double* q=(double*)out.request().ptr;
    {
        py::gil_scoped_release release;
        const long long total = static_cast<long long>(nx * ny * nz);
        #pragma omp parallel for schedule(static)
        for(long long flat=0; flat<total; ++flat){
            const std::size_t idx=static_cast<std::size_t>(flat);
            const std::size_t k=idx%nz, tmp=idx/nz, j=tmp%ny, i=tmp/ny;
            q[idx]=deriv_v(p,i,j,k,0,0,nx,ny,nz,h)+deriv_v(p,i,j,k,1,1,nx,ny,nz,h)+deriv_v(p,i,j,k,2,2,nx,ny,nz,h);
        }
    }
    return out;
}

py::array_t<double> director_curvature_b(py::array_t<double, py::array::c_style | py::array::forcecast> nf,double h){
    auto in=nf.request();
    if(in.ndim!=4||in.shape[3]!=3) throw std::invalid_argument("director must shape (nx,ny,nz,3)");
    std::size_t nx=in.shape[0],ny=in.shape[1],nz=in.shape[2];
    py::array_t<double> out(in.shape);
    const double* p=(double*)in.ptr; double* q=(double*)out.request().ptr;
    {
        py::gil_scoped_release release;
        const long long total = static_cast<long long>(nx * ny * nz);
        #pragma omp parallel for schedule(static)
        for(long long flat=0; flat<total; ++flat){
            const std::size_t u=static_cast<std::size_t>(flat);
            const std::size_t k=u%nz, tmp=u/nz, j=tmp%ny, i=tmp/ny, b=idx4(i,j,k,0,ny,nz,3);
            std::array<double,3> n={p[b],p[b+1],p[b+2]}, d[3];
            for(int a=0;a<3;++a)
                d[a]={deriv_v(p,i,j,k,0,a,nx,ny,nz,h),deriv_v(p,i,j,k,1,a,nx,ny,nz,h),deriv_v(p,i,j,k,2,a,nx,ny,nz,h)};
            q[b]=0.5*dot3(n,cross3(d[1],d[2]));
            q[b+1]=0.5*dot3(n,cross3(d[2],d[0]));
            q[b+2]=0.5*dot3(n,cross3(d[0],d[1]));
        }
    }
    return out;
}

py::array_t<double> director_curvature_b_fourth_order(py::array_t<double, py::array::c_style | py::array::forcecast> nf,double h){
    auto in=nf.request();
    if(in.ndim!=4||in.shape[3]!=3) throw std::invalid_argument("director must shape (nx,ny,nz,3)");
    std::size_t nx=in.shape[0],ny=in.shape[1],nz=in.shape[2];
    py::array_t<double> out(in.shape);
    const double* p=(double*)in.ptr; double* q=(double*)out.request().ptr;
    {
        py::gil_scoped_release release;
        const long long total = static_cast<long long>(nx * ny * nz);
        #pragma omp parallel for schedule(static)
        for(long long flat=0; flat<total; ++flat){
            const std::size_t u=static_cast<std::size_t>(flat);
            const std::size_t k=u%nz, tmp=u/nz, j=tmp%ny, i=tmp/ny, b=idx4(i,j,k,0,ny,nz,3);
            std::array<double,3> n={p[b],p[b+1],p[b+2]}, d[3];
            for(int a=0;a<3;++a)
                d[a]={deriv_v4(p,i,j,k,0,a,nx,ny,nz,h),deriv_v4(p,i,j,k,1,a,nx,ny,nz,h),deriv_v4(p,i,j,k,2,a,nx,ny,nz,h)};
            q[b]=0.5*dot3(n,cross3(d[1],d[2]));
            q[b+1]=0.5*dot3(n,cross3(d[2],d[0]));
            q[b+2]=0.5*dot3(n,cross3(d[0],d[1]));
        }
    }
    return out;
}

double hopf_charge(py::array_t<double, py::array::c_style | py::array::forcecast> a,
                   py::array_t<double, py::array::c_style | py::array::forcecast> b,double h){
    auto ia=a.request(),ib=b.request();
    if(ia.shape!=ib.shape||ia.size%3) throw std::invalid_argument("a/b shape mismatch");
    const double* pa=(double*)ia.ptr; const double* pb=(double*)ib.ptr;
    std::size_t n=ia.size/3; double sum=0;
    {
        py::gil_scoped_release release;
        #pragma omp parallel for reduction(+:sum)
        for(long long ii=0;ii<(long long)n;++ii){
            std::size_t i=ii;
            sum+=pa[3*i]*pb[3*i]+pa[3*i+1]*pb[3*i+1]+pa[3*i+2]*pb[3*i+2];
        }
    }
    return sum*h*h*h/(4*PI*PI);
}

double relative_l2(py::array_t<double, py::array::c_style | py::array::forcecast> x,
                   py::array_t<double, py::array::c_style | py::array::forcecast> ref,double eps){
    auto ix=x.request(),ir=ref.request();
    const double* px=(double*)ix.ptr; const double* pr=(double*)ir.ptr;
    double a=0,b=0;
    {
        py::gil_scoped_release release;
        #pragma omp parallel for reduction(+:a)
        for(long long i=0;i<(long long)ix.size;++i) a+=px[i]*px[i];
        #pragma omp parallel for reduction(+:b)
        for(long long i=0;i<(long long)ir.size;++i) b+=pr[i]*pr[i];
    }
    return std::sqrt(a)/(std::sqrt(b)+eps);
}

py::array_t<double> torus_knot_centerline(int p,int q,int samples,double R,double r){
    if(samples<8||R<=0||r<=0) throw std::invalid_argument("invalid torus knot parameters");
    py::array_t<double> out(std::vector<py::ssize_t>{static_cast<py::ssize_t>(samples), py::ssize_t{3}}); double* o=(double*)out.request().ptr;
    {
        py::gil_scoped_release release;
        #pragma omp parallel for
        for(int i=0;i<samples;++i){
            double t=2*PI*i/samples,rad=R+r*std::cos(q*t);
            o[3*i]=rad*std::cos(p*t); o[3*i+1]=rad*std::sin(p*t); o[3*i+2]=r*std::sin(q*t);
        }
    }
    return out;
}

static std::vector<std::array<double,3>> array_to_curve(py::array_t<double,py::array::c_style|py::array::forcecast> arr){
    auto in=arr.request();
    if(in.ndim!=2||in.shape[1]!=3) throw std::invalid_argument("curve must shape (N,3)");
    const double*p=(double*)in.ptr; std::vector<std::array<double,3>> c(in.shape[0]);
    for(std::size_t i=0;i<c.size();++i) c[i]={p[3*i],p[3*i+1],p[3*i+2]};
    return c;
}

double gauss_linking_number(py::array_t<double,py::array::c_style|py::array::forcecast> aa,
                            py::array_t<double,py::array::c_style|py::array::forcecast> bb,double eps){
    auto a=array_to_curve(aa),b=array_to_curve(bb); std::size_t na=a.size(),nb=b.size();
    std::vector<std::array<double,3>> da(na),db(nb),ma(na),mb(nb);
    for(std::size_t i=0;i<na;++i){auto j=(i+1)%na; da[i]=sub3(a[j],a[i]); ma[i]=mul3(add3(a[i],a[j]),0.5);}
    for(std::size_t i=0;i<nb;++i){auto j=(i+1)%nb; db[i]=sub3(b[j],b[i]); mb[i]=mul3(add3(b[i],b[j]),0.5);}
    double total=0;
    {
        py::gil_scoped_release release;
        #pragma omp parallel for reduction(+:total) schedule(dynamic)
        for(long long ii=0;ii<(long long)na;++ii){
            double local=0;
            for(std::size_t j=0;j<nb;++j){
                auto d=sub3(ma[ii],mb[j]); double rr=norm3(d);
                if(rr>eps) local+=dot3(cross3(da[ii],db[j]),d)/(rr*rr*rr);
            }
            total+=local;
        }
    }
    return total/(4*PI);
}

py::tuple bishop_frame(py::array_t<double,py::array::c_style|py::array::forcecast> curve){
    auto c=array_to_curve(curve); std::size_t n=c.size(); if(n<4) throw std::invalid_argument("curve too short");
    std::vector<std::array<double,3>> t(n),e1(n),e2(n);
    for(std::size_t i=0;i<n;++i) t[i]=normalized3(sub3(c[(i+1)%n],c[(i+n-1)%n]));
    std::array<double,3> ref={0,0,1}; if(std::abs(dot3(ref,t[0]))>0.9) ref={1,0,0};
    e1[0]=normalized3(sub3(ref,mul3(t[0],dot3(ref,t[0])))); e2[0]=cross3(t[0],e1[0]);
    for(std::size_t i=1;i<n;++i){
        auto cand=sub3(e1[i-1],mul3(t[i],dot3(e1[i-1],t[i])));
        if(norm3(cand)<1e-12) cand=sub3(e2[i-1],mul3(t[i],dot3(e2[i-1],t[i])));
        e1[i]=normalized3(cand); e2[i]=cross3(t[i],e1[i]);
    }
    auto curve_shape = std::vector<py::ssize_t>{static_cast<py::ssize_t>(n), py::ssize_t{3}};
    py::array_t<double> at(curve_shape), a1(curve_shape), a2(curve_shape);
    double*pt=(double*)at.request().ptr,*p1=(double*)a1.request().ptr,*p2=(double*)a2.request().ptr;
    for(std::size_t i=0;i<n;++i) for(int k=0;k<3;++k){pt[3*i+k]=t[i][k];p1[3*i+k]=e1[i][k];p2[3*i+k]=e2[i][k];}
    return py::make_tuple(at,a1,a2);
}

double polygonal_writhe(py::array_t<double,py::array::c_style|py::array::forcecast> curve,int excl){
    auto c=array_to_curve(curve); std::size_t n=c.size(); std::vector<std::array<double,3>> dc(n),mid(n);
    for(std::size_t i=0;i<n;++i){dc[i]=sub3(c[(i+1)%n],c[i]);mid[i]=mul3(add3(c[i],c[(i+1)%n]),0.5);}
    double total=0;
    {
        py::gil_scoped_release release;
        #pragma omp parallel for reduction(+:total) schedule(dynamic)
        for(long long ii=0;ii<(long long)n;++ii){
            double local=0;
            for(std::size_t j=ii+1;j<n;++j){
                std::size_t d=std::min<std::size_t>(j-ii,n-(j-ii)); if((int)d<=excl) continue;
                auto diff=sub3(mid[ii],mid[j]); double rr=norm3(diff);
                if(rr>1e-14) local+=dot3(cross3(dc[ii],dc[j]),diff)/(rr*rr*rr);
            }
            total+=local;
        }
    }
    return total/(2*PI);
}

double frame_twist(py::array_t<double,py::array::c_style|py::array::forcecast> tangent,
                   py::array_t<double,py::array::c_style|py::array::forcecast> e1arr){
    auto t=array_to_curve(tangent),e=array_to_curve(e1arr); if(t.size()!=e.size()) throw std::invalid_argument("shape mismatch");
    double total=0; std::size_t n=t.size();
    for(std::size_t i=0;i<n;++i){
        std::size_t j=(i+1)%n;
        auto transported=sub3(e[i],mul3(t[j],dot3(e[i],t[j]))); if(norm3(transported)<1e-14) continue;
        transported=normalized3(transported);
        auto target=normalized3(sub3(e[j],mul3(t[j],dot3(e[j],t[j]))));
        double s=dot3(t[j],cross3(transported,target)),co=clampd(dot3(transported,target),-1,1);
        total+=std::atan2(s,co);
    }
    return total/(2*PI);
}

py::array_t<cdouble> su2_rotation(py::array_t<double,py::array::c_style|py::array::forcecast> axis,double angle){
    auto in=axis.request(); if(in.size!=3) throw std::invalid_argument("axis must length 3"); const double*p=(double*)in.ptr;
    std::array<double,3>a={p[0],p[1],p[2]}; a=normalized3(a); double c=std::cos(angle/2),s=std::sin(angle/2);
    py::array_t<cdouble> out(std::vector<py::ssize_t>{py::ssize_t{2}, py::ssize_t{2}}); cdouble*o=(cdouble*)out.request().ptr;
    o[0]=cdouble(c,-s*a[2]); o[3]=cdouble(c,s*a[2]);
    o[1]=cdouble(-s*a[1],-s*a[0]); o[2]=cdouble(s*a[1],-s*a[0]);
    return out;
}

py::tuple structured_tube_spinor(py::array_t<double,py::array::c_style|py::array::forcecast> curve,
                                 py::array_t<double,py::array::c_style|py::array::forcecast> e1arr,
                                 py::array_t<double,py::array::c_style|py::array::forcecast> e2arr,
                                 int radial,int angular,double tube_radius,int m,int nw){
    auto c=array_to_curve(curve),e1=array_to_curve(e1arr),e2=array_to_curve(e2arr); std::size_t n=c.size();
    if(e1.size()!=n||e2.size()!=n||radial<2||angular<4||tube_radius<=0) throw std::invalid_argument("invalid tube args");
    py::array_t<double> pos(std::vector<py::ssize_t>{static_cast<py::ssize_t>(n), static_cast<py::ssize_t>(radial), static_cast<py::ssize_t>(angular), py::ssize_t{3}});
    py::array_t<cdouble> psi(std::vector<py::ssize_t>{static_cast<py::ssize_t>(n), static_cast<py::ssize_t>(radial), static_cast<py::ssize_t>(angular), py::ssize_t{2}});
    py::array_t<double> dir(std::vector<py::ssize_t>{static_cast<py::ssize_t>(n), static_cast<py::ssize_t>(radial), static_cast<py::ssize_t>(angular), py::ssize_t{3}});
    double*pp=(double*)pos.request().ptr; cdouble*ps=(cdouble*)psi.request().ptr; double*pd=(double*)dir.request().ptr;
    auto smooth=[](double t){t=clampd(t,0,1);return t*t*(3-2*t);};
    {
        py::gil_scoped_release release;
        const long long total = static_cast<long long>(n) * radial * angular;
        #pragma omp parallel for schedule(static)
        for(long long flat=0; flat<total; ++flat){
            const std::size_t idx=static_cast<std::size_t>(flat);
            const int k=static_cast<int>(idx % static_cast<std::size_t>(angular));
            const std::size_t tmp=idx/static_cast<std::size_t>(angular);
            const int j=static_cast<int>(tmp % static_cast<std::size_t>(radial));
            const std::size_t ii=tmp/static_cast<std::size_t>(radial);
            double r=tube_radius*j/(radial-1.0),ang=2*PI*k/angular,beta=PI*smooth(r/tube_radius),sp=2*PI*ii/n;
            for(int d=0;d<3;++d) pp[3*idx+d]=c[ii][d]+r*std::cos(ang)*e1[ii][d]+r*std::sin(ang)*e2[ii][d];
            cdouble p1=std::cos(beta/2.0)*std::exp(cdouble(0,m*sp)),p2=std::sin(beta/2.0)*std::exp(cdouble(0,nw*ang));
            ps[2*idx]=p1; ps[2*idx+1]=p2; cdouble z=std::conj(p1)*p2;
            pd[3*idx]=2*z.real(); pd[3*idx+1]=2*z.imag(); pd[3*idx+2]=std::norm(p1)-std::norm(p2);
        }
    }
    return py::make_tuple(pos,psi,dir);
}

py::dict backend_info(){
    py::dict d; d["backend"]="cpp"; d["cpp_standard"]="C++17";
#ifdef _OPENMP
    d["openmp"]=true; d["threads"]=omp_get_max_threads();
#else
    d["openmp"]=false; d["threads"]=1;
#endif
    d["version"]="0.1.3"; return d;
}

PYBIND11_MODULE(_native,m){
    m.doc()="SST Hopf Benchmark native C++17 kernels";
    m.def("backend_info",&backend_info);
    m.def("normalize_spinor",&normalize_spinor,py::arg("phi"),py::arg("epsilon")=1e-14);
    m.def("hopf_map",&hopf_map);
    m.def("spinor_norm_residual",&spinor_norm_residual);
    m.def("director_norm_residual",&director_norm_residual);
    m.def("analytic_hopf_spinor",&analytic_hopf_spinor,py::arg("x"),py::arg("y"),py::arg("z"),py::arg("scale")=1.0);
    m.def("connection_from_spinor",&connection_from_spinor);
    m.def("curl",&curl_field);
    m.def("divergence",&divergence_field);
    m.def("director_curvature_b",&director_curvature_b);
    m.def("director_curvature_b_fourth_order",&director_curvature_b_fourth_order);
    m.def("hopf_charge",&hopf_charge);
    m.def("relative_l2",&relative_l2,py::arg("numerator"),py::arg("reference"),py::arg("epsilon")=1e-15);
    m.def("gauss_linking_number",&gauss_linking_number,py::arg("curve_a"),py::arg("curve_b"),py::arg("epsilon")=1e-14);
    m.def("torus_knot_centerline",&torus_knot_centerline,py::arg("p")=2,py::arg("q")=3,py::arg("samples")=400,py::arg("major_radius")=2.0,py::arg("minor_radius")=0.7);
    m.def("bishop_frame",&bishop_frame);
    m.def("polygonal_writhe",&polygonal_writhe,py::arg("curve"),py::arg("neighbor_exclusion")=2);
    m.def("frame_twist",&frame_twist);
    m.def("su2_rotation",&su2_rotation);
    m.def("structured_tube_spinor",&structured_tube_spinor);
}
