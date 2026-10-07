#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace py=pybind11;
static constexpr double PI=3.141592653589793238462643383279502884;
struct V{double x,y,z;};
static V add(V a,V b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
static V sub(V a,V b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
static V mul(V a,double s){return {a.x*s,a.y*s,a.z*s};}
static double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static V crossp(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
static double norm(V a){return std::sqrt(dot(a,a));}
static V mid(V a,V b){return {(a.x+b.x)/2,(a.y+b.y)/2,(a.z+b.z)/2};}
static int csep(int i,int j,int n){int d=std::abs(i-j);return std::min(d,n-d);}
static double segdist(V p1,V q1,V p2,V q2){
 V d1=sub(q1,p1),d2=sub(q2,p2),r=sub(p1,p2); double a=dot(d1,d1),e=dot(d2,d2),f=dot(d2,r),eps=1e-15,s,t;
 if(a<=eps&&e<=eps)return norm(r);
 if(a<=eps){s=0;t=std::clamp(f/e,0.0,1.0);} else {double c=dot(d1,r); if(e<=eps){t=0;s=std::clamp(-c/a,0.0,1.0);} else {double b=dot(d1,d2),den=a*e-b*b;s=std::abs(den)<=eps?0.0:std::clamp((b*f-c*e)/den,0.0,1.0);t=(b*s+f)/e;if(t<0){t=0;s=std::clamp(-c/a,0.0,1.0);}else if(t>1){t=1;s=std::clamp((b-c)/a,0.0,1.0);}}}
 return norm(sub(add(p1,mul(d1,s)),add(p2,mul(d2,t))));
}
struct Seg{int c,i,n;V m,dl,a,b;double s,L;};
static py::dict measure(py::list pycomps,double core,double arcfrac){
 std::vector<std::vector<V>> comps; for(auto co:pycomps){py::list L=py::cast<py::list>(co);std::vector<V> c;c.reserve(py::len(L));for(auto po:L){auto p=py::cast<std::vector<double>>(po);c.push_back({p[0],p[1],p[2]});}comps.push_back(std::move(c));}
 std::vector<Seg> segs;double total=0,bend=0;
 for(int ci=0;ci<(int)comps.size();++ci){auto &c=comps[ci];int n=(int)c.size();std::vector<double> lens(n);double L=0;for(int i=0;i<n;++i){lens[i]=norm(sub(c[(i+1)%n],c[i]));L+=lens[i];}total+=L;double cum=0;for(int i=0;i<n;++i){V a=c[i],b=c[(i+1)%n],dl=sub(b,a);segs.push_back({ci,i,n,mid(a,b),dl,a,b,cum+.5*lens[i],L});cum+=lens[i];}for(int i=0;i<n;++i){V v1=sub(c[i],c[(i-1+n)%n]),v2=sub(c[(i+1)%n],c[i]);double n1=norm(v1),n2=norm(v2);if(n1*n2>1e-15){double co=std::clamp(dot(v1,v2)/(n1*n2),-1.0,1.0),ang=std::acos(co);bend+=ang*ang/(.5*(n1+n2)+1e-15);}}}
 double mind=std::numeric_limits<double>::infinity();
 for(int i=0;i<(int)segs.size();++i)for(int j=i+1;j<(int)segs.size();++j){auto&a=segs[i];auto&b=segs[j];if(a.c==b.c){double ds=std::abs(a.s-b.s),arc=std::min(ds,a.L-ds);if(arc<arcfrac*a.L)continue;}mind=std::min(mind,segdist(a.a,a.b,b.a,b.b));}if(!std::isfinite(mind))mind=0;
 int k=(int)comps.size();double neumann=0,writhe=0;std::vector<double> link(k*k,0.0);
 #pragma omp parallel
 {double ln=0,lw=0;std::vector<double> ll(k*k,0.0);
  #pragma omp for schedule(static)
  for(int i=0;i<(int)segs.size();++i)for(int j=i+1;j<(int)segs.size();++j){auto&a=segs[i];auto&b=segs[j];if(a.c==b.c&&csep(a.i,b.i,a.n)<=1)continue;V r=sub(a.m,b.m);double bare=dot(r,r),reg=bare+core*core;ln+=dot(a.dl,b.dl)/std::sqrt(reg);if(bare<=1e-24)continue;double g=dot(r,crossp(a.dl,b.dl))/std::pow(bare,1.5)/(4.0*PI);if(a.c==b.c)lw+=2*g;else{ll[a.c*k+b.c]+=g;ll[b.c*k+a.c]+=g;}}
  #pragma omp critical
  {neumann+=ln;writhe+=lw;for(size_t q=0;q<link.size();++q)link[q]+=ll[q];}}
 double strength=0,istrength=0,res=0;int nr=0;py::list mat;for(int i=0;i<k;++i){py::list row;for(int j=0;j<k;++j)row.append(link[i*k+j]);mat.append(row);for(int j=i+1;j<k;++j){double x=link[i*k+j];strength+=std::abs(x);istrength+=std::abs(std::round(x));res+=std::abs(x-std::round(x));++nr;}}
 double meanseg=total/std::max<size_t>(1,segs.size());py::dict d;d["total_length"]=total;d["bend_energy"]=bend;d["min_distance"]=mind;d["mean_segment"]=meanseg;d["contact_ratio"]=mind/(meanseg+1e-15);d["neumann_energy"]=neumann;d["abs_neumann_energy"]=std::abs(neumann);d["writhe"]=writhe;d["abs_writhe"]=std::abs(writhe);d["linking_strength"]=strength;d["linking_integer_strength"]=istrength;d["linking_residual"]=nr?res/nr:0.0;d["component_count"]=k;d["linking_matrix"]=mat;d["arclength_exclusion_fraction"]=arcfrac;return d;}
PYBIND11_MODULE(a055_native,m){m.doc()="A055 v0.2.0 topology-baseline C++17/OpenMP kernel";m.def("measure",&measure,py::arg("components"),py::arg("core")=0.03,py::arg("arclength_exclusion_fraction")=0.08);}
