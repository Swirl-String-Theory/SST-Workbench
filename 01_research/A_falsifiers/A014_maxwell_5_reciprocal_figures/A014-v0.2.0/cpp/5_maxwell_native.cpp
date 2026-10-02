#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <thread>
#include <tuple>
#include <utility>
#include <vector>

namespace py = pybind11;

struct Vec3 {
    double x{}, y{}, z{};
    Vec3 operator+(const Vec3& o) const { return {x+o.x,y+o.y,z+o.z}; }
    Vec3 operator-(const Vec3& o) const { return {x-o.x,y-o.y,z-o.z}; }
    Vec3 operator*(double a) const { return {a*x,a*y,a*z}; }
    Vec3 operator/(double a) const { return {x/a,y/a,z/a}; }
    Vec3& operator+=(const Vec3& o){x+=o.x;y+=o.y;z+=o.z;return *this;}
};
static inline double dot(const Vec3&a,const Vec3&b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static inline Vec3 cross(const Vec3&a,const Vec3&b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
static inline double norm2(const Vec3&a){return dot(a,a);}
static inline double norm(const Vec3&a){return std::sqrt(norm2(a));}

struct Component {
    std::size_t start{};
    int n{};
    std::vector<double> cum;
    double length{};
};
struct SegRef {
    int comp{}, i{};
    std::size_t g0{},g1{};
    Vec3 a,b;
    double s0{}, len{}, comp_len{};
};
struct Closest { double d{}, u{}, v{}; Vec3 p,q; };
struct Contact {
    int sa{}, sb{};
    Closest c;
    double sna{}, snb{};
};
struct Kink { int comp{}, vi{}; double R{}, snorm{}; };
struct NZ { int row{}, col{}; double value{}; };

static double circumradius(const Vec3&a,const Vec3&b,const Vec3&c){
    const double A=norm(b-c), B=norm(a-c), C=norm(a-b);
    const double area2=norm(cross(b-a,c-a));
    if(area2<=1e-15*(A*B+B*C+C*A+1.0)) return std::numeric_limits<double>::infinity();
    return A*B*C/(2.0*area2);
}

static Closest segseg(const Vec3&p1,const Vec3&q1,const Vec3&p2,const Vec3&q2){
    const double EPS=1e-15;
    Vec3 d1=q1-p1, d2=q2-p2, r=p1-p2;
    const double a=dot(d1,d1), e=dot(d2,d2), f=dot(d2,r);
    double s=0,t=0;
    if(a<=EPS && e<=EPS) return {norm(p1-p2),0,0,p1,p2};
    if(a<=EPS){ s=0; t=std::clamp(f/e,0.0,1.0); }
    else {
        const double c=dot(d1,r);
        if(e<=EPS){ t=0; s=std::clamp(-c/a,0.0,1.0); }
        else {
            const double b=dot(d1,d2), denom=a*e-b*b;
            s=(denom!=0)?std::clamp((b*f-c*e)/denom,0.0,1.0):0.0;
            t=(b*s+f)/e;
            if(t<0){t=0;s=std::clamp(-c/a,0.0,1.0);} 
            else if(t>1){t=1;s=std::clamp((b-c)/a,0.0,1.0);}
        }
    }
    Vec3 cp1=p1+d1*s, cp2=p2+d2*t;
    return {norm(cp1-cp2),s,t,cp1,cp2};
}

static bool locally_adjacent_same(const SegRef&a,const SegRef&b,const std::vector<Component>& comps,double exclusion_frac){
    if(a.comp!=b.comp) return false;
    const int n=comps[a.comp].n;
    int d=std::abs(a.i-b.i); d=std::min(d,n-d);
    const int k=std::max(1,(int)std::ceil(exclusion_frac*n));
    return d<=k;
}

static std::vector<Vec3> parse_points(py::array_t<double, py::array::c_style | py::array::forcecast> arr){
    auto b=arr.request();
    if(b.ndim!=2 || b.shape[1]!=3) throw std::runtime_error("points must have shape (N,3)");
    auto r=arr.unchecked<2>();
    std::vector<Vec3> p((std::size_t)b.shape[0]);
    for(py::ssize_t i=0;i<b.shape[0];++i) p[(std::size_t)i]={r(i,0),r(i,1),r(i,2)};
    return p;
}

static std::vector<int> parse_counts(py::array_t<long long, py::array::c_style | py::array::forcecast> arr,std::size_t N){
    auto b=arr.request(); if(b.ndim!=1) throw std::runtime_error("component_counts must be 1-D");
    auto r=arr.unchecked<1>();
    std::vector<int> counts; counts.reserve((std::size_t)b.shape[0]);
    std::size_t sum=0;
    for(py::ssize_t i=0;i<b.shape[0];++i){
        long long v=r(i); if(v<4) throw std::runtime_error("each closed component needs >=4 vertices");
        counts.push_back((int)v); sum+=(std::size_t)v;
    }
    if(sum!=N) throw std::runtime_error("sum(component_counts) != number of points");
    return counts;
}

static py::dict analyze_geometry(
    py::array_t<double, py::array::c_style | py::array::forcecast> points_arr,
    py::array_t<long long, py::array::c_style | py::array::forcecast> counts_arr,
    double radius,
    double contact_tol,
    double kink_tol,
    double local_exclusion_frac,
    int threads
){
    const auto points=parse_points(points_arr);
    const auto counts=parse_counts(counts_arr,points.size());
    if(!(contact_tol>=0) || !(kink_tol>=0) || !(local_exclusion_frac>=0)) throw std::runtime_error("tolerances must be non-negative");
    threads=std::max(1,threads);

    std::vector<Component> comps;
    comps.reserve(counts.size());
    std::size_t start=0;
    for(int n:counts){
        Component c; c.start=start; c.n=n; c.cum.assign((std::size_t)n+1,0.0);
        for(int i=0;i<n;++i){
            const auto g0=start+(std::size_t)i, g1=start+(std::size_t)((i+1)%n);
            c.cum[(std::size_t)i+1]=c.cum[(std::size_t)i]+norm(points[g1]-points[g0]);
        }
        c.length=c.cum.back(); if(!(c.length>0)) throw std::runtime_error("zero component length");
        comps.push_back(std::move(c)); start+=(std::size_t)n;
    }

    std::vector<SegRef> segs; segs.reserve(points.size());
    for(int ci=0;ci<(int)comps.size();++ci){
        const auto& c=comps[(std::size_t)ci];
        for(int i=0;i<c.n;++i){
            const std::size_t g0=c.start+(std::size_t)i, g1=c.start+(std::size_t)((i+1)%c.n);
            const double L=norm(points[g1]-points[g0]);
            segs.push_back({ci,i,g0,g1,points[g0],points[g1],c.cum[(std::size_t)i],L,c.length});
        }
    }

    double minR=std::numeric_limits<double>::infinity();
    std::vector<Kink> allk; allk.reserve(points.size());
    for(int ci=0;ci<(int)comps.size();++ci){
        const auto& c=comps[(std::size_t)ci];
        for(int i=0;i<c.n;++i){
            const int ip=(i-1+c.n)%c.n, in=(i+1)%c.n;
            const double R=circumradius(points[c.start+(std::size_t)ip],points[c.start+(std::size_t)i],points[c.start+(std::size_t)in]);
            minR=std::min(minR,R);
            allk.push_back({ci,i,R,c.cum[(std::size_t)i]/c.length});
        }
    }

    const int S=(int)segs.size();
    const int T=std::min(threads,std::max(1,S));
    std::vector<std::vector<Contact>> locals((std::size_t)T);
    std::vector<double> local_min((std::size_t)T,std::numeric_limits<double>::infinity());
    std::vector<std::thread> pool; pool.reserve((std::size_t)T);
    const double cutoff_lo = radius>0 ? 2.0*radius*(1.0-contact_tol) : 0.0;
    const double cutoff_hi = radius>0 ? 2.0*radius*(1.0+contact_tol) : std::numeric_limits<double>::infinity();

    {
        py::gil_scoped_release release;
        for(int tid=0;tid<T;++tid){
            pool.emplace_back([&,tid](){
                auto& out=locals[(std::size_t)tid];
                double md=std::numeric_limits<double>::infinity();
                for(int i=tid;i<S;i+=T){
                    for(int j=i+1;j<S;++j){
                        if(locally_adjacent_same(segs[(std::size_t)i],segs[(std::size_t)j],comps,local_exclusion_frac)) continue;
                        auto cl=segseg(segs[(std::size_t)i].a,segs[(std::size_t)i].b,segs[(std::size_t)j].a,segs[(std::size_t)j].b);
                        md=std::min(md,cl.d);
                        if(cl.d>=cutoff_lo && cl.d<=cutoff_hi){
                            const auto&A=segs[(std::size_t)i]; const auto&B=segs[(std::size_t)j];
                            const double sna=(A.s0+cl.u*A.len)/A.comp_len;
                            const double snb=(B.s0+cl.v*B.len)/B.comp_len;
                            out.push_back({i,j,cl,sna,snb});
                        }
                    }
                }
                local_min[(std::size_t)tid]=md;
            });
        }
        for(auto&th:pool) th.join();
    }

    double minD=std::numeric_limits<double>::infinity();
    std::vector<Contact> activeC;
    for(int tid=0;tid<T;++tid){
        minD=std::min(minD,local_min[(std::size_t)tid]);
        auto& v=locals[(std::size_t)tid]; activeC.insert(activeC.end(),v.begin(),v.end());
    }
    std::sort(activeC.begin(),activeC.end(),[](const Contact&a,const Contact&b){ return std::tie(a.sa,a.sb)<std::tie(b.sa,b.sb); });
    if(!std::isfinite(minD)) minD=std::numeric_limits<double>::quiet_NaN();

    bool radius_inferred=false;
    if(!(radius>0)){
        radius=std::min(minR,0.5*minD); radius_inferred=true;
    }
    if(!(radius>0) || !std::isfinite(radius)) throw std::runtime_error("could not determine positive radius");
    // If radius had to be inferred, recompute active contacts against the actual cutoff.
    if(radius_inferred){
        const double c2=2.0*radius*(1.0+contact_tol);
        std::vector<Contact> keep; keep.reserve(activeC.size());
        // activeC was all contacts only when radius<=0, so filter now.
        for(auto&r:activeC) if(r.c.d>=2.0*radius*(1.0-contact_tol) && r.c.d<=c2) keep.push_back(r);
        activeC.swap(keep);
    }

    std::vector<Kink> activeK;
    for(const auto&k:allk) if(k.R>=radius*(1.0-kink_tol) && k.R<=radius*(1.0+kink_tol)) activeK.push_back(k);

    const int M=(int)(activeC.size()+activeK.size());
    std::vector<NZ> nz; nz.reserve(activeC.size()*12+activeK.size()*9);
    std::vector<double> b(3*points.size(),0.0);
    int col=0;
    for(const auto&r:activeC){
        const auto&A=segs[(std::size_t)r.sa]; const auto&B=segs[(std::size_t)r.sb];
        const Vec3 d=r.c.p-r.c.q; const double dn=norm(d); if(dn<=1e-15) continue;
        const Vec3 n=d/dn;
        const std::array<std::pair<std::size_t,double>,4> w={{{A.g0,0.5*(1-r.c.u)},{A.g1,0.5*r.c.u},{B.g0,-0.5*(1-r.c.v)},{B.g1,-0.5*r.c.v}}};
        for(const auto&ww:w){
            const int base=3*(int)ww.first;
            nz.push_back({base+0,col,ww.second*n.x}); nz.push_back({base+1,col,ww.second*n.y}); nz.push_back({base+2,col,ww.second*n.z});
        }
        ++col;
    }
    const double mean_seg = [&](){ double s=0; for(const auto&q:segs)s+=q.len; return s/std::max<std::size_t>(1,segs.size()); }();
    const double h=std::max(1e-9,1e-7*mean_seg);
    for(const auto&r:activeK){
        const auto&c=comps[(std::size_t)r.comp]; const int n=c.n, i=r.vi, ip=(i-1+n)%n, in=(i+1)%n;
        const std::array<int,3> loc={ip,i,in};
        for(int q=0;q<3;++q){
            for(int ax=0;ax<3;++ax){
                Vec3 pp=points[c.start+(std::size_t)ip], pc=points[c.start+(std::size_t)i], pn=points[c.start+(std::size_t)in];
                Vec3* vp=q==0?&pp:(q==1?&pc:&pn); if(ax==0)vp->x+=h; else if(ax==1)vp->y+=h; else vp->z+=h;
                const double rp=circumradius(pp,pc,pn);
                pp=points[c.start+(std::size_t)ip]; pc=points[c.start+(std::size_t)i]; pn=points[c.start+(std::size_t)in];
                Vec3* vm=q==0?&pp:(q==1?&pc:&pn); if(ax==0)vm->x-=h; else if(ax==1)vm->y-=h; else vm->z-=h;
                const double rm=circumradius(pp,pc,pn); const double g=(rp-rm)/(2*h);
                if(std::isfinite(g)){ const std::size_t gv=c.start+(std::size_t)loc[(std::size_t)q]; nz.push_back({3*(int)gv+ax,col,g}); }
            }
        }
        ++col;
    }

    for(const auto&c:comps){
        for(int i=0;i<c.n;++i){
            const int ip=(i-1+c.n)%c.n, in=(i+1)%c.n;
            const auto gi=c.start+(std::size_t)i, gp=c.start+(std::size_t)ip, gn=c.start+(std::size_t)in;
            const Vec3 a=points[gi]-points[gp], d=points[gi]-points[gn];
            const double na=norm(a), nd=norm(d); if(na<=0||nd<=0) throw std::runtime_error("zero edge length");
            const Vec3 g=a/na+d/nd; b[3*gi]=g.x; b[3*gi+1]=g.y; b[3*gi+2]=g.z;
        }
    }

    py::array_t<long long> rows(nz.size()), cols(nz.size()); py::array_t<double> vals(nz.size()), b_arr(b.size());
    auto rr=rows.mutable_unchecked<1>(); auto cc=cols.mutable_unchecked<1>(); auto vv=vals.mutable_unchecked<1>(); auto bb=b_arr.mutable_unchecked<1>();
    for(std::size_t i=0;i<nz.size();++i){rr((py::ssize_t)i)=nz[i].row;cc((py::ssize_t)i)=nz[i].col;vv((py::ssize_t)i)=nz[i].value;}
    for(std::size_t i=0;i<b.size();++i)bb((py::ssize_t)i)=b[i];

    py::list contacts;
    int ccol=0;
    for(const auto&r:activeC){
        const auto&A=segs[(std::size_t)r.sa]; const auto&B=segs[(std::size_t)r.sb];
        if(norm(r.c.p-r.c.q)<=1e-15) continue;
        py::dict d; d["column"]=ccol++; d["comp_a"]=A.comp; d["seg_a"]=A.i; d["u"]=r.c.u; d["s_norm"]=r.sna;
        d["comp_b"]=B.comp; d["seg_b"]=B.i; d["v"]=r.c.v; d["t_norm"]=r.snb; d["distance"]=r.c.d; contacts.append(d);
    }
    py::list kinks;
    int kcol=ccol;
    for(const auto&r:activeK){ py::dict d; d["column"]=kcol++; d["comp"]=r.comp; d["vertex"]=r.vi; d["s_norm"]=r.snorm; d["radius"]=r.R; kinks.append(d); }

    py::dict meta;
    meta["backend"]="cpp-pybind11"; meta["component_count"]=(int)comps.size(); meta["vertex_count"]=(int)points.size(); meta["segment_count"]=(int)segs.size();
    meta["min_discrete_curvature_radius"]=minR; meta["min_nonadjacent_segment_distance"]=minD; meta["radius"]=radius; meta["radius_inferred"]=radius_inferred;
    meta["contact_tolerance_fraction"]=contact_tol; meta["kink_tolerance_fraction"]=kink_tol; meta["local_exclusion_fraction"]=local_exclusion_frac;
    meta["active_strut_count"]=(int)contacts.size(); meta["active_kink_count"]=(int)kinks.size(); meta["matrix_rows"]=(int)(3*points.size()); meta["matrix_columns"]=(int)(contacts.size()+kinks.size()); meta["threads"]=T;

    py::dict out; out["rows"]=rows; out["cols"]=cols; out["data"]=vals; out["b"]=b_arr; out["shape"]=py::make_tuple((int)(3*points.size()),(int)(contacts.size()+kinks.size())); out["contacts"]=contacts; out["kinks"]=kinks; out["metrics"]=meta;
    return out;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "5_Maxwell SST reciprocal-stress native geometry/contact kernel";
    m.def("analyze_geometry", &analyze_geometry,
          py::arg("points"), py::arg("component_counts"), py::arg("radius")=-1.0,
          py::arg("contact_tol")=0.015, py::arg("kink_tol")=0.015,
          py::arg("local_exclusion_frac")=0.02, py::arg("threads")=1,
          "Infer active struts/kinks and assemble sparse first-order rigidity matrix and length gradient.");
    m.def("version", [](){ return std::string("0.2.0"); });
}
