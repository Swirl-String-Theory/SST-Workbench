#include "core.hpp"
#include <cmath>
#include <algorithm>
#include <limits>
#include <stdexcept>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace sstpd {
static inline Vec3 add(const Vec3&a,const Vec3&b){return {a[0]+b[0],a[1]+b[1],a[2]+b[2]};}
static inline Vec3 sub(const Vec3&a,const Vec3&b){return {a[0]-b[0],a[1]-b[1],a[2]-b[2]};}
static inline Vec3 mul(const Vec3&a,double s){return {a[0]*s,a[1]*s,a[2]*s};}
static inline double dot(const Vec3&a,const Vec3&b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static inline Vec3 cross(const Vec3&a,const Vec3&b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
static inline double norm2(const Vec3&a){return dot(a,a);}
static inline double norm(const Vec3&a){return std::sqrt(norm2(a));}

std::vector<Vec3> biot_savart_velocity(const std::vector<Vec3>& x, double gamma, double core){
    const std::size_t n=x.size();
    if(n<4) throw std::runtime_error("need >=4 points");
    if(!(core>0)) throw std::runtime_error("core must be >0");
    std::vector<Vec3> v(n,{0.0,0.0,0.0});
    constexpr double PI=3.141592653589793238462643383279502884;
    const double pref=gamma/(4.0*PI);
    #ifdef _OPENMP
    #pragma omp parallel for schedule(static)
    #endif
    for(long long ii=0; ii<(long long)n; ++ii){
        const std::size_t i=(std::size_t)ii;
        Vec3 acc{0,0,0};
        for(std::size_t j=0;j<n;++j){
            const std::size_t jp=(j+1)%n;
            if(j==i || jp==i) continue; // omit singular local segments
            const Vec3 dl=sub(x[jp],x[j]);
            const Vec3 mid=mul(add(x[jp],x[j]),0.5);
            const Vec3 r=sub(x[i],mid);
            const double den=std::pow(norm2(r)+core*core,1.5);
            const Vec3 c=cross(dl,r);
            acc[0]+=c[0]/den; acc[1]+=c[1]/den; acc[2]+=c[2]/den;
        }
        v[i]=mul(acc,pref);
    }
    return v;
}

static std::vector<Vec3> combine(const std::vector<Vec3>& x,const std::vector<Vec3>& k,double a){
    std::vector<Vec3> y(x.size());
    for(std::size_t i=0;i<x.size();++i)y[i]=add(x[i],mul(k[i],a));
    return y;
}

std::vector<Vec3> rk4_step(const std::vector<Vec3>& x,double dt,double gamma,double core){
    auto k1=biot_savart_velocity(x,gamma,core);
    auto k2=biot_savart_velocity(combine(x,k1,0.5*dt),gamma,core);
    auto k3=biot_savart_velocity(combine(x,k2,0.5*dt),gamma,core);
    auto k4=biot_savart_velocity(combine(x,k3,dt),gamma,core);
    std::vector<Vec3> y(x.size());
    for(std::size_t i=0;i<x.size();++i){
        Vec3 s=add(add(k1[i],mul(k2[i],2.0)),add(mul(k3[i],2.0),k4[i]));
        y[i]=add(x[i],mul(s,dt/6.0));
    }
    return y;
}

static double segment_distance(const Vec3&p1,const Vec3&q1,const Vec3&p2,const Vec3&q2){
    const Vec3 d1=sub(q1,p1), d2=sub(q2,p2), r=sub(p1,p2);
    const double a=dot(d1,d1), e=dot(d2,d2), f=dot(d2,r);
    double s=0.0,t=0.0;
    const double eps=1e-15;
    if(a<=eps && e<=eps) return norm(r);
    if(a<=eps){ t=std::clamp(f/e,0.0,1.0); }
    else {
        const double c=dot(d1,r);
        if(e<=eps){ s=std::clamp(-c/a,0.0,1.0); }
        else {
            const double b=dot(d1,d2), denom=a*e-b*b;
            if(std::abs(denom)>eps) s=std::clamp((b*f-c*e)/denom,0.0,1.0);
            t=(b*s+f)/e;
            if(t<0){t=0;s=std::clamp(-c/a,0.0,1.0);} else if(t>1){t=1;s=std::clamp((b-c)/a,0.0,1.0);}
        }
    }
    const Vec3 c1=add(p1,mul(d1,s)), c2=add(p2,mul(d2,t));
    return norm(sub(c1,c2));
}

double min_nonadjacent_segment_distance(const std::vector<Vec3>& x,int exclusion){
    const int n=(int)x.size();
    double best=std::numeric_limits<double>::infinity();
    for(int i=0;i<n;++i){
        for(int j=i+1;j<n;++j){
            int d=std::abs(i-j); d=std::min(d,n-d);
            if(d<=exclusion) continue;
            best=std::min(best,segment_distance(x[i],x[(i+1)%n],x[j],x[(j+1)%n]));
        }
    }
    return best;
}

static void append_flat(std::vector<double>& out,const std::vector<Vec3>& x){
    out.reserve(out.size()+3*x.size());
    for(const auto&p:x){out.push_back(p[0]);out.push_back(p[1]);out.push_back(p[2]);}
}

EvolutionResult evolve_pair(const std::vector<Vec3>& a0,const std::vector<Vec3>& b0,int steps,double dt,double gamma,double core,int sample_every){
    if(a0.size()!=b0.size()) throw std::runtime_error("pair sizes differ");
    if(steps<1 || sample_every<1) throw std::runtime_error("invalid evolution controls");
    std::vector<Vec3> a=a0,b=b0;
    EvolutionResult r; r.n=a.size();
    r.times.push_back(0.0); append_flat(r.a_hist,a); append_flat(r.b_hist,b);
    for(int s=1;s<=steps;++s){
        a=rk4_step(a,dt,gamma,core); b=rk4_step(b,dt,gamma,core);
        if(s%sample_every==0 || s==steps){r.times.push_back(s*dt);append_flat(r.a_hist,a);append_flat(r.b_hist,b);}
    }
    r.final_gap_a=min_nonadjacent_segment_distance(a,2);
    r.final_gap_b=min_nonadjacent_segment_distance(b,2);
    return r;
}
}
