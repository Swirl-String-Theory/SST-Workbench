#pragma once
#include <array>
#include <cmath>
#include <vector>

namespace a057 {
using Point = std::array<double, 3>;
struct SegmentData { std::vector<Point> mid, dl; };

inline Point sub(const Point& a, const Point& b) {
    return {a[0]-b[0], a[1]-b[1], a[2]-b[2]};
}
inline double dot(const Point& a, const Point& b) {
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
}
inline SegmentData segment_data(const std::vector<Point>& pts) {
    SegmentData s;
    const std::size_t n = pts.size();
    s.mid.resize(n); s.dl.resize(n);
    for (std::size_t i=0;i<n;++i) {
        const auto& p=pts[i]; const auto& q=pts[(i+1)%n];
        s.dl[i]=sub(q,p);
        s.mid[i]={(p[0]+q[0])*0.5,(p[1]+q[1])*0.5,(p[2]+q[2])*0.5};
    }
    return s;
}
inline std::vector<std::vector<double>> energy_matrix(
    const std::vector<std::vector<Point>>& comps, double core) {
    std::vector<SegmentData> ds; ds.reserve(comps.size());
    for (const auto& c: comps) ds.push_back(segment_data(c));
    const std::size_t m=ds.size();
    std::vector<std::vector<double>> E(m,std::vector<double>(m,0.0));
    const double a2=core*core;
    for (std::size_t i=0;i<m;++i) for (std::size_t j=i;j<m;++j) {
        double value=0.0;
        #ifdef _OPENMP
        #pragma omp parallel for reduction(+:value)
        #endif
        for (long long k=0;k<static_cast<long long>(ds[i].mid.size());++k) {
            for (std::size_t l=0;l<ds[j].mid.size();++l) {
                const Point r=sub(ds[i].mid[static_cast<std::size_t>(k)],ds[j].mid[l]);
                const double den=std::sqrt(dot(r,r)+a2);
                value += dot(ds[i].dl[static_cast<std::size_t>(k)],ds[j].dl[l]) / std::max(den,1e-15);
            }
        }
        E[i][j]=E[j][i]=value;
    }
    return E;
}
}
