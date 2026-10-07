#include <sycl/sycl.hpp>
#include <iostream>
int main(){
  try{
    sycl::queue q{sycl::default_selector_v};
    auto d=q.get_device();
    std::cout << "{\"status\":\"PASS\",\"device\":\"" << d.get_info<sycl::info::device::name>()
              << "\",\"fp64\":" << (d.has(sycl::aspect::fp64)?"true":"false") << "}" << std::endl;
    return 0;
  }catch(const std::exception& e){ std::cerr<<e.what()<<std::endl; return 2; }
}
