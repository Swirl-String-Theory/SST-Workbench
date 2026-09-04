#include <sycl/sycl.hpp>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef SST_GPU_FP64
using Real = double;
static constexpr const char* PRECISION_NAME = "float64";
#else
using Real = float;
static constexpr const char* PRECISION_NAME = "float32";
#endif

struct Vec3 { Real x,y,z; };
struct DVec3 { double x,y,z; };

static Vec3 add(Vec3 a, Vec3 b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
static Vec3 sub(Vec3 a, Vec3 b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
static Vec3 mul(Vec3 a, Real s){return {a.x*s,a.y*s,a.z*s};}
static double normd(DVec3 a){return std::sqrt(a.x*a.x+a.y*a.y+a.z*a.z);}

struct Args{
    std::string input, output, meta; int steps=0;
};
static Args parse_args(int argc,char**argv){
    Args a;
    for(int i=1;i<argc;i++){
        std::string s=argv[i];
        auto need=[&](std::string& out){if(i+1>=argc)throw std::runtime_error("missing value for "+s);out=argv[++i];};
        if(s=="--input") need(a.input); else if(s=="--output") need(a.output); else if(s=="--meta") need(a.meta); else if(s=="--steps"){std::string v;need(v);a.steps=std::stoi(v);} else throw std::runtime_error("unknown arg: "+s);
    }
    if(a.input.empty()||a.output.empty()||a.meta.empty()) throw std::runtime_error("--input --output --meta required");
    return a;
}

struct Header{char magic[8]; uint32_t version,K,N; double core,cfl;};
struct Batch{
    Header h{}; std::vector<std::array<char,24>> ids; std::vector<Vec3> x; std::vector<int32_t> next;
};
static Batch read_batch(const std::string& path){
    std::ifstream f(path,std::ios::binary); if(!f) throw std::runtime_error("cannot open input");
    Batch b;
    f.read(b.h.magic,8);
    f.read(reinterpret_cast<char*>(&b.h.version),sizeof(uint32_t));
    f.read(reinterpret_cast<char*>(&b.h.K),sizeof(uint32_t));
    f.read(reinterpret_cast<char*>(&b.h.N),sizeof(uint32_t));
    f.read(reinterpret_cast<char*>(&b.h.core),sizeof(double));
    f.read(reinterpret_cast<char*>(&b.h.cfl),sizeof(double));
    if(std::memcmp(b.h.magic,"SSTGPU40",8)!=0||b.h.version!=1) throw std::runtime_error("batch format mismatch");
    const size_t total=size_t(b.h.K)*b.h.N; b.ids.resize(b.h.K); b.x.resize(total); b.next.resize(total);
    for(uint32_t c=0;c<b.h.K;c++){
        f.read(b.ids[c].data(),24);
        for(uint32_t i=0;i<b.h.N;i++){
            double q[3]; f.read(reinterpret_cast<char*>(q),sizeof(q)); b.x[size_t(c)*b.h.N+i]={(Real)q[0],(Real)q[1],(Real)q[2]};
        }
        f.read(reinterpret_cast<char*>(b.next.data()+size_t(c)*b.h.N),sizeof(int32_t)*b.h.N);
    }
    if(!f) throw std::runtime_error("truncated batch"); return b;
}

static std::string idstr(const std::array<char,24>& a){size_t n=0;while(n<a.size()&&a[n])n++;return std::string(a.data(),n);}

static void compute_velocity(sycl::queue& q, const std::vector<Vec3>& x, const std::vector<int32_t>& next, uint32_t K,uint32_t N, Real core, std::vector<Vec3>& v){
    const size_t total=size_t(K)*N; v.assign(total,{0,0,0}); const Real pref=Real(1.0/(4.0*3.141592653589793238462643383279502884)); const Real core2=core*core;
    sycl::buffer<Vec3,1> bx(x.data(),sycl::range<1>(total)); sycl::buffer<int32_t,1> bn(next.data(),sycl::range<1>(total)); sycl::buffer<Vec3,1> bv(v.data(),sycl::range<1>(total));
    q.submit([&](sycl::handler& h){
        auto X=bx.template get_access<sycl::access::mode::read>(h); auto NN=bn.template get_access<sycl::access::mode::read>(h); auto V=bv.template get_access<sycl::access::mode::write>(h);
        h.parallel_for(sycl::range<1>(total),[=](sycl::id<1> id){
            size_t gi=id[0]; uint32_t c=uint32_t(gi/N); size_t base=size_t(c)*N; Vec3 xi=X[gi]; Real ux=0,uy=0,uz=0;
            for(uint32_t jj=0;jj<N;jj++){
                size_t gj=base+jj; int32_t nk=NN[gj]; if(nk<0)continue; size_t gk=base+size_t(nk);
                Vec3 a=X[gj],b=X[gk]; Real dlx=b.x-a.x,dly=b.y-a.y,dlz=b.z-a.z; Real mx=Real(.5)*(a.x+b.x),my=Real(.5)*(a.y+b.y),mz=Real(.5)*(a.z+b.z);
                Real rx=xi.x-mx,ry=xi.y-my,rz=xi.z-mz; Real r2=rx*rx+ry*ry+rz*rz+core2; Real den=r2*sycl::sqrt(r2); Real fac=pref/den;
                ux+=(dly*rz-dlz*ry)*fac; uy+=(dlz*rx-dlx*rz)*fac; uz+=(dlx*ry-dly*rx)*fac;
            }
            V[gi]={ux,uy,uz};
        });
    }).wait();
}

static std::vector<int> advance_pairs(const int32_t* nxt,uint32_t N,int i,int lag){int j=i;for(int s=0;s<lag;s++){if(j<0||j>=int(N))return{};j=nxt[j];}if(j<0||j==i)return{};return{i,j};}
static double mesh_cv(const Vec3* x,const int32_t*nxt,uint32_t N,double* edge_ratio=nullptr){std::vector<double>d;for(uint32_t i=0;i<N;i++){int j=nxt[i];if(j<0)continue;double dx=double(x[j].x)-x[i].x,dy=double(x[j].y)-x[i].y,dz=double(x[j].z)-x[i].z;d.push_back(std::sqrt(dx*dx+dy*dy+dz*dz));}double m=std::accumulate(d.begin(),d.end(),0.0)/std::max<size_t>(1,d.size());double s=0,mn=1e300,mx=0;for(double z:d){s+=(z-m)*(z-m);mn=std::min(mn,z);mx=std::max(mx,z);}if(edge_ratio)*edge_ratio=mx/std::max(mn,1e-300);return std::sqrt(s/std::max<size_t>(1,d.size()))/std::max(std::abs(m),1e-300);}
static double ds_min(const Vec3* x,const int32_t*nxt,uint32_t N){double mn=1e300;for(uint32_t i=0;i<N;i++){int j=nxt[i];if(j<0)continue;double dx=double(x[j].x)-x[i].x,dy=double(x[j].y)-x[i].y,dz=double(x[j].z)-x[i].z;mn=std::min(mn,std::sqrt(dx*dx+dy*dy+dz*dz));}return mn;}
static double pair_strain(const Vec3* x,const Vec3* v,const int32_t*nxt,uint32_t N){long double ss=0;size_t cnt=0;const int lags[4]={2,4,8,16};for(uint32_t i=0;i<N;i++)for(int lag:lags){auto p=advance_pairs(nxt,N,int(i),lag);if(p.empty())continue;int j=p[1];double dx=double(x[j].x)-x[i].x,dy=double(x[j].y)-x[i].y,dz=double(x[j].z)-x[i].z;double dvx=double(v[j].x)-v[i].x,dvy=double(v[j].y)-v[i].y,dvz=double(v[j].z)-v[i].z;double den=dx*dx+dy*dy+dz*dz;if(den>1e-20){double r=(dx*dvx+dy*dvy+dz*dvz)/den;ss+=r*r;cnt++;}}return cnt?std::sqrt(double(ss/cnt)):1e300;}
static double shape_drift(const Vec3*x0,const Vec3*x1,const int32_t*nxt,uint32_t N){long double ss=0;size_t cnt=0;const int lags[4]={2,4,8,16};for(uint32_t i=0;i<N;i++)for(int lag:lags){auto p=advance_pairs(nxt,N,int(i),lag);if(p.empty())continue;int j=p[1];auto D=[&](const Vec3*x){double dx=double(x[j].x)-x[i].x,dy=double(x[j].y)-x[i].y,dz=double(x[j].z)-x[i].z;return std::sqrt(dx*dx+dy*dy+dz*dz);};double a=D(x0),b=D(x1);if(a>1e-15&&b>1e-15){double z=std::log(b/a);ss+=z*z;cnt++;}}return cnt?std::sqrt(double(ss/cnt)):1e300;}

int main(int argc,char**argv){
    try{
        Args a=parse_args(argc,argv); Batch b=read_batch(a.input);
        sycl::queue q{sycl::gpu_selector_v};
#ifdef SST_GPU_FP64
        if(!q.get_device().has(sycl::aspect::fp64)) throw std::runtime_error("selected GPU has no fp64 aspect");
#endif
        std::vector<Vec3>x0=b.x,x=b.x,v0,v,k2,tmp; compute_velocity(q,x,b.next,b.h.K,b.h.N,(Real)b.h.core,v0);
        std::vector<double>dt(b.h.K);for(uint32_t c=0;c<b.h.K;c++){double d=ds_min(x.data()+size_t(c)*b.h.N,b.next.data()+size_t(c)*b.h.N,b.h.N);dt[c]=4.0*3.14159265358979323846*b.h.cfl*d*d;}
        for(int step=0;step<a.steps;step++){
            compute_velocity(q,x,b.next,b.h.K,b.h.N,(Real)b.h.core,v); tmp=x;
            for(uint32_t c=0;c<b.h.K;c++)for(uint32_t i=0;i<b.h.N;i++){size_t g=size_t(c)*b.h.N+i;tmp[g]=add(x[g],mul(v[g],Real(0.5*dt[c])));} compute_velocity(q,tmp,b.next,b.h.K,b.h.N,(Real)b.h.core,k2);
            for(uint32_t c=0;c<b.h.K;c++)for(uint32_t i=0;i<b.h.N;i++){size_t g=size_t(c)*b.h.N+i;x[g]=add(x[g],mul(k2[g],Real(dt[c])));} 
        }
        std::ofstream o(a.output); if(!o)throw std::runtime_error("cannot open output"); o<<std::setprecision(17); o<<"opaque_id,mean_speed,speed_cv,pair_strain_rms,mesh_cv_initial,mesh_edge_ratio_initial,shape_signature_drift,mesh_cv_final,mesh_edge_ratio_final,steps,dt_hat\n";
        for(uint32_t c=0;c<b.h.K;c++){size_t base=size_t(c)*b.h.N;std::vector<double>s(b.h.N);for(uint32_t i=0;i<b.h.N;i++){auto z=v0[base+i];s[i]=std::sqrt(double(z.x)*z.x+double(z.y)*z.y+double(z.z)*z.z);}double mean=std::accumulate(s.begin(),s.end(),0.0)/s.size();double vv=0;for(double z:s)vv+=(z-mean)*(z-mean);double scv=std::sqrt(vv/s.size())/std::max(std::abs(mean),1e-300);double er0,er1;double cv0=mesh_cv(x0.data()+base,b.next.data()+base,b.h.N,&er0),cv1=mesh_cv(x.data()+base,b.next.data()+base,b.h.N,&er1);double strain=pair_strain(x0.data()+base,v0.data()+base,b.next.data()+base,b.h.N);double drift=a.steps?shape_drift(x0.data()+base,x.data()+base,b.next.data()+base,b.h.N):0.0;o<<idstr(b.ids[c])<<','<<mean<<','<<scv<<','<<strain<<','<<cv0<<','<<er0<<','<<drift<<','<<cv1<<','<<er1<<','<<a.steps<<','<<dt[c]<<"\n";}
        std::ofstream m(a.meta);m<<"device="<<q.get_device().get_info<sycl::info::device::name>()<<"\n"<<"vendor="<<q.get_device().get_info<sycl::info::device::vendor>()<<"\n"<<"driver="<<q.get_device().get_info<sycl::info::device::driver_version>()<<"\n"<<"precision="<<PRECISION_NAME<<"\n"<<"candidates="<<b.h.K<<"\n"<<"N="<<b.h.N<<"\n"<<"steps="<<a.steps<<"\n"<<"core_hat="<<b.h.core<<"\n"<<"cfl="<<b.h.cfl<<"\n";
        std::cout<<"device="<<q.get_device().get_info<sycl::info::device::name>()<<" candidates="<<b.h.K<<" N="<<b.h.N<<" steps="<<a.steps<<" precision="<<PRECISION_NAME<<"\n";return 0;
    }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 2;}
}
