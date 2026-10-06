#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <array>
#include <cmath>
#include <algorithm>
#include <limits>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
static constexpr double PI = 3.141592653589793238462643383279502884;
struct V{double x,y,z;};
static V sub(V a,V b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
static double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static V crossp(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
static double norm(V a){return std::sqrt(dot(a,a));}
static V mid(V a,V b){return {(a.x+b.x)/2,(a.y+b.y)/2,(a.z+b.z)/2};}
static int csep(int i,int j,int n){int d=std::abs(i-j);return std::min(d,n-d);}
struct Seg{int c,i,n;V m,dl;};

static py::dict measure(py::list pycomps,double core){
    std::vector<std::vector<V>> comps;
    for(auto co:pycomps){
        py::list L=py::cast<py::list>(co); std::vector<V> c; c.reserve(py::len(L));
        for(auto po:L){
            auto p=py::cast<std::vector<double>>(po);
            if(p.size()!=3) throw std::runtime_error("point must have 3 coordinates");
            c.push_back({p[0],p[1],p[2]});
        }
        comps.push_back(std::move(c));
    }
    std::vector<Seg> segs; double total=0,bend=0;
    for(int ci=0;ci<(int)comps.size();++ci){
        auto &c=comps[ci]; int n=(int)c.size();
        for(int i=0;i<n;++i){
            V a=c[i],b=c[(i+1)%n],dl=sub(b,a); double ds=norm(dl);
            total+=ds; segs.push_back({ci,i,n,mid(a,b),dl});
        }
        for(int i=0;i<n;++i){
            V v1=sub(c[i],c[(i-1+n)%n]), v2=sub(c[(i+1)%n],c[i]);
            double n1=norm(v1),n2=norm(v2);
            if(n1*n2>1e-15){
                double co=std::clamp(dot(v1,v2)/(n1*n2),-1.0,1.0);
                double ang=std::acos(co);
                bend+=ang*ang/(0.5*(n1+n2)+1e-15);
            }
        }
    }
    double min_d=std::numeric_limits<double>::infinity();
    for(int ca=0;ca<(int)comps.size();++ca) for(int ia=0;ia<(int)comps[ca].size();++ia)
      for(int cb=ca;cb<(int)comps.size();++cb){
        int st=(cb==ca?ia+1:0);
        for(int ib=st;ib<(int)comps[cb].size();++ib){
            if(ca==cb && csep(ia,ib,(int)comps[ca].size())<=2) continue;
            min_d=std::min(min_d,norm(sub(comps[ca][ia],comps[cb][ib])));
        }
      }
    if(!std::isfinite(min_d)) min_d=0.0;

    int k=(int)comps.size();
    double neumann=0,writhe=0;
    std::vector<double> link(k*k,0.0);

    #pragma omp parallel
    {
        double ln=0,lw=0;
        std::vector<double> ll(k*k,0.0);
        #pragma omp for schedule(static)
        for(int i=0;i<(int)segs.size();++i){
            for(int j=i+1;j<(int)segs.size();++j){
                auto &a=segs[i]; auto &b=segs[j];
                if(a.c==b.c && csep(a.i,b.i,a.n)<=1) continue;
                V r=sub(a.m,b.m); double r2=dot(r,r)+core*core;
                ln += dot(a.dl,b.dl)/std::sqrt(r2);
                double g=dot(r,crossp(a.dl,b.dl))/std::pow(r2,1.5)/(4.0*PI);
                if(a.c==b.c) lw += 2.0*g;
                else { ll[a.c*k+b.c]+=g; ll[b.c*k+a.c]+=g; }
            }
        }
        #pragma omp critical
        {
            neumann+=ln; writhe+=lw;
            for(size_t q=0;q<link.size();++q) link[q]+=ll[q];
        }
    }

    double strength=0,res=0; int nr=0;
    py::list mat;
    for(int i=0;i<k;++i){
        py::list row;
        for(int j=0;j<k;++j) row.append(link[i*k+j]);
        mat.append(row);
        for(int j=i+1;j<k;++j){
            double x=link[i*k+j]; strength+=std::abs(x); res+=std::abs(x-std::round(x)); ++nr;
        }
    }
    double mean_seg=total/std::max<size_t>(1,segs.size());
    py::dict d;
    d["total_length"]=total; d["bend_energy"]=bend; d["min_distance"]=min_d;
    d["mean_segment"]=mean_seg; d["contact_ratio"]=min_d/(mean_seg+1e-15);
    d["neumann_energy"]=neumann; d["abs_neumann_energy"]=std::abs(neumann);
    d["writhe"]=writhe; d["abs_writhe"]=std::abs(writhe);
    d["linking_strength"]=strength; d["linking_residual"]=nr?res/nr:0.0;
    d["component_count"]=k; d["linking_matrix"]=mat;
    return d;
}
PYBIND11_MODULE(a054_native,m){
    m.doc()="A054 C++17/OpenMP screening kernel";
    m.def("measure",&measure,py::arg("components"),py::arg("core")=0.03);
}
