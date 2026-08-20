#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <limits>
#include <string>
#include <thread>
#include <vector>
namespace py = pybind11;
constexpr double PI=3.141592653589793238462643383279502884;
struct V3{double x,y,z;};
inline V3 add(V3 a,V3 b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
inline V3 sub(V3 a,V3 b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
inline V3 mul(V3 a,double s){return {a.x*s,a.y*s,a.z*s};}
inline double dot(V3 a,V3 b){return a.x*b.x+a.y*b.y+a.z*b.z;}
inline V3 cross(V3 a,V3 b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
inline double norm(V3 a){return std::sqrt(dot(a,a));}
template<class F> void parallel_for(std::size_t n,int threads,F fn){
 if(n==0)return; unsigned hw=std::thread::hardware_concurrency(); int nt=threads>0?threads:(hw?int(hw):1); nt=std::max(1,std::min<int>(nt,int(n)));
 if(nt==1||n<64){for(std::size_t i=0;i<n;++i)fn(i);return;} std::vector<std::thread> pool; std::atomic<std::size_t> next{0};
 for(int t=0;t<nt;++t)pool.emplace_back([&](){for(;;){auto i=next.fetch_add(1);if(i>=n)break;fn(i);}}); for(auto&th:pool)th.join();
}
std::vector<V3> read_points(const py::array_t<double,py::array::c_style|py::array::forcecast>&a){auto b=a.request();if(b.ndim!=2||b.shape[1]!=3)throw std::runtime_error("points must be Nx3");const double*p=(const double*)b.ptr;std::vector<V3>o(b.shape[0]);for(py::ssize_t i=0;i<b.shape[0];++i)o[i]={p[3*i],p[3*i+1],p[3*i+2]};return o;}
struct Seg{V3 p,q,m,dl;};
std::vector<Seg> segs(const std::vector<V3>&p){std::vector<Seg>s(p.size());for(std::size_t i=0;i<p.size();++i){V3 q=p[(i+1)%p.size()];V3 dl=sub(q,p[i]);s[i]={p[i],q,mul(add(q,p[i]),0.5),dl};}return s;}
double denom3(double r2,double a,const std::string&k){
 if(k=="softcore")return std::pow(r2+a*a,1.5);
 if(k=="vatistas2")return std::pow(r2*r2+std::pow(a,4),0.75);
 double r=std::sqrt(r2);return std::pow(std::max(r,1e-300),3);
}
py::dict polyline_stats(const py::array_t<double,py::array::c_style|py::array::forcecast>&arr,bool closed=true){auto p=read_points(arr);if(p.size()<2)throw std::runtime_error("need >=2 points");std::size_t m=closed?p.size():p.size()-1;double L=0,mn=1e300,mx=0;std::vector<double>e(m);V3 c{0,0,0};for(auto q:p)c=add(c,q);c=mul(c,1.0/p.size());for(std::size_t i=0;i<m;++i){V3 d=sub(p[(i+1)%p.size()],p[i]);e[i]=norm(d);L+=e[i];mn=std::min(mn,e[i]);mx=std::max(mx,e[i]);}double mean=L/m,var=0;for(double x:e){double d=x-mean;var+=d*d;}var/=m;py::dict d;d["n_vertices"]=p.size();d["length"]=L;d["edge_mean"]=mean;d["edge_min"]=mn;d["edge_max"]=mx;d["edge_cv"]=std::sqrt(var)/std::max(mean,1e-300);d["centroid"]=py::make_tuple(c.x,c.y,c.z);return d;}
double interaction_energy(const py::array_t<double,py::array::c_style|py::array::forcecast>&aa,const py::array_t<double,py::array::c_style|py::array::forcecast>&bb,double a=0.0,int threads=0){auto A=segs(read_points(aa)),B=segs(read_points(bb));double a2=a*a;std::vector<double>part(A.size(),0);{py::gil_scoped_release rel;parallel_for(A.size(),threads,[&](std::size_t i){double s=0;for(auto&b:B){V3 r=sub(A[i].m,b.m);s+=dot(A[i].dl,b.dl)/std::sqrt(dot(r,r)+a2);}part[i]=s;});}double sum=0;for(double x:part)sum+=x;return sum/(4*PI);}
py::array_t<double> biot_savart(const py::array_t<double,py::array::c_style|py::array::forcecast>&source,const py::array_t<double,py::array::c_style|py::array::forcecast>&query,double a=0.0,const std::string&kernel="softcore",int threads=0){auto S=segs(read_points(source));auto Q=read_points(query);py::array_t<double>out({static_cast<py::ssize_t>(Q.size()), static_cast<py::ssize_t>(3)});auto b=out.request();double*dst=(double*)b.ptr;{py::gil_scoped_release rel;parallel_for(Q.size(),threads,[&](std::size_t i){V3 v{0,0,0};for(auto&s:S){V3 r=sub(Q[i],s.m);double r2=dot(r,r);if(a==0.0&&r2<1e-28)continue;double den=denom3(r2,a,kernel);v=add(v,mul(cross(s.dl,r),1.0/den));}v=mul(v,1.0/(4*PI));dst[3*i]=v.x;dst[3*i+1]=v.y;dst[3*i+2]=v.z;});}return out;}
double gauss_linking(const py::array_t<double,py::array::c_style|py::array::forcecast>&aa,const py::array_t<double,py::array::c_style|py::array::forcecast>&bb,double a=0.0,int threads=0){auto A=segs(read_points(aa)),B=segs(read_points(bb));double a2=a*a;std::vector<double>part(A.size(),0);{py::gil_scoped_release rel;parallel_for(A.size(),threads,[&](std::size_t i){double s=0;for(auto&b:B){V3 r=sub(A[i].m,b.m);double r2=dot(r,r)+a2;if(r2<1e-28)continue;s+=dot(cross(A[i].dl,b.dl),r)/std::pow(r2,1.5);}part[i]=s;});}double sum=0;for(double x:part)sum+=x;return sum/(4*PI);}
// Standard closest distance between two line segments.
double segdist(const Seg&A,const Seg&B){V3 u=sub(A.q,A.p),v=sub(B.q,B.p),w=sub(A.p,B.p);double a=dot(u,u),b=dot(u,v),c=dot(v,v),d=dot(u,w),e=dot(v,w),D=a*c-b*b,sc,sN,sD=D,tc,tN,tD=D;const double EPS=1e-14;if(D<EPS){sN=0;sD=1;tN=e;tD=c;}else{sN=b*e-c*d;tN=a*e-b*d;if(sN<0){sN=0;tN=e;tD=c;}else if(sN>sD){sN=sD;tN=e+b;tD=c;}}if(tN<0){tN=0;if(-d<0)sN=0;else if(-d>a)sN=sD;else{sN=-d;sD=a;}}else if(tN>tD){tN=tD;if((-d+b)<0)sN=0;else if((-d+b)>a)sN=sD;else{sN=(-d+b);sD=a;}}sc=(std::abs(sN)<EPS?0:sN/sD);tc=(std::abs(tN)<EPS?0:tN/tD);V3 dp=sub(add(w,mul(u,sc)),mul(v,tc));return norm(dp);}
double min_segment_distance(const py::array_t<double,py::array::c_style|py::array::forcecast>&aa,const py::array_t<double,py::array::c_style|py::array::forcecast>&bb,bool same_component=false,int exclude_neighbors=2,int threads=0){auto A=segs(read_points(aa)),B=segs(read_points(bb));std::vector<double>part(A.size(),std::numeric_limits<double>::infinity());{py::gil_scoped_release rel;parallel_for(A.size(),threads,[&](std::size_t i){double mn=std::numeric_limits<double>::infinity();for(std::size_t j=0;j<B.size();++j){if(same_component){std::size_t n=A.size();std::size_t dij=i>j?i-j:j-i;dij=std::min(dij,n-dij);if(int(dij)<=exclude_neighbors)continue;}mn=std::min(mn,segdist(A[i],B[j]));}part[i]=mn;});}double mn=std::numeric_limits<double>::infinity();for(double x:part)mn=std::min(mn,x);return mn;}

double doubly_critical_distance(const py::array_t<double,py::array::c_style|py::array::forcecast>&aa,const py::array_t<double,py::array::c_style|py::array::forcecast>&bb,bool same_component=false,int exclude_neighbors=3,double cos_tol=0.20,int threads=0){auto A=segs(read_points(aa)),B=segs(read_points(bb));std::vector<double>part(A.size(),std::numeric_limits<double>::infinity());{py::gil_scoped_release rel;parallel_for(A.size(),threads,[&](std::size_t i){double mn=std::numeric_limits<double>::infinity();double na=norm(A[i].dl);if(na<1e-300){part[i]=mn;return;}V3 ta=mul(A[i].dl,1.0/na);for(std::size_t j=0;j<B.size();++j){if(same_component){std::size_t n=A.size();std::size_t dij=i>j?i-j:j-i;dij=std::min(dij,n-dij);if(int(dij)<=exclude_neighbors)continue;}double nb=norm(B[j].dl);if(nb<1e-300)continue;V3 tb=mul(B[j].dl,1.0/nb);V3 r=sub(B[j].m,A[i].m);double d=norm(r);if(d<1e-300)continue;double ca=std::abs(dot(r,ta))/d,cb=std::abs(dot(r,tb))/d;if(ca<=cos_tol&&cb<=cos_tol)mn=std::min(mn,d);}part[i]=mn;});}double mn=std::numeric_limits<double>::infinity();for(double x:part)mn=std::min(mn,x);return mn;}
PYBIND11_MODULE(_native,m){m.doc()="Helmholtz-SST v0.1.1 native vortex kernels";m.def("polyline_stats",&polyline_stats,py::arg("points"),py::arg("closed")=true);m.def("interaction_energy",&interaction_energy,py::arg("a"),py::arg("b"),py::arg("core_radius")=0.0,py::arg("threads")=0);m.def("biot_savart",&biot_savart,py::arg("source"),py::arg("query"),py::arg("core_radius")=0.0,py::arg("kernel")="softcore",py::arg("threads")=0);m.def("gauss_linking",&gauss_linking,py::arg("a"),py::arg("b"),py::arg("core_radius")=0.0,py::arg("threads")=0);m.def("min_segment_distance",&min_segment_distance,py::arg("a"),py::arg("b"),py::arg("same_component")=false,py::arg("exclude_neighbors")=2,py::arg("threads")=0);m.def("doubly_critical_distance",&doubly_critical_distance,py::arg("a"),py::arg("b"),py::arg("same_component")=false,py::arg("exclude_neighbors")=3,py::arg("cos_tol")=0.20,py::arg("threads")=0);}
