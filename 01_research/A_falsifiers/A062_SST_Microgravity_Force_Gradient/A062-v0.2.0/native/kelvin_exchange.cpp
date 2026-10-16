// Standalone C++ FP64 implementation of Rosenhead-Kelvin exchange for two closed
// regularized vortex filaments. Independent loops; no Newton G in source.
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
struct V {double x,y,z;};
V operator+(V a,V b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
V operator-(V a,V b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
V operator*(V a,double b){return {a.x*b,a.y*b,a.z*b};}
V cross(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
std::vector<V> read(std::string path){std::ifstream file(path);if(!file)throw std::runtime_error("missing geometry");std::vector<V> v;V x;while(file>>x.x>>x.y>>x.z)v.push_back(x);if(v.size()<24)throw std::runtime_error("too few vertices");return v;}
V rotate_x(V v,double t){double c=cos(t),s=sin(t);return {v.x,c*v.y-s*v.z,s*v.y+c*v.z};}
V vel(V target,const std::vector<V> &src,double a){V ans={0,0,0};const double tau=1./(4.*acos(-1.));for(size_t i=0;i<src.size();++i){V ds=src[(i+1)%src.size()]-src[i];V mid=(src[i]+src[(i+1)%src.size()])*.5;V r=target-mid; double d=std::pow(dot(r,r)+a*a,1.5);ans=ans+cross(ds,r)*(tau/d);}return ans;}
V exchange(const std::vector<V>&a,const std::vector<V>&b,double eps){V q={0,0,0};for(size_t i=0;i<b.size();++i){V ds=b[(i+1)%b.size()]-b[i];V mid=(b[i]+b[(i+1)%b.size()])*.5;q=q+cross(vel(mid,a,eps),ds);}return q;}
int main(int argc,char** argv){try{if(argc!=7)throw std::runtime_error("usage: cpp geoA geoB separation core theta sign_b");auto a=read(argv[1]),b=read(argv[2]);double r=std::stod(argv[3]),eps=std::stod(argv[4]),t=std::stod(argv[5]),sign=std::stod(argv[6]);for(auto&v:b){v=rotate_x(v,t);v.z+=r;}const double rho=7e-7,rc=1.40897017e-15,vs=1.09384563e6;double gamma=2*acos(-1.)*rc*vs;double pref=rho*gamma*gamma*sign;V fb=exchange(a,b,eps)*pref;V fa=exchange(b,a,eps)*pref;std::cout<<std::setprecision(17)<<fb.x<<" "<<fb.y<<" "<<fb.z<<" "<<fa.x<<" "<<fa.y<<" "<<fa.z<<"\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
