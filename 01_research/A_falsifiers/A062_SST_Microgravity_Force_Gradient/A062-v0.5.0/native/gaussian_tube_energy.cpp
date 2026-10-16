#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <vector>
#include <array>
struct P{double x,y,z;};
P operator-(P a,P b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
P operator+(P a,P b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
P operator*(P a,double s){return {a.x*s,a.y*s,a.z*s};}
double dot(P a,P b){return a.x*b.x+a.y*b.y+a.z*b.z;}
int main(int argc,char**argv){
 if(argc!=3) return 2;
 const double a=std::strtod(argv[2],nullptr);
 if(!(a>0))return 3;
 std::ifstream f(argv[1]);if(!f)return 4;
 std::vector<P> x;P t;
 while(f>>t.x>>t.y>>t.z)x.push_back(t);
 if(x.size()<24)return 5;
 const size_t n=x.size();
 std::vector<P> edges(n),mids(n);
 for(size_t i=0;i<n;++i) {edges[i]=x[(i+1)%n]-x[i];mids[i]=(x[(i+1)%n]+x[i])*.5;}
 double sum=0,cs=0;
 for(size_t i=0;i<n;++i)for(size_t j=0;j<n;++j){
   P d=mids[i]-mids[j];double r=std::sqrt(dot(d,d));
   const double k=r>1e-14?std::erf(r/(2*a))/r:1/(a*std::sqrt(3.1415926535897932384626));
   double add=dot(edges[i],edges[j])*k;
   double y=add-cs,ss=sum+y;cs=(ss-sum)-y;sum=ss;
 }
 std::cout<<std::setprecision(17)<<sum<<"\n";
 return 0;
}
