// Source-native multicomponent midpoint Rosenhead Biot-Savart velocity.
// Unforced dimensionless filament surrogate. No topology reconnections.
#include <cmath>
#include <cstddef>
#ifdef _OPENMP
#include <omp.h>
#endif
extern "C" {
#ifdef _WIN32
__declspec(dllexport)
#endif
void bs_velocity(const double *xyz, const int *starts, const double *gamma,
                 int components, int total_points, double core, double *vel) {
    const double inv4pi = 0.07957747154594766788444188;
    if (!xyz || !starts || !gamma || !vel || core <= 0 || components < 1 || total_points <= 0) return;
    const double a2 = core * core;
    #pragma omp parallel for schedule(static)
    for(int i=0; i<total_points; ++i) {
        const double *target = xyz + 3*i;
        double vx=0., vy=0., vz=0.;
        for (int j=0; j<components; ++j) {
            const int lo = starts[j], hi=starts[j+1];
            const double g=gamma[j];
            for(int k=lo; k<hi; ++k) {
                const int next=(k+1<hi)?k+1:lo;
                const double *b=xyz+3*k, *c=xyz+3*next;
                const double dx=c[0]-b[0], dy=c[1]-b[1], dz=c[2]-b[2];
                const double rx=target[0]-(b[0]+c[0])*0.5;
                const double ry=target[1]-(b[1]+c[1])*0.5;
                const double rz=target[2]-(b[2]+c[2])*0.5;
                const double inv=1./std::pow(rx*rx+ry*ry+rz*rz+a2,1.5);
                vx+=g*(dy*rz-dz*ry)*inv;
                vy+=g*(dz*rx-dx*rz)*inv;
                vz+=g*(dx*ry-dy*rx)*inv;
            }
        }
        vel[3*i] = vx*inv4pi;
        vel[3*i+1]=vy*inv4pi;
        vel[3*i+2]=vz*inv4pi;
    }
}
}
