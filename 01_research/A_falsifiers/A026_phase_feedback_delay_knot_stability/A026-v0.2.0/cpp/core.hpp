#pragma once
#include <array>
#include <vector>
#include <cstddef>

namespace sstpd {
using Vec3 = std::array<double,3>;

struct EvolutionResult {
    std::vector<double> times;
    std::vector<double> a_hist;
    std::vector<double> b_hist;
    std::size_t n = 0;
    double final_gap_a = 0.0;
    double final_gap_b = 0.0;
};

std::vector<Vec3> biot_savart_velocity(const std::vector<Vec3>& x, double gamma, double core);
std::vector<Vec3> rk4_step(const std::vector<Vec3>& x, double dt, double gamma, double core);
double min_nonadjacent_segment_distance(const std::vector<Vec3>& x, int exclusion=2);
EvolutionResult evolve_pair(const std::vector<Vec3>& a0, const std::vector<Vec3>& b0,
                            int steps, double dt, double gamma, double core, int sample_every);
}
