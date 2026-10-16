#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
struct Charge {double x,y,z,m;};
struct Probe {double x,y,z;};
int main(int argc,char**argv){
  if(argc!=3){std::cerr<<"usage: gravity_green_v060 charges.txt probes.txt\n";return 2;}
  std::ifstream a(argv[1]),b(argv[2]);
  if(!a||!b)return 3;
  std::vector<Charge> cs;std::vector<Probe> ps; Charge c;Probe q;
  while(a>>c.x>>c.y>>c.z>>c.m)cs.push_back(c);
  while(b>>q.x>>q.y>>q.z)ps.push_back(q);
  if(cs.empty()||ps.empty())return 4;
  std::cout<<std::setprecision(17);
  for(const auto& p:ps){
    double phi=0,gx=0,gy=0,gz=0;
    for(const auto& s:cs){
      double x=p.x-s.x,y=p.y-s.y,z=p.z-s.z;
      double d2=x*x+y*y+z*z;if(d2<=0)return 5;
      double inv=1/std::sqrt(d2),cube=inv/d2;
      phi-=s.m*inv;gx-=s.m*x*cube;gy-=s.m*y*cube;gz-=s.m*z*cube;
    }
    std::cout<<phi<<" "<<gx<<" "<<gy<<" "<<gz<<"\n";
  }
}
