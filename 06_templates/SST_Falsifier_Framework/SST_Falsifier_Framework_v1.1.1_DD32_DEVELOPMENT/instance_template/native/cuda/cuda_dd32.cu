// SST DD32 CUDA prototype. NO device double arithmetic; keep fast-math disabled.
// Build for Pascal (GTX 1060) with nvcc 12.6 -arch=sm_61.
// Binary input: 8-byte ASCII magic SSTDD321, uint32 countP,countQ,
// float64 gamma,core, followed by float64 XYZ vertices and XYZ queries.
// Binary output: countQ * 3 little-endian float64 values, assembled on host
// from CUDA double-single (hi,lo) outputs. Strictly a numerical diagnostic.
#include <cuda_runtime.h>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <vector>

struct DS { float hi,lo; };
__host__ inline DS split_host(double x) {
    float h=static_cast<float>(x); return {h,static_cast<float>(x-static_cast<double>(h))};
}
__device__ __forceinline__ DS two_sum(float a,float b) {
    float s=a+b,bb=s-a,e=(a-(s-bb))+(b-bb);return {s,e};
}
__device__ __forceinline__ DS quick_two_sum(float a,float b) {
    float s=a+b; return {s,b-(s-a)};
}
__device__ __forceinline__ DS ds_add(DS a,DS b) {
    DS t=two_sum(a.hi,b.hi);return quick_two_sum(t.hi,t.lo+(a.lo+b.lo));
}
__device__ __forceinline__ DS ds_neg(DS a) {return {-a.hi,-a.lo};}
__device__ __forceinline__ DS ds_sub(DS a,DS b) {return ds_add(a,ds_neg(b));}
__device__ __forceinline__ DS ds_mul(DS a,DS b) {
    float p=a.hi*b.hi;
    float e=fmaf(a.hi,b.hi,-p);  // Explicit product residual: FMA is mandatory.
    e+=a.hi*b.lo+a.lo*b.hi;
    e+=a.lo*b.lo;
    return quick_two_sum(p,e);
}
__device__ __forceinline__ DS ds_div(DS a,DS b) {
    DS q={a.hi/b.hi,0.0f};
#pragma unroll
    for(int i=0;i<3;i++) {
        DS r=ds_sub(a,ds_mul(b,q));
        DS correction={(r.hi+r.lo)/b.hi,0.0f};
        q=ds_add(q,correction);
    }
    return q;
}
__device__ __forceinline__ DS ds_sqrt(DS a) {
    DS y={sqrtf(a.hi+a.lo),0.0f};
    const DS two={2.0f,0.0f};
#pragma unroll
    for(int i=0;i<2;i++) {
        DS r=ds_sub(a,ds_mul(y,y));
        y=ds_add(y,ds_div(r,ds_mul(two,y)));
    }
    return y;
}
__device__ __forceinline__ DS component(const DS* p, unsigned index, unsigned k) {
    return p[3ull*index+k];
}
__global__ void biot_savart_dd32(const DS* pts,const DS* queries,DS* out,
    unsigned np,unsigned nq,DS scale,DS core2) {
    unsigned iq=blockIdx.x*blockDim.x+threadIdx.x;
    if(iq>=nq)return;
    const DS half={0.5f,0.0f},one={1.0f,0.0f};
    DS x[3]={component(queries,iq,0),component(queries,iq,1),component(queries,iq,2)};
    DS sum[3]={{0,0},{0,0},{0,0}};
    for(unsigned j=0;j<np;j++) {
        unsigned next=(j+1==np)?0:j+1;
        DS dl[3],r[3];
#pragma unroll
        for(unsigned k=0;k<3;k++) {
            DS a=component(pts,j,k),b=component(pts,next,k);
            dl[k]=ds_sub(b,a);
            DS mid=ds_mul(half,ds_add(a,b));
            r[k]=ds_sub(x[k],mid);
        }
        DS norm=ds_add(ds_add(ds_mul(r[0],r[0]),ds_mul(r[1],r[1])),
                       ds_add(ds_mul(r[2],r[2]),core2));
        DS fac=ds_mul(scale,ds_div(one,ds_mul(norm,ds_sqrt(norm))));
        DS cross[3]={ds_sub(ds_mul(dl[1],r[2]),ds_mul(dl[2],r[1])),
                     ds_sub(ds_mul(dl[2],r[0]),ds_mul(dl[0],r[2])),
                     ds_sub(ds_mul(dl[0],r[1]),ds_mul(dl[1],r[0]))};
#pragma unroll
        for(unsigned k=0;k<3;k++) sum[k]=ds_add(sum[k],ds_mul(fac,cross[k]));
    }
#pragma unroll
    for(unsigned k=0;k<3;k++) out[3ull*iq+k]=sum[k];
}
static void require_cuda(cudaError_t code,const char* where) {
    if(code!=cudaSuccess){std::cerr<<where<<": "<<cudaGetErrorString(code)<<"\n";std::exit(3);}
}
static int probe() {
    int count=0;require_cuda(cudaGetDeviceCount(&count),"get_device_count");
    if(!count){std::cerr<<"No CUDA devices\n";return 4;}
    cudaDeviceProp prop{}; require_cuda(cudaGetDeviceProperties(&prop,0),"get_device_properties");
    std::cout<<"{\"available\":true,\"device_type\":\"cuda\",\"device_name\":\"";
    for(char c:std::string(prop.name)){if(c=='"'||c=='\\')std::cout<<'\\';std::cout<<c;}
    std::cout<<"\",\"compute_capability\":\""<<prop.major<<"."<<prop.minor<<"\"}\n";
    return 0;
}
template<class T> static void read_exact(std::ifstream& f,T& dst) {
    if(!f.read(reinterpret_cast<char*>(&dst),sizeof(dst))) throw std::runtime_error("Truncated binary header");
}
static int run(const char* input,const char* output) {
    std::ifstream f(input,std::ios::binary);if(!f)throw std::runtime_error("Missing binary input");
    char magic[8];if(!f.read(magic,8)||std::memcmp(magic,"SSTDD321",8)!=0)throw std::runtime_error("Invalid SSTDD321 magic");
    uint32_t np,nq;double gamma,core;
    read_exact(f,np);read_exact(f,nq);read_exact(f,gamma);read_exact(f,core);
    if(np<3 || nq==0 || np>1000000 || nq>1000000 || !std::isfinite(gamma) || !std::isfinite(core) || core<=0.0)
        throw std::runtime_error("Invalid shapes or regularization parameters");
    std::vector<double> raw(3ull*(np+nq));
    if(!f.read(reinterpret_cast<char*>(raw.data()),static_cast<std::streamsize>(raw.size()*sizeof(double))))
        throw std::runtime_error("Truncated coordinates");
    for(double v:raw)if(!std::isfinite(v))throw std::runtime_error("Nonfinite coordinates");
    std::vector<DS> pts(3ull*np),queries(3ull*nq),results(3ull*nq);
    for(size_t i=0;i<pts.size();i++)pts[i]=split_host(raw[i]);
    for(size_t i=0;i<queries.size();i++)queries[i]=split_host(raw[pts.size()+i]);
    DS *dp=nullptr,*dq=nullptr,*dr=nullptr;
    require_cuda(cudaMalloc(reinterpret_cast<void**>(&dp),pts.size()*sizeof(DS)),"malloc-p");
    require_cuda(cudaMalloc(reinterpret_cast<void**>(&dq),queries.size()*sizeof(DS)),"malloc-q");
    require_cuda(cudaMalloc(reinterpret_cast<void**>(&dr),results.size()*sizeof(DS)),"malloc-r");
    require_cuda(cudaMemcpy(dp,pts.data(),pts.size()*sizeof(DS),cudaMemcpyHostToDevice),"copy-p");
    require_cuda(cudaMemcpy(dq,queries.data(),queries.size()*sizeof(DS),cudaMemcpyHostToDevice),"copy-q");
    DS scale=split_host(gamma/(4.0*3.141592653589793238462643383279502884));
    DS core2=split_host(core*core);
    biot_savart_dd32<<<(nq+63)/64,64>>>(dp,dq,dr,np,nq,scale,core2);
    require_cuda(cudaGetLastError(),"kernel-launch");
    require_cuda(cudaDeviceSynchronize(),"kernel-sync");
    require_cuda(cudaMemcpy(results.data(),dr,results.size()*sizeof(DS),cudaMemcpyDeviceToHost),"copy-output");
    cudaFree(dp);cudaFree(dq);cudaFree(dr);
    std::vector<double> out(results.size());
    for(size_t i=0;i<out.size();i++){
        out[i]=static_cast<double>(results[i].hi)+static_cast<double>(results[i].lo);
        if(!std::isfinite(out[i]))throw std::runtime_error("Nonfinite DD32 output");
    }
    std::ofstream dest(output,std::ios::binary|std::ios::trunc);
    if(!dest.write(reinterpret_cast<char*>(out.data()),static_cast<std::streamsize>(out.size()*sizeof(double))))
        throw std::runtime_error("Unable to write CUDA DD32 output");
    return 0;
}
int main(int argc,char** argv){
    try {
        if(argc==2 && std::string(argv[1])=="--probe")return probe();
        if(argc==3)return run(argv[1],argv[2]);
        std::cerr<<"usage: cuda_dd32.exe --probe | input.bin output.bin\n";return 2;
    }catch(const std::exception& ex){std::cerr<<ex.what()<<"\n";return 2;}
}
