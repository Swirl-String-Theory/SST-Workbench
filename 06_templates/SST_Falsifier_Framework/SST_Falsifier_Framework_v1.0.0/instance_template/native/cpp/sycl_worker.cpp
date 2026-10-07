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
constexpr uint32_t MAGIC_REQ=0x32545353,MAGIC_RES=0x32525353,VERSION=2,CMD_F32=2,CMD_F64=3,CMD_QUIT=9;
constexpr uint64_t MAX_INTERACTIONS=250000000ULL;
template<class T> bool read_exact(std::istream& s,T* p,size_t n=1){s.read(reinterpret_cast<char*>(p),sizeof(T)*n);return size_t(s.gcount())==sizeof(T)*n;}
template<class T> void write_exact(std::ostream& s,const T* p,size_t n=1){s.write(reinterpret_cast<const char*>(p),sizeof(T)*n);}
std::string esc(const std::string& s){std::string o;for(char c:s){if(c=='"'||c=='\\')o+='\\';if(c=='\n')o+="\\n";else o+=c;}return o;}
void err(uint64_t rid,uint32_t code,const std::string& msg){uint32_t m=MAGIC_RES,v=VERSION,dt=0;uint64_t n=msg.size(),kns=0;write_exact(std::cout,&m);write_exact(std::cout,&v);write_exact(std::cout,&code);write_exact(std::cout,&dt);write_exact(std::cout,&rid);write_exact(std::cout,&n);write_exact(std::cout,&kns);std::cout.write(msg.data(),msg.size());std::cout.flush();}
template<typename T,class K> uint64_t biot(sycl::queue& q,const std::vector<T>& p,uint64_t n,const std::vector<T>& x,uint64_t m,double gamma,double core,std::vector<T>& v){
  sycl::buffer<T,1> bp(p.data(),sycl::range<1>(p.size())),bx(x.data(),sycl::range<1>(x.size())),bv(v.data(),sycl::range<1>(v.size()));
  T scale=T(gamma/(4.0*3.141592653589793238462643383279502884)),a2=T(core*core);
  auto e=q.submit([&](sycl::handler& h){auto P=bp.template get_access<sycl::access::mode::read>(h);auto X=bx.template get_access<sycl::access::mode::read>(h);auto V=bv.template get_access<sycl::access::mode::write>(h);h.parallel_for<K>(sycl::range<1>(m),[=](sycl::id<1> id){uint64_t j=id[0];T vx=0,vy=0,vz=0;for(uint64_t s=0;s<n;++s){uint64_t t=(s+1)%n;T ax=P[3*s],ay=P[3*s+1],az=P[3*s+2],bx=P[3*t],by=P[3*t+1],bz=P[3*t+2];T dlx=bx-ax,dly=by-ay,dlz=bz-az,mx=T(.5)*(ax+bx),my=T(.5)*(ay+by),mz=T(.5)*(az+bz),rx=X[3*j]-mx,ry=X[3*j+1]-my,rz=X[3*j+2]-mz,D=rx*rx+ry*ry+rz*rz+a2,inv=T(1)/(D*sycl::sqrt(D));vx+=scale*(dly*rz-dlz*ry)*inv;vy+=scale*(dlz*rx-dlx*rz)*inv;vz+=scale*(dlx*ry-dly*rx)*inv;}V[3*j]=vx;V[3*j+1]=vy;V[3*j+2]=vz;});}); e.wait();
  uint64_t start=e.get_profiling_info<sycl::info::event_profiling::command_start>(),end=e.get_profiling_info<sycl::info::event_profiling::command_end>(); return end>start?end-start:0;
}
class K32; class K64;
int main(int argc,char** argv){try{sycl::device dev(sycl::gpu_selector_v);sycl::queue q(dev,sycl::property_list{sycl::property::queue::enable_profiling{}});auto name=dev.get_info<sycl::info::device::name>();bool fp64=dev.has(sycl::aspect::fp64);std::string info=std::string("{\"protocol_version\":2,\"device_name\":\"")+esc(name)+"\",\"is_gpu\":"+(dev.is_gpu()?"true":"false")+",\"fp64\":"+(fp64?"true":"false")+"}";if(argc>1&&std::string(argv[1])=="--probe"){std::cout<<info<<std::endl;return dev.is_gpu()?0:2;}
#ifdef _WIN32
_setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
std::cerr<<"SST_WORKER_READY "<<info<<std::endl;std::cerr.flush();for(;;){uint32_t magic=0,ver=0,cmd=0,res=0;uint64_t rid=0,n=0,m=0;double gamma=0,core=0;if(!read_exact(std::cin,&magic))break;if(!read_exact(std::cin,&ver)||!read_exact(std::cin,&cmd)||!read_exact(std::cin,&res)||!read_exact(std::cin,&rid))break;if(magic!=MAGIC_REQ||ver!=VERSION){err(rid,100,"bad magic/version");break;}if(cmd==CMD_QUIT)break;if(!read_exact(std::cin,&n)||!read_exact(std::cin,&m)||!read_exact(std::cin,&gamma)||!read_exact(std::cin,&core))break;if(n<3||m<1||n>100000||m>100000||n*m>MAX_INTERACTIONS||!std::isfinite(gamma)||!std::isfinite(core)||core<=0){err(rid,101,"invalid shape/work/core");continue;}try{if(cmd==CMD_F32){std::vector<float> p(3*n),x(3*m),v(3*m);if(!read_exact(std::cin,p.data(),p.size())||!read_exact(std::cin,x.data(),x.size()))break;uint64_t kns=biot<float,K32>(q,p,n,x,m,gamma,core,v);uint32_t om=MAGIC_RES,ov=VERSION,st=0,dt=1;uint64_t bytes=sizeof(float)*v.size();write_exact(std::cout,&om);write_exact(std::cout,&ov);write_exact(std::cout,&st);write_exact(std::cout,&dt);write_exact(std::cout,&rid);write_exact(std::cout,&bytes);write_exact(std::cout,&kns);write_exact(std::cout,v.data(),v.size());std::cout.flush();}else if(cmd==CMD_F64){if(!fp64){err(rid,102,"device has no native fp64");continue;}std::vector<double> p(3*n),x(3*m),v(3*m);if(!read_exact(std::cin,p.data(),p.size())||!read_exact(std::cin,x.data(),x.size()))break;uint64_t kns=biot<double,K64>(q,p,n,x,m,gamma,core,v);uint32_t om=MAGIC_RES,ov=VERSION,st=0,dt=2;uint64_t bytes=sizeof(double)*v.size();write_exact(std::cout,&om);write_exact(std::cout,&ov);write_exact(std::cout,&st);write_exact(std::cout,&dt);write_exact(std::cout,&rid);write_exact(std::cout,&bytes);write_exact(std::cout,&kns);write_exact(std::cout,v.data(),v.size());std::cout.flush();}else err(rid,103,"unknown command");}catch(const std::exception&e){err(rid,200,e.what());}}
return 0;}catch(const std::exception&e){std::cerr<<"SST_WORKER_FATAL "<<e.what()<<std::endl;return 3;}}
