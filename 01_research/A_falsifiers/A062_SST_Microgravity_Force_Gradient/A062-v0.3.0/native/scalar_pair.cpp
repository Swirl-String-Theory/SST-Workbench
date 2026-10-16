// Independent C++17 FP64 quadrature for H1 postulated dimensionless scalar.
#include <fstream>
#include <vector>
#include <array>
#include <iostream>
#include <cmath>
#include <iomanip>
struct Point {double x,y,z,w;};
int main(int argc,char**argv){if(argc!=3)return 2;std::ifstream in(argv[1]);if(!in)return 3;double R=std::stod(argv[2]);std::vector<Point> q;Point p;while(in>>p.x>>p.y>>p.z>>p.w)q.push_back(p);if(q.empty())return 4;double fx=0,fy=0,fz=0;
for(auto const& b:q)for(auto const& a:q){double x=b.x-a.x,y=b.y-a.y,z=b.z+R-a.z;double inv=1./std::pow(x*x+y*y+z*z,1.5);double wt=-a.w*b.w*inv/(4.*3.141592653589793238462643383279502884);fx+=wt*x;fy+=wt*y;fz+=wt*z;}
std::cout<<std::setprecision(17)<<fx<<' '<<fy<<' '<<fz<<'\n';return 0;}
