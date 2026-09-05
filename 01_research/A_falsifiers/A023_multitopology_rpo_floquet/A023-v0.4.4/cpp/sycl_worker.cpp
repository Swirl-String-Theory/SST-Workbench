#include <sycl/sycl.hpp>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
#include <stdexcept>
#include <cmath>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif

static constexpr uint32_t MAGIC_REQ = 0x31545353u; // SST1
static constexpr uint32_t MAGIC_RES = 0x52545353u; // SSTR
static constexpr uint32_t CMD_F32 = 2u;
static constexpr uint32_t CMD_F64 = 3u;
static constexpr uint32_t CMD_QUIT = 9u;
static constexpr double PI = 3.141592653589793238462643383279502884;

class SstWorkerBiotFloatKernel;
class SstWorkerBiotDoubleKernel;

template<class T> static bool read_exact(std::istream& in, T* p, size_t n=1){
    in.read(reinterpret_cast<char*>(p), static_cast<std::streamsize>(sizeof(T)*n));
    return bool(in);
}
template<class T> static void write_exact(std::ostream& out, const T* p, size_t n=1){
    out.write(reinterpret_cast<const char*>(p), static_cast<std::streamsize>(sizeof(T)*n));
}
static void response_error(uint32_t status, const std::string& msg){
    uint32_t magic=MAGIC_RES; uint64_t bytes=static_cast<uint64_t>(msg.size());
    write_exact(std::cout,&magic); write_exact(std::cout,&status); write_exact(std::cout,&bytes);
    if(bytes) std::cout.write(msg.data(), static_cast<std::streamsize>(bytes));
    std::cout.flush();
}

template<class T, class KernelName>
static void biot_kernel(sycl::queue& q, const std::vector<T>& p, uint64_t n,
                        const std::vector<T>& x, uint64_t m, double gamma, double core,
                        std::vector<T>& out){
    const T s=T(gamma/(4.0*PI)); const T a2=T(core*core);
    sycl::buffer<T,1> P(const_cast<T*>(p.data()), sycl::range<1>(3*n));
    sycl::buffer<T,1> X(const_cast<T*>(x.data()), sycl::range<1>(3*m));
    sycl::buffer<T,1> V(out.data(), sycl::range<1>(3*m));
    q.submit([&](sycl::handler& h){
        auto P_=P.template get_access<sycl::access_mode::read>(h);
        auto X_=X.template get_access<sycl::access_mode::read>(h);
        auto V_=V.template get_access<sycl::access_mode::write>(h);
        h.parallel_for<KernelName>(sycl::range<1>(m), [=](sycl::id<1> ii){
            size_t i=ii[0];
            T xx=X_[3*i], yy=X_[3*i+1], zz=X_[3*i+2], vx=0,vy=0,vz=0;
            for(size_t j=0;j<n;++j){
                size_t k=(j+1)%n;
                T ax=P_[3*j], ay=P_[3*j+1], az=P_[3*j+2];
                T bx=P_[3*k], by=P_[3*k+1], bz=P_[3*k+2];
                T dlx=bx-ax,dly=by-ay,dlz=bz-az;
                T mx=T(.5)*(ax+bx),my=T(.5)*(ay+by),mz=T(.5)*(az+bz);
                T rx=xx-mx,ry=yy-my,rz=zz-mz;
                T D=rx*rx+ry*ry+rz*rz+a2;
                T inv=T(1)/(D*sycl::sqrt(D));
                vx += s*(dly*rz-dlz*ry)*inv;
                vy += s*(dlz*rx-dlx*rz)*inv;
                vz += s*(dlx*ry-dly*rx)*inv;
            }
            V_[3*i]=vx; V_[3*i+1]=vy; V_[3*i+2]=vz;
        });
    });
    q.wait_and_throw();
}

static std::string json_escape(const std::string& s){
    std::string o; o.reserve(s.size()+8);
    for(char c:s){ if(c=='\\' || c=='\"') {o.push_back('\\');o.push_back(c);} else if(c=='\n') o += "\\n"; else o.push_back(c); }
    return o;
}

int main(int argc, char** argv){
    try{
        sycl::device dev(sycl::gpu_selector_v);
        sycl::queue q(dev);
        const auto name=dev.get_info<sycl::info::device::name>();
        const bool fp64=dev.has(sycl::aspect::fp64);
        const std::string info = std::string("{\"device_name\":\"")+json_escape(name)+
            "\",\"is_gpu\":"+(dev.is_gpu()?"true":"false")+
            ",\"fp64\":"+(fp64?"true":"false")+
            ",\"backend\":\"level_zero_or_selected_sycl\"}";
        if(argc>1 && std::string(argv[1])=="--probe"){
            std::cout << info << std::endl;
            return dev.is_gpu()?0:2;
        }
#ifdef _WIN32
        _setmode(_fileno(stdin), _O_BINARY);
        _setmode(_fileno(stdout), _O_BINARY);
#endif
        std::cerr << "SST_WORKER_READY " << info << std::endl;
        std::cerr.flush();
        for(;;){
            uint32_t magic=0,cmd=0; uint64_t n=0,m=0; double gamma=0,core=0;
            if(!read_exact(std::cin,&magic)) break;
            if(magic!=MAGIC_REQ){ response_error(100,"bad request magic"); break; }
            if(!read_exact(std::cin,&cmd)) break;
            if(cmd==CMD_QUIT) break;
            if(!read_exact(std::cin,&n)||!read_exact(std::cin,&m)||!read_exact(std::cin,&gamma)||!read_exact(std::cin,&core)) break;
            if(n<3 || m<1 || n>100000 || m>100000){ response_error(101,"invalid shape"); continue; }
            try{
                if(cmd==CMD_F32){
                    std::vector<float> p(3*n),x(3*m),v(3*m);
                    if(!read_exact(std::cin,p.data(),p.size())||!read_exact(std::cin,x.data(),x.size())) break;
                    biot_kernel<float,SstWorkerBiotFloatKernel>(q,p,n,x,m,gamma,core,v);
                    uint32_t om=MAGIC_RES, st=0; uint64_t bytes=sizeof(float)*v.size();
                    write_exact(std::cout,&om);write_exact(std::cout,&st);write_exact(std::cout,&bytes);write_exact(std::cout,v.data(),v.size());std::cout.flush();
                }else if(cmd==CMD_F64){
                    if(!fp64){ response_error(102,"device has no native fp64"); continue; }
                    std::vector<double> p(3*n),x(3*m),v(3*m);
                    if(!read_exact(std::cin,p.data(),p.size())||!read_exact(std::cin,x.data(),x.size())) break;
                    biot_kernel<double,SstWorkerBiotDoubleKernel>(q,p,n,x,m,gamma,core,v);
                    uint32_t om=MAGIC_RES, st=0; uint64_t bytes=sizeof(double)*v.size();
                    write_exact(std::cout,&om);write_exact(std::cout,&st);write_exact(std::cout,&bytes);write_exact(std::cout,v.data(),v.size());std::cout.flush();
                }else response_error(103,"unknown command");
            }catch(const std::exception& e){ response_error(200,e.what()); }
        }
        return 0;
    }catch(const std::exception& e){ std::cerr << "SST_WORKER_FATAL " << e.what() << std::endl; return 3; }
}
