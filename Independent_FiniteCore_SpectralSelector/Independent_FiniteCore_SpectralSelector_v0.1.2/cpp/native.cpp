#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <thread>
#include <vector>

namespace py = pybind11;
constexpr double PI = 3.141592653589793238462643383279502884;

struct Vec3 {
    double x{}, y{}, z{};
    Vec3() = default;
    Vec3(double X, double Y, double Z): x(X), y(Y), z(Z) {}
    Vec3 operator+(const Vec3& o) const { return {x+o.x,y+o.y,z+o.z}; }
    Vec3 operator-(const Vec3& o) const { return {x-o.x,y-o.y,z-o.z}; }
    Vec3 operator*(double s) const { return {x*s,y*s,z*s}; }
    Vec3& operator+=(const Vec3& o) { x+=o.x; y+=o.y; z+=o.z; return *this; }
};
static inline double dot(const Vec3&a,const Vec3&b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static inline Vec3 cross(const Vec3&a,const Vec3&b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
static inline double norm2(const Vec3&a){return dot(a,a);}
static inline double norm(const Vec3&a){return std::sqrt(norm2(a));}

static std::vector<Vec3> make_ring(int n, double radius) {
    if (n < 8) throw std::runtime_error("n_nodes must be >= 8");
    if (!(radius > 1.0)) throw std::runtime_error("ring_radius_over_core must be > 1");
    std::vector<Vec3> p(n);
    for(int i=0;i<n;++i){ double t=2.0*PI*i/n; p[i]={radius*std::cos(t),radius*std::sin(t),0.0}; }
    return p;
}

static double kernel_weight(double r2, double core, int model) {
    const double a2 = core*core;
    if (model == 0) { // Rosenhead-Moore
        return 1.0/std::pow(r2+a2,1.5);
    }
    if (model == 1) { // smooth Gaussian/Lamb-Oseen-like cutoff
        const double r = std::sqrt(std::max(r2,1e-300));
        const double g = 1.0-std::exp(-r2/(2.0*a2));
        return g/(r*r*r);
    }
    if (model == 2) { // stronger algebraic core, robustness probe
        return 1.0/std::pow(r2+2.0*a2,1.5);
    }
    throw std::runtime_error("unknown core_model; use 0,1,2");
}

static std::vector<Vec3> velocity_raw(const std::vector<Vec3>& p, double core, double cell, int shell, int model, bool interaction_only=false) {
    const int n=(int)p.size();
    std::vector<Vec3> v(n);
    const double coeff=1.0/(4.0*PI); // circulation is the dimensionless unit Gamma=1
    for(int i=0;i<n;++i){
        Vec3 sum{};
        for(int ix=-shell;ix<=shell;++ix) for(int iy=-shell;iy<=shell;++iy) for(int iz=-shell;iz<=shell;++iz){
            if(interaction_only && ix==0 && iy==0 && iz==0) continue;
            Vec3 shift{cell*ix,cell*iy,cell*iz};
            for(int j=0;j<n;++j){
                const int k=(j+1)%n;
                Vec3 a=p[j]+shift, b=p[k]+shift;
                Vec3 dl=b-a;
                Vec3 mid=(a+b)*0.5;
                Vec3 r=p[i]-mid;
                double w=kernel_weight(norm2(r),core,model);
                sum += cross(dl,r)*(coeff*w);
            }
        }
        v[i]=sum;
    }
    return v;
}

static bool solve3(double A[3][3], double b[3], double x[3]) {
    double M[3][4];
    for(int i=0;i<3;++i){ for(int j=0;j<3;++j) M[i][j]=A[i][j]; M[i][3]=b[i]; }
    for(int c=0;c<3;++c){
        int piv=c; for(int r=c+1;r<3;++r) if(std::abs(M[r][c])>std::abs(M[piv][c])) piv=r;
        if(std::abs(M[piv][c])<1e-14) return false;
        if(piv!=c) for(int j=c;j<4;++j) std::swap(M[piv][j],M[c][j]);
        double d=M[c][c]; for(int j=c;j<4;++j) M[c][j]/=d;
        for(int r=0;r<3;++r) if(r!=c){ double f=M[r][c]; for(int j=c;j<4;++j) M[r][j]-=f*M[c][j]; }
    }
    for(int i=0;i<3;++i) x[i]=M[i][3];
    return true;
}

struct ShapeResult { std::vector<Vec3> shape; Vec3 U; Vec3 Omega; double raw_rms{}, shape_rms{}; };

static ShapeResult remove_rigid(const std::vector<Vec3>& p, const std::vector<Vec3>& v){
    int n=(int)p.size(); Vec3 c{}, U{};
    for(int i=0;i<n;++i){ c+=p[i]; U+=v[i]; }
    c=c*(1.0/n); U=U*(1.0/n);
    double A[3][3]={{0,0,0},{0,0,0},{0,0,0}}; double bvec[3]={0,0,0};
    double raw2=0.0;
    for(int i=0;i<n;++i){
        Vec3 r=p[i]-c, w=v[i]-U; raw2 += norm2(v[i]);
        double rr=norm2(r);
        A[0][0]+=rr-r.x*r.x; A[0][1]+=-r.x*r.y; A[0][2]+=-r.x*r.z;
        A[1][0]+=-r.y*r.x; A[1][1]+=rr-r.y*r.y; A[1][2]+=-r.y*r.z;
        A[2][0]+=-r.z*r.x; A[2][1]+=-r.z*r.y; A[2][2]+=rr-r.z*r.z;
        Vec3 cr=cross(r,w); bvec[0]+=cr.x; bvec[1]+=cr.y; bvec[2]+=cr.z;
    }
    double om[3]={0,0,0}; solve3(A,bvec,om); Vec3 O{om[0],om[1],om[2]};
    std::vector<Vec3> s(n); double sh2=0.0;
    for(int i=0;i<n;++i){ Vec3 r=p[i]-c; s[i]=v[i]-U-cross(O,r); sh2+=norm2(s[i]); }
    return {s,U,O,std::sqrt(raw2/n),std::sqrt(sh2/n)};
}

static std::vector<Vec3> shape_velocity(const std::vector<Vec3>& p,double core,double cell,int shell,int model,bool interaction_only=false){
    return remove_rigid(p,velocity_raw(p,core,cell,shell,model,interaction_only)).shape;
}

static void ring_basis(const std::vector<Vec3>& p, std::vector<Vec3>& nrm, std::vector<Vec3>& bin){
    int n=(int)p.size(); nrm.resize(n); bin.resize(n);
    for(int i=0;i<n;++i){
        double r=std::sqrt(p[i].x*p[i].x+p[i].y*p[i].y); nrm[i]={p[i].x/r,p[i].y/r,0.0}; bin[i]={0,0,1};
    }
}

static py::array_t<double> ring_normal_jacobian(int n_nodes,double radius,double cell,int shell,double fd_eps,int core_model,int threads,bool interaction_only){
    const double core=1.0; // definition of dimensionless length unit, not a physical input
    if(!(cell>2.0*(radius+core))) throw std::runtime_error("cell_over_core must exceed 2*(ring_radius_over_core+1) to avoid cell overlap");
    if(!(fd_eps>0.0 && fd_eps<0.1)) throw std::runtime_error("fd_eps_over_core must lie in (0,0.1)");
    auto base=make_ring(n_nodes,radius); std::vector<Vec3> nrm,bin; ring_basis(base,nrm,bin);
    const int d=2*n_nodes;
    py::array_t<double> arr({d,d}); auto m=arr.mutable_unchecked<2>();
    // initialize because worker threads write disjoint columns
    for(int i=0;i<d;++i) for(int j=0;j<d;++j) m(i,j)=0.0;
    std::atomic<int> next{0}; int nt=std::max(1,std::min(threads,d));
    auto worker=[&](){
        for(;;){ int col=next.fetch_add(1); if(col>=d) break; int j=col/2; bool bmode=(col%2)==1; Vec3 e=bmode?bin[j]:nrm[j];
            auto pp=base, pm=base; pp[j]+=e*fd_eps; pm[j]+=e*(-fd_eps);
            auto vp=shape_velocity(pp,core,cell,shell,core_model,interaction_only); auto vm=shape_velocity(pm,core,cell,shell,core_model,interaction_only);
            for(int i=0;i<n_nodes;++i){ Vec3 dv=(vp[i]-vm[i])*(0.5/fd_eps); m(2*i,col)=dot(dv,nrm[i]); m(2*i+1,col)=dot(dv,bin[i]); }
        }
    };
    std::vector<std::thread> pool; pool.reserve(nt); for(int t=0;t<nt;++t) pool.emplace_back(worker); for(auto& th:pool) th.join();
    return arr;
}


static void jacobian_column_values(const std::vector<Vec3>& base,const std::vector<Vec3>& nrm,const std::vector<Vec3>& bin,
                                   int col,double core,double cell,int shell,double fd_eps,int core_model,bool interaction_only,
                                   std::vector<double>& out){
    const int n=(int)base.size();
    const int j=col/2; const bool bmode=(col%2)==1; const Vec3 e=bmode?bin[j]:nrm[j];
    auto pp=base, pm=base; pp[j]+=e*fd_eps; pm[j]+=e*(-fd_eps);
    auto vp=shape_velocity(pp,core,cell,shell,core_model,interaction_only);
    auto vm=shape_velocity(pm,core,cell,shell,core_model,interaction_only);
    out.resize(2*n);
    for(int i=0;i<n;++i){
        Vec3 dv=(vp[i]-vm[i])*(0.5/fd_eps);
        out[2*i]=dot(dv,nrm[i]); out[2*i+1]=dot(dv,bin[i]);
    }
}

static py::array_t<double> ring_normal_jacobian_c4(int n_nodes,double radius,double cell,int shell,double fd_eps,int core_model,int threads,bool interaction_only){
    const double core=1.0;
    if(n_nodes%4!=0) return ring_normal_jacobian(n_nodes,radius,cell,shell,fd_eps,core_model,threads,interaction_only);
    if(!(cell>2.0*(radius+core))) throw std::runtime_error("cell_over_core must exceed 2*(ring_radius_over_core+1) to avoid cell overlap");
    if(!(fd_eps>0.0 && fd_eps<0.1)) throw std::runtime_error("fd_eps_over_core must lie in (0,0.1)");
    auto base=make_ring(n_nodes,radius); std::vector<Vec3> nrm,bin; ring_basis(base,nrm,bin);
    const int d=2*n_nodes, quarter=n_nodes/4, base_cols=2*quarter;
    py::array_t<double> arr({d,d}); auto m=arr.mutable_unchecked<2>();
    for(int i=0;i<d;++i) for(int j=0;j<d;++j) m(i,j)=0.0;
    std::atomic<int> next{0}; int nt=std::max(1,std::min(threads,base_cols));
    auto worker=[&](){
        std::vector<double> vals;
        for(;;){
            int col0=next.fetch_add(1); if(col0>=base_cols) break;
            jacobian_column_values(base,nrm,bin,col0,core,cell,shell,fd_eps,core_model,interaction_only,vals);
            const int j0=col0/2, parity=col0%2;
            for(int rot=0;rot<4;++rot){
                const int jt=(j0+rot*quarter)%n_nodes; const int col=2*jt+parity;
                for(int i=0;i<n_nodes;++i){
                    const int it=(i+rot*quarter)%n_nodes;
                    m(2*it,col)=vals[2*i]; m(2*it+1,col)=vals[2*i+1];
                }
            }
        }
    };
    std::vector<std::thread> pool; pool.reserve(nt); for(int t=0;t<nt;++t) pool.emplace_back(worker); for(auto& th:pool) th.join();
    return arr;
}

static py::dict ring_c4_symmetry_audit(int n_nodes,double radius,double cell,int shell,double fd_eps,int core_model,bool interaction_only){
    py::dict d;
    if(n_nodes%4!=0){ d["available"]=false; d["relative_error"]=1.0; d["max_abs_error"]=1.0; return d; }
    const double core=1.0; auto base=make_ring(n_nodes,radius); std::vector<Vec3> nrm,bin; ring_basis(base,nrm,bin);
    const int quarter=n_nodes/4; double diff2=0.0, ref2=0.0, maxabs=0.0;
    for(int parity=0;parity<2;++parity){
        std::vector<double> a,b;
        jacobian_column_values(base,nrm,bin,parity,core,cell,shell,fd_eps,core_model,interaction_only,a);
        jacobian_column_values(base,nrm,bin,2*quarter+parity,core,cell,shell,fd_eps,core_model,interaction_only,b);
        for(int i=0;i<n_nodes;++i){
            const int it=(i+quarter)%n_nodes;
            for(int k=0;k<2;++k){
                const double av=a[2*i+k], bv=b[2*it+k], df=av-bv;
                diff2+=df*df; ref2+=bv*bv; maxabs=std::max(maxabs,std::abs(df));
            }
        }
    }
    d["available"]=true; d["relative_error"]=std::sqrt(diff2)/std::max(std::sqrt(ref2),1e-300); d["max_abs_error"]=maxabs; return d;
}

static py::dict ring_base_metrics(int n_nodes,double radius,double cell,int shell,int core_model){
    const double core=1.0; auto p=make_ring(n_nodes,radius); auto raw=velocity_raw(p,core,cell,shell,core_model,false); auto s=remove_rigid(p,raw);
    py::dict d; d["raw_rms"]=s.raw_rms; d["shape_rms"]=s.shape_rms; d["relative_shape_residual"]=s.shape_rms/std::max(s.raw_rms,1e-300);
    d["translation"]=py::make_tuple(s.U.x,s.U.y,s.U.z); d["rotation"]=py::make_tuple(s.Omega.x,s.Omega.y,s.Omega.z); return d;
}

PYBIND11_MODULE(_native,m){
    m.doc()="Dimensionless finite-core periodic vortex-ring spectral kernel.";
    m.def("ring_normal_jacobian",&ring_normal_jacobian,py::arg("n_nodes"),py::arg("ring_radius_over_core"),py::arg("cell_over_core"),py::arg("image_shell")=1,py::arg("fd_eps_over_core")=1e-4,py::arg("core_model")=0,py::arg("threads")=1,py::arg("interaction_only")=false);
    m.def("ring_normal_jacobian_c4",&ring_normal_jacobian_c4,py::arg("n_nodes"),py::arg("ring_radius_over_core"),py::arg("cell_over_core"),py::arg("image_shell")=1,py::arg("fd_eps_over_core")=1e-4,py::arg("core_model")=0,py::arg("threads")=1,py::arg("interaction_only")=false);
    m.def("ring_c4_symmetry_audit",&ring_c4_symmetry_audit,py::arg("n_nodes"),py::arg("ring_radius_over_core"),py::arg("cell_over_core"),py::arg("image_shell")=1,py::arg("fd_eps_over_core")=1e-4,py::arg("core_model")=0,py::arg("interaction_only")=false);
    m.def("ring_base_metrics",&ring_base_metrics,py::arg("n_nodes"),py::arg("ring_radius_over_core"),py::arg("cell_over_core"),py::arg("image_shell")=1,py::arg("core_model")=0);
}
