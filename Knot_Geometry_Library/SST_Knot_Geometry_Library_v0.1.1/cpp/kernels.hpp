#pragma once
#include <cmath>
#include <limits>
#include <algorithm>
#include <vector>

namespace sstknot {
struct V3 { double x,y,z; };
inline V3 add(V3 a,V3 b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
inline V3 sub(V3 a,V3 b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
inline V3 mul(V3 a,double s){return {a.x*s,a.y*s,a.z*s};}
inline double dot(V3 a,V3 b){return a.x*b.x+a.y*b.y+a.z*b.z;}
inline V3 cross(V3 a,V3 b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
inline double norm(V3 a){return std::sqrt(dot(a,a));}
inline double segseg(V3 p1,V3 q1,V3 p2,V3 q2){
    V3 u=sub(q1,p1), v=sub(q2,p2), w=sub(p1,p2);
    double a=dot(u,u), b=dot(u,v), c=dot(v,v), d=dot(u,w), e=dot(v,w);
    double D=a*c-b*b, eps=1e-30, sN=D,sD=D,tN=D,tD=D;
    if(D<eps){sN=0.0;sD=1.0;tN=e;tD=c;}
    else{
        sN=b*e-c*d; tN=a*e-b*d;
        if(sN<0.0){sN=0.0;tN=e;tD=c;}
        else if(sN>sD){sN=sD;tN=e+b;tD=c;}
    }
    if(tN<0.0){tN=0.0;if(-d<0.0)sN=0.0;else if(-d>a)sN=sD;else{sN=-d;sD=a;}}
    else if(tN>tD){tN=tD;if((-d+b)<0.0)sN=0.0;else if((-d+b)>a)sN=sD;else{sN=(-d+b);sD=a;}}
    double sc=(std::abs(sN)<eps)?0.0:sN/std::max(sD,eps);
    double tc=(std::abs(tN)<eps)?0.0:tN/std::max(tD,eps);
    return norm(add(w,sub(mul(u,sc),mul(v,tc))));
}
inline double min_nonlocal_distance(const std::vector<V3>& p,int skip){
    int n=(int)p.size(); double best=std::numeric_limits<double>::infinity();
    for(int i=0;i<n;i++){
        int i2=(i+1)%n;
        for(int j=i+1;j<n;j++){
            int cyc=j-i; cyc=std::min(cyc,n-cyc); if(cyc<=skip) continue;
            int j2=(j+1)%n;
            best=std::min(best,segseg(p[i],p[i2],p[j],p[j2]));
        }
    }
    return best;
}
inline double writhe_midpoint(const std::vector<V3>& p){
    int n=(int)p.size(); std::vector<V3> m(n),dl(n);
    for(int i=0;i<n;i++){V3 q=p[(i+1)%n];dl[i]=sub(q,p[i]);m[i]=mul(add(q,p[i]),0.5);}
    double acc=0.0;
    #ifdef _OPENMP
    #pragma omp parallel for reduction(+:acc) schedule(static)
    #endif
    for(int i=0;i<n;i++){
        double local=0.0;
        for(int j=0;j<n;j++){
            if(j==i || j==(i+1)%n || j==(i+n-1)%n) continue;
            V3 r=sub(m[i],m[j]);double rr=norm(r);if(rr<1e-15)continue;
            local+=dot(cross(dl[i],dl[j]),r)/(rr*rr*rr);
        }
        acc+=local;
    }
    return acc/(4.0*3.141592653589793238462643383279502884);
}
inline double linking_midpoint(const std::vector<V3>& a,const std::vector<V3>& b){
    int na=(int)a.size(),nb=(int)b.size();std::vector<V3> ma(na),da(na),mb(nb),db(nb);
    for(int i=0;i<na;i++){V3 q=a[(i+1)%na];da[i]=sub(q,a[i]);ma[i]=mul(add(q,a[i]),0.5);}
    for(int j=0;j<nb;j++){V3 q=b[(j+1)%nb];db[j]=sub(q,b[j]);mb[j]=mul(add(q,b[j]),0.5);}
    double acc=0.0;
    #ifdef _OPENMP
    #pragma omp parallel for reduction(+:acc) schedule(static)
    #endif
    for(int i=0;i<na;i++){
        double local=0.0;
        for(int j=0;j<nb;j++){
            V3 r=sub(ma[i],mb[j]);double rr=norm(r);if(rr<1e-15)continue;
            local+=dot(cross(da[i],db[j]),r)/(rr*rr*rr);
        }
        acc+=local;
    }
    return acc/(4.0*3.141592653589793238462643383279502884);
}
}
