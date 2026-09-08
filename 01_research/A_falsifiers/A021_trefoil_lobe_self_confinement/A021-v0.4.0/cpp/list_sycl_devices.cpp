#include <iostream>
#ifdef __SYCL_COMPILER_VERSION
#include <sycl/sycl.hpp>
int main(){for(auto const&p:sycl::platform::get_platforms())for(auto const&d:p.get_devices())std::cout<<p.get_info<sycl::info::platform::name>()<<" | "<<d.get_info<sycl::info::device::name>()<<" | gpu="<<d.is_gpu()<<"\n";return 0;}
#else
int main(){std::cout<<"Compile with icpx -fsycl\n";return 0;}
#endif
