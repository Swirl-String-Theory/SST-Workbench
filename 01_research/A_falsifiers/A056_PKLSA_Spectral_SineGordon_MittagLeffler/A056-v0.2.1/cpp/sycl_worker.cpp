#include <sycl/sycl.hpp>
#include <iostream>
#include <iomanip>
#include <cmath>
#include <cstring>
#include <string>
#include <algorithm>

struct DS { float hi, lo; };

static inline DS two_sum(float a, float b){
    float s=a+b;
    float bb=s-a;
    float e=(a-(s-bb))+(b-bb);
    return {s,e};
}
static inline DS quick_two_sum(float a, float b){
    float s=a+b;
    float e=b-(s-a);
    return {s,e};
}
static inline DS ds_add(DS a, DS b){
    DS s=two_sum(a.hi,b.hi);
    float e=s.lo+a.lo+b.lo;
    return quick_two_sum(s.hi,e);
}
static inline DS two_prod(float a,float b){
    float p=a*b;
    float e=sycl::fma(a,b,-p);
    return {p,e};
}
static inline DS ds_mul(DS a,DS b){
    DS p=two_prod(a.hi,b.hi);
    float e=p.lo + a.hi*b.lo + a.lo*b.hi + a.lo*b.lo;
    return quick_two_sum(p.hi,e);
}

int main(int argc,char** argv){
  try{
    sycl::queue q{sycl::default_selector_v};
    auto d=q.get_device();
    const bool fp64=d.has(sycl::aspect::fp64);
    const bool ddtest = argc>1 && std::string(argv[1])=="--dd32-selftest";
    if(!ddtest){
      std::cout << "{\"status\":\"PASS\",\"device\":\"" << d.get_info<sycl::info::device::name>()
                << "\",\"fp64\":" << (fp64?"true":"false") << ",\"backend\":\"sycl-worker\"}" << std::endl;
      return 0;
    }

    constexpr int N=4096;
    float* hi=sycl::malloc_shared<float>(N,q);
    float* lo=sycl::malloc_shared<float>(N,q);
    float* out=sycl::malloc_shared<float>(3,q);
    if(!hi||!lo||!out) throw std::runtime_error("USM allocation failed");
    long double ref=0.0L;
    for(int k=0;k<N/2;++k){
      double eps=std::ldexp(1.0,-30)*(1.0+0.01*double(k%7));
      double a=1.0+eps, b=-1.0;
      float ah=(float)a, bh=(float)b;
      hi[2*k]=ah; lo[2*k]=(float)(a-(double)ah);
      hi[2*k+1]=bh; lo[2*k+1]=(float)(b-(double)bh);
      ref+=(long double)a+(long double)b;
    }
    q.single_task([=](){
      float sf=0.0f; DS sd{0.0f,0.0f};
      for(int i=0;i<N;++i){
        sf += hi[i];
        sd=ds_add(sd,DS{hi[i],lo[i]});
      }
      out[0]=sf; out[1]=sd.hi; out[2]=sd.lo;
    }).wait();
    const double fp32=(double)out[0];
    const double dd32=(double)out[1]+(double)out[2];
    const double refd=(double)ref;
    const double floor=1e-300;
    const double e32=std::abs(fp32-refd)/std::max(std::abs(refd),floor);
    const double edd=std::abs(dd32-refd)/std::max(std::abs(refd),floor);
    const double imp=e32/std::max(edd,1e-30);
    const bool pass=edd<=1e-8 && imp>=20.0;
    std::cout<<std::setprecision(17)
      <<"{\"status\":\""<<(pass?"PASS":"FAIL")
      <<"\",\"device\":\""<<d.get_info<sycl::info::device::name>()
      <<"\",\"fp64\":"<<(fp64?"true":"false")
      <<",\"precision\":\"DD32-FP32x2-not-IEEE-FP64\""
      <<",\"reference\":"<<refd
      <<",\"fp32\":"<<fp32
      <<",\"dd32\":"<<dd32
      <<",\"fp32_relative_error\":"<<e32
      <<",\"dd32_relative_error\":"<<edd
      <<",\"improvement_factor\":"<<imp
      <<",\"dd32_relative_limit\":1e-8,\"min_improvement\":20.0}"<<std::endl;
    sycl::free(hi,q); sycl::free(lo,q); sycl::free(out,q);
    return pass?0:3;
  }catch(const std::exception& e){
    std::cerr<<"{\"status\":\"FAIL\",\"error\":\""<<e.what()<<"\"}"<<std::endl;
    return 2;
  }
}
