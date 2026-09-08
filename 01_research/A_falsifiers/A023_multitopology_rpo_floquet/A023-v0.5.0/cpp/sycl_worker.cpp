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
static constexpr uint32_t CMD_F32  = 2u;
static constexpr uint32_t CMD_F64  = 3u;
static constexpr uint32_t CMD_DD32 = 4u;  // FP32x2 / double-single arithmetic
static constexpr uint32_t CMD_QUIT = 9u;
static constexpr double PI = 3.141592653589793238462643383279502884;

class SstWorkerBiotFloatKernel;
class SstWorkerBiotDoubleKernel;
class SstWorkerBiotDD32Kernel;

// -----------------------------------------------------------------------------
// FP32x2 arithmetic (often called double-single arithmetic).
// A value is represented as hi + lo with two IEEE-754 binary32 numbers.
// This is NOT IEEE binary64: ideal significand capacity is ~48 bits and the
// observed accuracy must be validated against the CPU FP64 reference.
// -----------------------------------------------------------------------------
struct DS {
    float hi;
    float lo;
};

static inline DS ds_make(float x) { return DS{x, 0.0f}; }
static inline DS ds_neg(DS a) { return DS{-a.hi, -a.lo}; }

static inline DS two_sum(float a, float b) {
    float s = a + b;
    float bb = s - a;
    float e = (a - (s - bb)) + (b - bb);
    return DS{s, e};
}

static inline DS quick_two_sum(float a, float b) {
    float s = a + b;
    float e = b - (s - a);
    return DS{s, e};
}

static inline DS two_prod(float a, float b) {
    float p = a * b;
    // FMA gives the exact residual of the rounded binary32 product when the
    // hardware/runtime implements IEEE fused multiply-add semantics.
    float e = sycl::fma(a, b, -p);
    return DS{p, e};
}

static inline DS ds_add(DS a, DS b) {
    // Knuth-style compensated addition followed by renormalization.
    float s1 = a.hi + b.hi;
    float v  = s1 - a.hi;
    float s2 = ((b.hi - v) + (a.hi - (s1 - v))) + a.lo + b.lo;
    return two_sum(s1, s2);
}

static inline DS ds_sub(DS a, DS b) { return ds_add(a, ds_neg(b)); }

static inline DS ds_mul(DS a, DS b) {
    // Keep the exact hi*hi residual and both cross terms.  The lo*lo term is
    // below the leading product by ~48 bits but is cheap and improves edge cases.
    DS p = two_prod(a.hi, b.hi);
    DS c1 = two_prod(a.hi, b.lo);
    DS c2 = two_prod(a.lo, b.hi);
    DS c3 = two_prod(a.lo, b.lo);
    return ds_add(ds_add(p, c1), ds_add(c2, c3));
}

static inline DS ds_mul_float(DS a, float b) { return ds_mul(a, ds_make(b)); }

static inline DS ds_div(DS a, DS b) {
    // Three quotient corrections.  q1 captures the leading binary32 quotient;
    // q2/q3 recover the low part using DD residuals.
    float q1 = a.hi / b.hi;
    DS q = ds_make(q1);
    DS r = ds_sub(a, ds_mul(b, q));
    float q2 = (r.hi + r.lo) / b.hi;
    q = ds_add(q, ds_make(q2));
    r = ds_sub(a, ds_mul(b, q));
    float q3 = (r.hi + r.lo) / b.hi;
    return ds_add(q, ds_make(q3));
}

static inline DS ds_recip(DS a) { return ds_div(ds_make(1.0f), a); }

static inline DS ds_sqrt(DS a) {
    // Newton correction around a binary32 sqrt seed.  Two DD iterations are
    // used because the surrounding Biot-Savart denominator is sensitivity-heavy.
    float seed = sycl::sqrt(a.hi);
    DS y = ds_make(seed);
    for (int it = 0; it < 2; ++it) {
        DS r = ds_sub(a, ds_mul(y, y));
        DS den = ds_mul_float(y, 2.0f);
        y = ds_add(y, ds_div(r, den));
    }
    return y;
}

static inline DS ds_from_split(float hi, float lo) { return DS{hi, lo}; }

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

static inline DS split_double_host(double x) {
    float hi = static_cast<float>(x);
    float lo = static_cast<float>(x - static_cast<double>(hi));
    return DS{hi, lo};
}

static void biot_kernel_dd32(sycl::queue& q,
                             const std::vector<double>& p64, uint64_t n,
                             const std::vector<double>& x64, uint64_t m,
                             double gamma, double core,
                             std::vector<double>& out64) {
    std::vector<float> ph(3*n), pl(3*n), xh(3*m), xl(3*m);
    for (size_t i=0;i<ph.size();++i) { DS z=split_double_host(p64[i]); ph[i]=z.hi; pl[i]=z.lo; }
    for (size_t i=0;i<xh.size();++i) { DS z=split_double_host(x64[i]); xh[i]=z.hi; xl[i]=z.lo; }
    std::vector<float> vh(3*m,0.0f), vl(3*m,0.0f);
    DS s_h = split_double_host(gamma/(4.0*PI));
    DS a2_h = split_double_host(core*core);
    const float s_hi=s_h.hi, s_lo=s_h.lo, a2_hi=a2_h.hi, a2_lo=a2_h.lo;

    {
        sycl::buffer<float,1> PH(ph.data(), sycl::range<1>(3*n));
        sycl::buffer<float,1> PL(pl.data(), sycl::range<1>(3*n));
        sycl::buffer<float,1> XH(xh.data(), sycl::range<1>(3*m));
        sycl::buffer<float,1> XL(xl.data(), sycl::range<1>(3*m));
        sycl::buffer<float,1> VH(vh.data(), sycl::range<1>(3*m));
        sycl::buffer<float,1> VL(vl.data(), sycl::range<1>(3*m));
    
        q.submit([&](sycl::handler& h){
            auto ph_=PH.get_access<sycl::access_mode::read>(h);
            auto pl_=PL.get_access<sycl::access_mode::read>(h);
            auto xh_=XH.get_access<sycl::access_mode::read>(h);
            auto xl_=XL.get_access<sycl::access_mode::read>(h);
            auto vh_=VH.get_access<sycl::access_mode::write>(h);
            auto vl_=VL.get_access<sycl::access_mode::write>(h);
            h.parallel_for<SstWorkerBiotDD32Kernel>(sycl::range<1>(m), [=](sycl::id<1> ii){
                const size_t i=ii[0];
                DS xx=ds_from_split(xh_[3*i],xl_[3*i]);
                DS yy=ds_from_split(xh_[3*i+1],xl_[3*i+1]);
                DS zz=ds_from_split(xh_[3*i+2],xl_[3*i+2]);
                DS vx=ds_make(0.0f), vy=ds_make(0.0f), vz=ds_make(0.0f);
                const DS s=ds_from_split(s_hi,s_lo);
                const DS a2=ds_from_split(a2_hi,a2_lo);
                for(size_t j=0;j<n;++j){
                    const size_t k=(j+1)%n;
                    DS ax=ds_from_split(ph_[3*j],pl_[3*j]);
                    DS ay=ds_from_split(ph_[3*j+1],pl_[3*j+1]);
                    DS az=ds_from_split(ph_[3*j+2],pl_[3*j+2]);
                    DS bx=ds_from_split(ph_[3*k],pl_[3*k]);
                    DS by=ds_from_split(ph_[3*k+1],pl_[3*k+1]);
                    DS bz=ds_from_split(ph_[3*k+2],pl_[3*k+2]);
                    DS dlx=ds_sub(bx,ax), dly=ds_sub(by,ay), dlz=ds_sub(bz,az);
                    DS mx=ds_mul_float(ds_add(ax,bx),0.5f);
                    DS my=ds_mul_float(ds_add(ay,by),0.5f);
                    DS mz=ds_mul_float(ds_add(az,bz),0.5f);
                    DS rx=ds_sub(xx,mx), ry=ds_sub(yy,my), rz=ds_sub(zz,mz);
                    DS D=ds_add(ds_add(ds_mul(rx,rx),ds_mul(ry,ry)),ds_add(ds_mul(rz,rz),a2));
                    DS root=ds_sqrt(D);
                    DS inv=ds_recip(ds_mul(D,root));
                    DS cx=ds_sub(ds_mul(dly,rz),ds_mul(dlz,ry));
                    DS cy=ds_sub(ds_mul(dlz,rx),ds_mul(dlx,rz));
                    DS cz=ds_sub(ds_mul(dlx,ry),ds_mul(dly,rx));
                    DS scale=ds_mul(s,inv);
                    vx=ds_add(vx,ds_mul(scale,cx));
                    vy=ds_add(vy,ds_mul(scale,cy));
                    vz=ds_add(vz,ds_mul(scale,cz));
                }
                vh_[3*i]=vx.hi; vl_[3*i]=vx.lo;
                vh_[3*i+1]=vy.hi; vl_[3*i+1]=vy.lo;
                vh_[3*i+2]=vz.hi; vl_[3*i+2]=vz.lo;
            });
        });
        q.wait_and_throw();
    }
    for (size_t i=0;i<out64.size();++i) out64[i]=static_cast<double>(vh[i])+static_cast<double>(vl[i]);
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
            ",\"dd32\":true,\"dd32_bits_nominal\":48,\"backend\":\"level_zero_or_selected_sycl\"}";
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
                }else if(cmd==CMD_DD32){
                    // Host transport is FP64; the worker splits each value into two
                    // binary32 components before launching a float-only device kernel.
                    std::vector<double> p(3*n),x(3*m),v(3*m);
                    if(!read_exact(std::cin,p.data(),p.size())||!read_exact(std::cin,x.data(),x.size())) break;
                    biot_kernel_dd32(q,p,n,x,m,gamma,core,v);
                    uint32_t om=MAGIC_RES, st=0; uint64_t bytes=sizeof(double)*v.size();
                    write_exact(std::cout,&om);write_exact(std::cout,&st);write_exact(std::cout,&bytes);write_exact(std::cout,v.data(),v.size());std::cout.flush();
                }else response_error(103,"unknown command");
            }catch(const std::exception& e){ response_error(200,e.what()); }
        }
        return 0;
    }catch(const std::exception& e){ std::cerr << "SST_WORKER_FATAL " << e.what() << std::endl; return 3; }
}
