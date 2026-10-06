#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
namespace py=pybind11;
std::vector<double> centered_group_velocity(const std::vector<double>& k,const std::vector<double>& w){
 if(k.size()!=w.size() || k.size()<3) throw std::runtime_error("need >=3 aligned samples");
 std::vector<double> out; out.reserve(k.size()-2);
 for(std::size_t i=1;i+1<k.size();++i){ double dk=k[i+1]-k[i-1]; if(dk==0) throw std::runtime_error("duplicate k"); out.push_back((w[i+1]-w[i-1])/dk); }
 return out;
}
PYBIND11_MODULE(_native,m){m.def("centered_group_velocity",&centered_group_velocity);}
