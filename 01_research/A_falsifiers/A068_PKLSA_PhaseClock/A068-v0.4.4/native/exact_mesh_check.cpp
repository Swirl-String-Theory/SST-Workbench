// OPTIONAL independent CGAL mesh check, not built during Python-only smoke.
// Uses exact predicates on the binary64 input point coordinates; this cannot
// certify smooth-time continuous surfaces between archived snapshots.
#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/Surface_mesh.h>
#include <CGAL/Polygon_mesh_processing/self_intersections.h>
#include <fstream>
#include <iostream>
#include <string>
#include <utility>
#include <vector>
namespace PMP = CGAL::Polygon_mesh_processing;
using Kernel = CGAL::Exact_predicates_exact_constructions_kernel;
using Mesh = CGAL::Surface_mesh<Kernel::Point_3>;
int main(int argc,char** argv){
  if(argc!=2){std::cerr<<"Usage: exact_mesh_check mesh.txt\n";return 2;}
  std::ifstream in(argv[1]); if(!in){std::cerr<<"Cannot open mesh\n";return 2;}
  size_t nv=0,nf=0; if(!(in>>nv>>nf)||nv<4||nf<4){std::cerr<<"Bad mesh header\n";return 2;}
  Mesh mesh;std::vector<Mesh::Vertex_index> vertices;
  vertices.reserve(nv);
  for(size_t i=0;i<nv;++i){double x,y,z;if(!(in>>x>>y>>z))return 2;
    vertices.push_back(mesh.add_vertex(Kernel::Point_3(x,y,z)));}
  for(size_t i=0;i<nf;++i){size_t a,b,c;if(!(in>>a>>b>>c)||a>=nv||b>=nv||c>=nv)return 2;
    if(mesh.add_face(vertices[a],vertices[b],vertices[c])==Mesh::null_face()){
      std::cerr<<"Invalid topological face "<<i<<"\n";return 3;
    }}
  std::vector<std::pair<Mesh::Face_index,Mesh::Face_index>> collision;
  try{PMP::self_intersections(mesh,std::back_inserter(collision));}
  catch(const std::exception& ex){std::cerr<<ex.what()<<"\n";return 3;}
  std::cout<<"{\"schema\":\"A068-EXACT-PREDICATE-MESH-v0.4.5\",\"triangle_count\":"
           <<nf<<",\"self_intersection_pairs\":"<<collision.size()
           <<",\"mesh_no_self_intersection\":"<<(collision.empty()?"true":"false")
           <<",\"relative_to_binary64_input\":true,\"continuous_time_certified\":false}"<<std::endl;
  return collision.empty()?0:4;
}
