#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

struct Vec3 {
    double x{}, y{}, z{};
    Vec3 operator+(const Vec3& o) const { return {x+o.x,y+o.y,z+o.z}; }
    Vec3 operator-(const Vec3& o) const { return {x-o.x,y-o.y,z-o.z}; }
    Vec3 operator*(double a) const { return {a*x,a*y,a*z}; }
    Vec3 operator/(double a) const { return {x/a,y/a,z/a}; }
    Vec3& operator+=(const Vec3& o){x+=o.x;y+=o.y;z+=o.z;return *this;}
};
static inline double dot(const Vec3&a,const Vec3&b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static inline Vec3 cross(const Vec3&a,const Vec3&b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
static inline double norm2(const Vec3&a){return dot(a,a);}
static inline double norm(const Vec3&a){return std::sqrt(norm2(a));}
static inline Vec3 normalized(const Vec3&a){double n=norm(a); return n>0?a/n:Vec3{};}

struct Component {
    std::vector<Vec3> p;
    std::vector<std::size_t> global;
    std::vector<double> cum; // cumulative arclength, size n+1
    double length{};
};
struct SegRef { int comp; int i; std::size_t g0,g1; Vec3 a,b; double s0, len, comp_len; };
struct Closest { double d; double u,v; Vec3 p,q; };

static std::vector<std::string> split_csv(const std::string& line){ std::vector<std::string> v; std::string x; std::istringstream ss(line); while(std::getline(ss,x,',')) v.push_back(x); return v; }

static std::vector<Component> read_xyz(const std::string& path){
    std::ifstream in(path);
    if(!in) throw std::runtime_error("cannot open input: "+path);
    std::vector<Component> comps(1);
    std::string line;
    while(std::getline(in,line)){
        auto first=line.find_first_not_of(" \t\r\n");
        if(first==std::string::npos){
            if(!comps.back().p.empty()) comps.emplace_back();
            continue;
        }
        if(line[first]=='#') continue;
        std::istringstream ss(line);
        Vec3 v;
        if(!(ss>>v.x>>v.y>>v.z)) throw std::runtime_error("bad XYZ line: "+line);
        comps.back().p.push_back(v);
    }
    if(comps.back().p.empty()) comps.pop_back();
    if(comps.empty()) throw std::runtime_error("no components found");
    std::size_t g=0;
    for(auto& c:comps){
        if(c.p.size()<4) throw std::runtime_error("each closed component needs >=4 vertices");
        c.global.resize(c.p.size());
        c.cum.assign(c.p.size()+1,0.0);
        for(std::size_t i=0;i<c.p.size();++i){
            c.global[i]=g++;
            c.cum[i+1]=c.cum[i]+norm(c.p[(i+1)%c.p.size()]-c.p[i]);
        }
        c.length=c.cum.back();
    }
    return comps;
}

static double circumradius(const Vec3&a,const Vec3&b,const Vec3&c){
    double A=norm(b-c), B=norm(a-c), C=norm(a-b);
    double area2=norm(cross(b-a,c-a)); // 2*area
    if(area2<=1e-15*(A*B+B*C+C*A+1.0)) return std::numeric_limits<double>::infinity();
    return A*B*C/(2.0*area2); // abc/(4 area) = abc/(2*area2)
}

// Ericson-style closest points between line segments.
static Closest segseg(const Vec3&p1,const Vec3&q1,const Vec3&p2,const Vec3&q2){
    const double EPS=1e-15;
    Vec3 d1=q1-p1, d2=q2-p2, r=p1-p2;
    double a=dot(d1,d1), e=dot(d2,d2), f=dot(d2,r);
    double s=0,t=0;
    if(a<=EPS && e<=EPS){ return {norm(p1-p2),0,0,p1,p2}; }
    if(a<=EPS){ s=0; t=std::clamp(f/e,0.0,1.0); }
    else {
        double c=dot(d1,r);
        if(e<=EPS){ t=0; s=std::clamp(-c/a,0.0,1.0); }
        else {
            double b=dot(d1,d2), denom=a*e-b*b;
            if(denom!=0) s=std::clamp((b*f-c*e)/denom,0.0,1.0); else s=0;
            t=(b*s+f)/e;
            if(t<0){t=0;s=std::clamp(-c/a,0.0,1.0);} else if(t>1){t=1;s=std::clamp((b-c)/a,0.0,1.0);}
        }
    }
    Vec3 cp1=p1+d1*s, cp2=p2+d2*t;
    return {norm(cp1-cp2),s,t,cp1,cp2};
}

static bool locally_adjacent_same(const SegRef&a,const SegRef&b,const std::vector<Component>& comps,double exclusion_frac){
    if(a.comp!=b.comp) return false;
    int n=(int)comps[a.comp].p.size();
    int d=std::abs(a.i-b.i); d=std::min(d,n-d);
    int k=std::max(1,(int)std::ceil(exclusion_frac*n));
    return d<=k;
}

static void add_grad(std::map<std::pair<int,int>,double>& nz, int row, int col, double v){
    if(std::abs(v)>1e-18) nz[{row,col}]+=v;
}

static void write_mtx(const std::string& path,int rows,int cols,const std::map<std::pair<int,int>,double>& nz){
    std::ofstream out(path); if(!out) throw std::runtime_error("cannot write "+path);
    out<<"%%MatrixMarket matrix coordinate real general\n";
    out<<rows<<" "<<cols<<" "<<nz.size()<<"\n";
    out<<std::setprecision(17);
    for(auto &kv:nz) out<<kv.first.first+1<<" "<<kv.first.second+1<<" "<<kv.second<<"\n";
}

static void write_vec_csv(const std::string& path,const std::vector<Vec3>& v){
    std::ofstream out(path); if(!out) throw std::runtime_error("cannot write "+path);
    out<<"index,x,y,z\n"<<std::setprecision(17);
    for(std::size_t i=0;i<v.size();++i) out<<i<<","<<v[i].x<<","<<v[i].y<<","<<v[i].z<<"\n";
}

static std::string json_escape(const std::string&s){
    std::ostringstream o;
    for(char c:s){ if(c=='\\'||c=='\"') o<<'\\'<<c; else if(c=='\n')o<<"\\n"; else o<<c; }
    return o.str();
}

int main(int argc,char**argv){
    try{
        std::string input,outdir="native_out",contacts_sidecar,kinks_sidecar;
        double radius=-1.0, contact_tol=0.015, kink_tol=0.015, local_exclusion_frac=0.02;
        for(int i=1;i<argc;++i){
            std::string a=argv[i];
            auto need=[&](){ if(i+1>=argc) throw std::runtime_error("missing value after "+a); return std::string(argv[++i]);};
            if(a=="--input") input=need();
            else if(a=="--out") outdir=need();
            else if(a=="--radius") radius=std::stod(need());
            else if(a=="--contact-tol") contact_tol=std::stod(need());
            else if(a=="--kink-tol") kink_tol=std::stod(need());
            else if(a=="--local-exclusion-frac") local_exclusion_frac=std::stod(need());
            else if(a=="--contacts-sidecar") contacts_sidecar=need();
            else if(a=="--kinks-sidecar") kinks_sidecar=need();
            else if(a=="--help"){
                std::cout<<"sst_reciprocal_core --input curve.xyz --out DIR [--radius a] [--contact-tol f] [--kink-tol f] [--local-exclusion-frac f] [--contacts-sidecar contacts.csv] [--kinks-sidecar kinks.csv]\n";
                return 0;
            } else throw std::runtime_error("unknown argument: "+a);
        }
        if(input.empty()) throw std::runtime_error("--input is required");
#ifdef _WIN32
        std::string mkdir_cmd="if not exist \""+outdir+"\" mkdir \""+outdir+"\"";
#else
        std::string mkdir_cmd="mkdir -p \""+outdir+"\"";
#endif
        if(std::system(mkdir_cmd.c_str())!=0) throw std::runtime_error("failed to create outdir");
        auto comps=read_xyz(input);
        std::vector<Vec3> all;
        for(auto&c:comps) for(auto&p:c.p) all.push_back(p);
        const int N=(int)all.size();

        std::vector<SegRef> segs;
        for(int ci=0;ci<(int)comps.size();++ci){
            auto& c=comps[ci];
            for(int i=0;i<(int)c.p.size();++i){
                int j=(i+1)%c.p.size();
                double L=norm(c.p[j]-c.p[i]);
                segs.push_back({ci,i,c.global[i],c.global[j],c.p[i],c.p[j],c.cum[i],L,c.length});
            }
        }

        double minR=std::numeric_limits<double>::infinity();
        struct KRec{int comp,vi; std::size_t gprev,g,gnext; double R,snorm; double supplied_lambda=std::numeric_limits<double>::quiet_NaN();};
        std::vector<KRec> allk;
        for(int ci=0;ci<(int)comps.size();++ci){
            auto&c=comps[ci]; int n=(int)c.p.size();
            for(int i=0;i<n;++i){
                int ip=(i-1+n)%n, in=(i+1)%n;
                double R=circumradius(c.p[ip],c.p[i],c.p[in]);
                minR=std::min(minR,R);
                allk.push_back({ci,i,c.global[ip],c.global[i],c.global[in],R,c.cum[i]/c.length,std::numeric_limits<double>::quiet_NaN()});
            }
        }

        double minD=std::numeric_limits<double>::infinity();
        struct CRec{int sa,sb; Closest c; double sna,snb; double supplied_lambda=std::numeric_limits<double>::quiet_NaN();};
        std::vector<CRec> allc;
        for(int i=0;i<(int)segs.size();++i){
            for(int j=i+1;j<(int)segs.size();++j){
                if(locally_adjacent_same(segs[i],segs[j],comps,local_exclusion_frac)) continue;
                auto cl=segseg(segs[i].a,segs[i].b,segs[j].a,segs[j].b);
                minD=std::min(minD,cl.d);
                double sna=(segs[i].s0+cl.u*segs[i].len)/segs[i].comp_len;
                double snb=(segs[j].s0+cl.v*segs[j].len)/segs[j].comp_len;
                allc.push_back({i,j,cl,sna,snb,std::numeric_limits<double>::quiet_NaN()});
            }
        }
        if(!std::isfinite(minD)) minD=std::numeric_limits<double>::quiet_NaN();
        double inferred=std::min(minR,0.5*minD);
        bool radius_inferred=radius<=0;
        if(radius_inferred) radius=inferred;
        if(!(radius>0) || !std::isfinite(radius)) throw std::runtime_error("could not determine positive radius");

        std::vector<CRec> activeC;
        if(contacts_sidecar.empty()) {
            for(auto&r:allc) if(r.c.d <= 2.0*radius*(1.0+contact_tol)) activeC.push_back(r);
        } else {
            std::ifstream f(contacts_sidecar); if(!f) throw std::runtime_error("cannot open contacts sidecar: "+contacts_sidecar);
            std::string line; if(!std::getline(f,line)) throw std::runtime_error("empty contacts sidecar");
            auto hdr=split_csv(line); std::map<std::string,int> H; for(int i=0;i<(int)hdr.size();++i) H[hdr[i]]=i;
            for(auto req:{std::string("comp_a"),std::string("s_norm"),std::string("comp_b"),std::string("t_norm")}) if(!H.count(req)) throw std::runtime_error("contacts sidecar missing column "+req);
            auto locate=[&](int ci,double sn){ auto&c=comps.at(ci); sn=sn-std::floor(sn); double target=sn*c.length; auto it=std::upper_bound(c.cum.begin(),c.cum.end(),target); int i=std::max(0,std::min((int)c.p.size()-1,(int)(it-c.cum.begin())-1)); double den=c.cum[i+1]-c.cum[i]; double u=den>0?(target-c.cum[i])/den:0.0; int si=-1; for(int k=0;k<(int)segs.size();++k) if(segs[k].comp==ci && segs[k].i==i){si=k;break;} return std::pair<int,double>(si,u); };
            while(std::getline(f,line)){ if(line.empty()) continue; auto v=split_csv(line); int ca=std::stoi(v[H["comp_a"]]), cb=std::stoi(v[H["comp_b"]]); double sa=std::stod(v[H["s_norm"]]), sb=std::stod(v[H["t_norm"]]); auto la=locate(ca,sa), lb=locate(cb,sb); if(la.first<0||lb.first<0) throw std::runtime_error("sidecar location failed"); auto&A=segs[la.first]; auto&B=segs[lb.first]; Vec3 pa=A.a+(A.b-A.a)*la.second, pb=B.a+(B.b-B.a)*lb.second; Closest cl{norm(pa-pb),la.second,lb.second,pa,pb}; double lam=std::numeric_limits<double>::quiet_NaN(); if(H.count("multiplier") && H["multiplier"]<(int)v.size() && !v[H["multiplier"]].empty()) lam=std::stod(v[H["multiplier"]]); activeC.push_back({la.first,lb.first,cl,sa,sb,lam}); }
        }
        std::vector<KRec> activeK;
        if(kinks_sidecar.empty()) {
            for(auto&r:allk) if(r.R <= radius*(1.0+kink_tol)) activeK.push_back(r);
        } else {
            std::ifstream f(kinks_sidecar); if(!f) throw std::runtime_error("cannot open kinks sidecar: "+kinks_sidecar);
            std::string line; if(!std::getline(f,line)) throw std::runtime_error("empty kinks sidecar"); auto hdr=split_csv(line); std::map<std::string,int> H; for(int i=0;i<(int)hdr.size();++i) H[hdr[i]]=i;
            if(!H.count("comp")||!H.count("s_norm")) throw std::runtime_error("kinks sidecar requires comp,s_norm");
            while(std::getline(f,line)){ if(line.empty())continue; auto v=split_csv(line); int ci=std::stoi(v[H["comp"]]); double sn=std::stod(v[H["s_norm"]]); auto&c=comps.at(ci); double target=(sn-std::floor(sn))*c.length; int best=0; double bd=1e300; for(int i=0;i<(int)c.p.size();++i){ double d=std::abs(c.cum[i]-target); d=std::min(d,c.length-d); if(d<bd){bd=d;best=i;} } int n=(int)c.p.size(), ip=(best-1+n)%n, in=(best+1)%n; double R=circumradius(c.p[ip],c.p[best],c.p[in]); double lam=std::numeric_limits<double>::quiet_NaN(); if(H.count("multiplier")&&H["multiplier"]<(int)v.size()&&!v[H["multiplier"]].empty())lam=std::stod(v[H["multiplier"]]); activeK.push_back({ci,best,c.global[ip],c.global[best],c.global[in],R,c.cum[best]/c.length,lam}); }
        }

        const int M=(int)(activeC.size()+activeK.size());
        std::map<std::pair<int,int>,double> nz;
        int col=0;
        std::ofstream coutf(outdir+"/contacts.csv");
        coutf<<"column,comp_a,seg_a,u,s_norm,comp_b,seg_b,v,t_norm,distance,supplied_multiplier\n"<<std::setprecision(17);
        for(auto&r:activeC){
            auto&A=segs[r.sa]; auto&B=segs[r.sb];
            Vec3 d=r.c.p-r.c.q; double dn=norm(d); if(dn<=1e-15) continue;
            Vec3 n=d/dn;
            // gradient of d/2 wrt segment endpoints
            std::array<std::pair<std::size_t,double>,4> w={{{A.g0,0.5*(1-r.c.u)},{A.g1,0.5*r.c.u},{B.g0,-0.5*(1-r.c.v)},{B.g1,-0.5*r.c.v}}};
            for(auto &ww:w){
                int base=3*(int)ww.first;
                add_grad(nz,base+0,col,ww.second*n.x);
                add_grad(nz,base+1,col,ww.second*n.y);
                add_grad(nz,base+2,col,ww.second*n.z);
            }
            coutf<<col<<","<<A.comp<<","<<A.i<<","<<r.c.u<<","<<r.sna<<","<<B.comp<<","<<B.i<<","<<r.c.v<<","<<r.snb<<","<<r.c.d<<","<<(std::isfinite(r.supplied_lambda)?std::to_string(r.supplied_lambda):std::string(""))<<"\n";
            ++col;
        }
        coutf.close();

        std::ofstream kout(outdir+"/kinks.csv");
        kout<<"column,comp,vertex,s_norm,radius,supplied_multiplier\n"<<std::setprecision(17);
        double scale=0; for(auto&s:segs) scale+=s.len; scale/=std::max<std::size_t>(1,segs.size());
        double h=std::max(1e-9,1e-7*scale);
        for(auto&r:activeK){
            auto&c=comps[r.comp]; int n=(int)c.p.size(); int i=r.vi, ip=(i-1+n)%n, in=(i+1)%n;
            std::array<int,3> loc={ip,i,in};
            for(int q=0;q<3;++q){
                for(int ax=0;ax<3;++ax){
                    auto pp=c.p[ip], pc=c.p[i], pn=c.p[in];
                    Vec3* vp = q==0?&pp:(q==1?&pc:&pn);
                    if(ax==0) vp->x+=h; else if(ax==1) vp->y+=h; else vp->z+=h;
                    double rp=circumradius(pp,pc,pn);
                    pp=c.p[ip]; pc=c.p[i]; pn=c.p[in];
                    Vec3* vm = q==0?&pp:(q==1?&pc:&pn);
                    if(ax==0) vm->x-=h; else if(ax==1) vm->y-=h; else vm->z-=h;
                    double rm=circumradius(pp,pc,pn);
                    double g=(rp-rm)/(2*h);
                    std::size_t gv=c.global[loc[q]];
                    if(std::isfinite(g)) add_grad(nz,3*(int)gv+ax,col,g);
                }
            }
            kout<<col<<","<<r.comp<<","<<r.vi<<","<<r.snorm<<","<<r.R<<","<<(std::isfinite(r.supplied_lambda)?std::to_string(r.supplied_lambda):std::string(""))<<"\n";
            ++col;
        }
        kout.close();

        // Length gradient b = grad L, compatible with -grad L + A lambda = 0.
        std::vector<Vec3> b(N);
        for(auto&c:comps){ int n=(int)c.p.size();
            for(int i=0;i<n;++i){ int ip=(i-1+n)%n, in=(i+1)%n; Vec3 g=(c.p[i]-c.p[ip])/norm(c.p[i]-c.p[ip])+(c.p[i]-c.p[in])/norm(c.p[i]-c.p[in]); b[c.global[i]]+=g; }
        }
        write_mtx(outdir+"/A.mtx",3*N,M,nz);
        write_vec_csv(outdir+"/b_length_gradient.csv",b);

        std::ofstream meta(outdir+"/native_metrics.json");
        meta<<std::setprecision(17);
        meta<<"{\n";
        meta<<"  \"input\": \""<<json_escape(input)<<"\",\n";
        meta<<"  \"component_count\": "<<comps.size()<<",\n";
        meta<<"  \"vertex_count\": "<<N<<",\n";
        meta<<"  \"segment_count\": "<<segs.size()<<",\n";
        meta<<"  \"min_discrete_curvature_radius\": "<<minR<<",\n";
        meta<<"  \"min_nonadjacent_segment_distance\": "<<minD<<",\n";
        meta<<"  \"radius\": "<<radius<<",\n";
        meta<<"  \"radius_inferred\": "<<(radius_inferred?"true":"false")<<",\n";
        meta<<"  \"contact_tolerance_fraction\": "<<contact_tol<<",\n";
        meta<<"  \"kink_tolerance_fraction\": "<<kink_tol<<",\n";
        meta<<"  \"local_exclusion_fraction\": "<<local_exclusion_frac<<",\n";
        meta<<"  \"contacts_source\": \""<<(contacts_sidecar.empty()?"inferred":"sidecar")<<"\",\n";
        meta<<"  \"kinks_source\": \""<<(kinks_sidecar.empty()?"inferred":"sidecar")<<"\",\n";
        meta<<"  \"active_strut_count\": "<<activeC.size()<<",\n";
        meta<<"  \"active_kink_count\": "<<activeK.size()<<",\n";
        meta<<"  \"matrix_rows\": "<<3*N<<",\n";
        meta<<"  \"matrix_columns\": "<<M<<"\n";
        meta<<"}\n";
        meta.close();
        std::cout<<"Wrote native geometry/contact audit to "<<outdir<<" (N="<<N<<", M="<<M<<")\n";
        return 0;
    }catch(const std::exception&e){ std::cerr<<"ERROR: "<<e.what()<<"\n"; return 2; }
}
