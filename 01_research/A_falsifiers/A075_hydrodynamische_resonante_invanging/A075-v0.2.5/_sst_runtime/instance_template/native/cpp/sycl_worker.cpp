#include <sycl/sycl.hpp>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <iomanip>
#include <vector>
#include <string>
#include <stdexcept>
#include <cmath>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

constexpr uint32_t MAGIC_REQ=0x32545353,MAGIC_RES=0x32525353,VERSION=3,
                   CMD_F32=2,CMD_F64=3,CMD_DD32=4,CMD_QUIT=9;
constexpr uint64_t MAX_INTERACTIONS=250000000ULL;
constexpr double INV4PI_D=0.079577471545947667884441881686257181;

template<class T> bool read_exact(std::istream& s,T* p,size_t n=1){s.read(reinterpret_cast<char*>(p),sizeof(T)*n);return size_t(s.gcount())==sizeof(T)*n;}
template<class T> void write_exact(std::ostream& s,const T* p,size_t n=1){s.write(reinterpret_cast<const char*>(p),sizeof(T)*n);}
std::string esc(const std::string& s){std::string o;for(char c:s){if(c=='"'||c=='\\')o+='\\';if(c=='\n')o+="\\n";else o+=c;}return o;}
void err(uint64_t rid,uint32_t code,const std::string& msg){uint32_t m=MAGIC_RES,v=VERSION,dt=0;uint64_t n=msg.size(),kns=0;write_exact(std::cout,&m);write_exact(std::cout,&v);write_exact(std::cout,&code);write_exact(std::cout,&dt);write_exact(std::cout,&rid);write_exact(std::cout,&n);write_exact(std::cout,&kns);std::cout.write(msg.data(),msg.size());std::cout.flush();}

// DD32 / FP32x2 double-single arithmetic. This is not IEEE binary64: the
// exponent range remains binary32 and the nominal significand capacity is ~48 bits.
struct DS{float hi,lo;};
inline DS ds_from_float(float a){return DS{a,0.0f};}
inline DS ds_neg(DS a){return DS{-a.hi,-a.lo};}
inline DS ds_split_host(double x){float h=static_cast<float>(x);float l=static_cast<float>(x-static_cast<double>(h));return DS{h,l};}
inline DS ds_quick_two_sum(float a,float b){float s=a+b;float e=b-(s-a);return DS{s,e};}
inline DS ds_two_sum(float a,float b){float s=a+b;float bb=s-a;float e=(a-(s-bb))+(b-bb);return DS{s,e};}
inline DS ds_add(DS a,DS b){DS t=ds_two_sum(a.hi,b.hi);float e=t.lo+(a.lo+b.lo);return ds_quick_two_sum(t.hi,e);}
inline DS ds_sub(DS a,DS b){return ds_add(a,ds_neg(b));}
inline DS ds_mul(DS a,DS b){
    float p=a.hi*b.hi;
    float e=sycl::fma(a.hi,b.hi,-p);
    e += a.hi*b.lo + a.lo*b.hi;
    e += a.lo*b.lo;
    return ds_quick_two_sum(p,e);
}
inline DS ds_div(DS a,DS b){
    DS q=ds_from_float(a.hi/b.hi);
    for(int k=0;k<3;++k){DS r=ds_sub(a,ds_mul(b,q));float qi=(r.hi+r.lo)/b.hi;q=ds_add(q,ds_from_float(qi));}
    return q;
}
inline DS ds_sqrt(DS a){
    float seed=sycl::sqrt(a.hi+a.lo);DS y=ds_from_float(seed);DS two=ds_from_float(2.0f);
    for(int k=0;k<2;++k){DS r=ds_sub(a,ds_mul(y,y));DS corr=ds_div(r,ds_mul(two,y));y=ds_add(y,corr);}
    return y;
}

template<typename T,class K> uint64_t biot(sycl::queue& q,const std::vector<T>& p,uint64_t n,const std::vector<T>& x,uint64_t m,double gamma,double core,std::vector<T>& v){
  sycl::buffer<T,1> bp(p.data(),sycl::range<1>(p.size())),bx(x.data(),sycl::range<1>(x.size())),bv(v.data(),sycl::range<1>(v.size()));
  T scale=T(gamma*INV4PI_D),a2=T(core*core);
  auto e=q.submit([&](sycl::handler& h){auto P=bp.template get_access<sycl::access::mode::read>(h);auto X=bx.template get_access<sycl::access::mode::read>(h);auto V=bv.template get_access<sycl::access::mode::write>(h);h.parallel_for<K>(sycl::range<1>(m),[=](sycl::id<1> id){uint64_t j=id[0];T vx=0,vy=0,vz=0;for(uint64_t s=0;s<n;++s){uint64_t t=(s+1)%n;T ax=P[3*s],ay=P[3*s+1],az=P[3*s+2],bx=P[3*t],by=P[3*t+1],bz=P[3*t+2];T dlx=bx-ax,dly=by-ay,dlz=bz-az,mx=T(.5)*(ax+bx),my=T(.5)*(ay+by),mz=T(.5)*(az+bz),rx=X[3*j]-mx,ry=X[3*j+1]-my,rz=X[3*j+2]-mz,D=rx*rx+ry*ry+rz*rz+a2,inv=T(1)/(D*sycl::sqrt(D));vx+=scale*(dly*rz-dlz*ry)*inv;vy+=scale*(dlz*rx-dlx*rz)*inv;vz+=scale*(dlx*ry-dly*rx)*inv;}V[3*j]=vx;V[3*j+1]=vy;V[3*j+2]=vz;});}); e.wait();
  uint64_t start=e.template get_profiling_info<sycl::info::event_profiling::command_start>(),end=e.template get_profiling_info<sycl::info::event_profiling::command_end>(); return end>start?end-start:0;
}

class KDD32;
uint64_t biot_dd32(sycl::queue& q,const std::vector<double>& p64,uint64_t n,const std::vector<double>& x64,uint64_t m,double gamma,double core,std::vector<double>& out){
  std::vector<DS> p(p64.size()),x(x64.size()),v(3*m);
  for(size_t i=0;i<p64.size();++i)p[i]=ds_split_host(p64[i]);
  for(size_t i=0;i<x64.size();++i)x[i]=ds_split_host(x64[i]);
  DS g=ds_split_host(gamma),inv4pi=ds_split_host(INV4PI_D),scale=ds_mul(g,inv4pi),c=ds_split_host(core),a2=ds_mul(c,c),half=ds_from_float(0.5f),one=ds_from_float(1.0f);
  uint64_t start=0,end=0;
  {
    sycl::buffer<DS,1> bp(p.data(),sycl::range<1>(p.size())),bx(x.data(),sycl::range<1>(x.size())),bv(v.data(),sycl::range<1>(v.size()));
    auto e=q.submit([&](sycl::handler& h){
      auto P=bp.template get_access<sycl::access::mode::read>(h);auto X=bx.template get_access<sycl::access::mode::read>(h);auto V=bv.template get_access<sycl::access::mode::write>(h);
      h.parallel_for<KDD32>(sycl::range<1>(m),[=](sycl::id<1> id){
        uint64_t j=id[0];DS vx=ds_from_float(0.0f),vy=ds_from_float(0.0f),vz=ds_from_float(0.0f);
        for(uint64_t s=0;s<n;++s){
          uint64_t t=(s+1)%n;
          DS ax=P[3*s],ay=P[3*s+1],az=P[3*s+2],bbx=P[3*t],bby=P[3*t+1],bbz=P[3*t+2];
          DS dlx=ds_sub(bbx,ax),dly=ds_sub(bby,ay),dlz=ds_sub(bbz,az);
          DS mx=ds_mul(half,ds_add(ax,bbx)),my=ds_mul(half,ds_add(ay,bby)),mz=ds_mul(half,ds_add(az,bbz));
          DS rx=ds_sub(X[3*j],mx),ry=ds_sub(X[3*j+1],my),rz=ds_sub(X[3*j+2],mz);
          DS D=ds_add(ds_add(ds_mul(rx,rx),ds_mul(ry,ry)),ds_add(ds_mul(rz,rz),a2));
          DS inv=ds_div(one,ds_mul(D,ds_sqrt(D)));
          DS cx=ds_sub(ds_mul(dly,rz),ds_mul(dlz,ry));
          DS cy=ds_sub(ds_mul(dlz,rx),ds_mul(dlx,rz));
          DS cz=ds_sub(ds_mul(dlx,ry),ds_mul(dly,rx));
          DS f=ds_mul(scale,inv);
          vx=ds_add(vx,ds_mul(f,cx));vy=ds_add(vy,ds_mul(f,cy));vz=ds_add(vz,ds_mul(f,cz));
        }
        V[3*j]=vx;V[3*j+1]=vy;V[3*j+2]=vz;
      });
    });
    e.wait();
    start=e.get_profiling_info<sycl::info::event_profiling::command_start>();
    end=e.get_profiling_info<sycl::info::event_profiling::command_end>();
  } // buffer destructors copy DD32 results back to host vector v
  out.resize(3*m);for(size_t i=0;i<v.size();++i)out[i]=static_cast<double>(v[i].hi)+static_cast<double>(v[i].lo);
  return end>start?end-start:0;
}

class K32; class K64;
int main(int argc,char** argv){try{
  sycl::device dev(sycl::gpu_selector_v);sycl::queue q(dev,sycl::property_list{sycl::property::queue::enable_profiling{}});auto name=dev.get_info<sycl::info::device::name>();bool fp64=dev.has(sycl::aspect::fp64);
  std::string info=std::string("{\"protocol_version\":3,\"device_name\":\"")+esc(name)+"\",\"is_gpu\":"+(dev.is_gpu()?"true":"false")+",\"fp64\":"+(fp64?"true":"false")+",\"dd32\":true,\"dd32_nominal_significand_bits\":48}";
  if(argc>1&&std::string(argv[1])=="--probe"){std::cout<<info<<std::endl;return dev.is_gpu()?0:2;}
#ifdef _WIN32
  _setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
  std::cerr<<"SST_WORKER_READY "<<info<<std::endl;std::cerr.flush();
  for(;;){
    uint32_t magic=0,ver=0,cmd=0,res=0;uint64_t rid=0,n=0,m=0;double gamma=0,core=0;
    if(!read_exact(std::cin,&magic))break;if(!read_exact(std::cin,&ver)||!read_exact(std::cin,&cmd)||!read_exact(std::cin,&res)||!read_exact(std::cin,&rid))break;
    if(magic!=MAGIC_REQ||ver!=VERSION){err(rid,100,"bad magic/version");break;}if(cmd==CMD_QUIT)break;
    if(!read_exact(std::cin,&n)||!read_exact(std::cin,&m)||!read_exact(std::cin,&gamma)||!read_exact(std::cin,&core))break;
    if(n<3||m<1||n>100000||m>100000||n*m>MAX_INTERACTIONS||!std::isfinite(gamma)||!std::isfinite(core)||core<=0){err(rid,101,"invalid shape/work/core");continue;}
    try{
      if(cmd==CMD_F32){
        std::vector<float> p(3*n),x(3*m),v(3*m);if(!read_exact(std::cin,p.data(),p.size())||!read_exact(std::cin,x.data(),x.size()))break;
        uint64_t kns=biot<float,K32>(q,p,n,x,m,gamma,core,v);uint32_t om=MAGIC_RES,ov=VERSION,st=0,dt=1;uint64_t bytes=sizeof(float)*v.size();write_exact(std::cout,&om);write_exact(std::cout,&ov);write_exact(std::cout,&st);write_exact(std::cout,&dt);write_exact(std::cout,&rid);write_exact(std::cout,&bytes);write_exact(std::cout,&kns);write_exact(std::cout,v.data(),v.size());std::cout.flush();
      }else if(cmd==CMD_F64){
        if(!fp64){err(rid,102,"device has no native fp64");continue;}std::vector<double> p(3*n),x(3*m),v(3*m);if(!read_exact(std::cin,p.data(),p.size())||!read_exact(std::cin,x.data(),x.size()))break;
        uint64_t kns=biot<double,K64>(q,p,n,x,m,gamma,core,v);uint32_t om=MAGIC_RES,ov=VERSION,st=0,dt=2;uint64_t bytes=sizeof(double)*v.size();write_exact(std::cout,&om);write_exact(std::cout,&ov);write_exact(std::cout,&st);write_exact(std::cout,&dt);write_exact(std::cout,&rid);write_exact(std::cout,&bytes);write_exact(std::cout,&kns);write_exact(std::cout,v.data(),v.size());std::cout.flush();
      }else if(cmd==CMD_DD32){
        std::vector<double> p(3*n),x(3*m),v;if(!read_exact(std::cin,p.data(),p.size())||!read_exact(std::cin,x.data(),x.size()))break;
        uint64_t kns=biot_dd32(q,p,n,x,m,gamma,core,v);uint32_t om=MAGIC_RES,ov=VERSION,st=0,dt=3;uint64_t bytes=sizeof(double)*v.size();write_exact(std::cout,&om);write_exact(std::cout,&ov);write_exact(std::cout,&st);write_exact(std::cout,&dt);write_exact(std::cout,&rid);write_exact(std::cout,&bytes);write_exact(std::cout,&kns);write_exact(std::cout,v.data(),v.size());std::cout.flush();
      }else err(rid,103,"unknown command");
    }catch(const std::exception&e){err(rid,200,e.what());}
  }
  return 0;
}catch(const std::exception&e){std::cerr<<"SST_WORKER_FATAL "<<e.what()<<std::endl;return 3;}}
