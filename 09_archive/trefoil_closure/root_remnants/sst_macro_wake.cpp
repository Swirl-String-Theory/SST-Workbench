// sst_macro_wake.cpp
// Macroscopische Biot-Savart solver voor absolute vorticiteit behoud (Z-as contour)
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>

namespace py = pybind11;

const double PI = 3.14159265358979323846;

// Functie voor Biot-Savart inductie op een specifiek meetpunt
std::vector<double> calculate_induced_velocity(
    const std::vector<std::vector<double>>& source_points,
    double gamma_source,
    const std::vector<double>& target_point
) {
    int N = source_points.size();
    double vx = 0.0, vy = 0.0, vz = 0.0;

    for (int i = 0; i < N; ++i) {
        int next_i = (i + 1) % N;
        double dl_x = source_points[next_i][0] - source_points[i][0];
        double dl_y = source_points[next_i][1] - source_points[i][1];
        double dl_z = source_points[next_i][2] - source_points[i][2];

        double rx = target_point[0] - source_points[i][0];
        double ry = target_point[1] - source_points[i][1];
        double rz = target_point[2] - source_points[i][2];

        double r_norm = std::sqrt(rx*rx + ry*ry + rz*rz);
        double r_cube = r_norm * r_norm * r_norm;

        vx += (dl_y * rz - dl_z * ry) / r_cube;
        vy += (dl_z * rx - dl_x * rz) / r_cube;
        vz += (dl_x * ry - dl_y * rx) / r_cube;
    }

    double prefactor = gamma_source / (4.0 * PI);
    return {prefactor * vx, prefactor * vy, prefactor * vz};
}

// Fase 5: Macro-Kelvin equilibratie via de centrale Z-as
double equilibrate_macro_circulation(
    double r_knot,
    double omega_0,
    double u_ext,
    double c_signal
) {
    int N_source = 1000;
    int N_contour = 2000;

    // De initiële capaciteit
    double gamma_0 = 2.0 * PI * r_knot * r_knot * omega_0;

    // Definieer de proxy-knoop (ring) in het X-Y vlak
    std::vector<std::vector<double>> source_points(N_source, std::vector<double>(3, 0.0));
    for (int i = 0; i < N_source; ++i) {
        double theta = 2.0 * PI * i / N_source;
        source_points[i][0] = r_knot * std::cos(theta);
        source_points[i][1] = r_knot * std::sin(theta);
        source_points[i][2] = 0.0;
    }

    // Meetcontour is nu de Z-as: prikt dwars door de kern (meet het wake-zog in de stroomrichting)
    double L_integration = 50.0 * r_knot;
    double dz = (2.0 * L_integration) / N_contour;

    std::vector<std::vector<double>> contour_points(N_contour, std::vector<double>(3, 0.0));
    for (int i = 0; i < N_contour; ++i) {
        contour_points[i][0] = 0.0;
        contour_points[i][1] = 0.0;
        contour_points[i][2] = -L_integration + i * dz;
    }

    double gamma_u = gamma_0;
    double tol = 1e-8;
    int max_iter = 100;

    for (int iter = 0; iter < max_iter; ++iter) {
        double gamma_wake = 0.0;

        for (int i = 0; i < N_contour; ++i) {
            auto v_ind = calculate_induced_velocity(source_points, gamma_u, contour_points[i]);

            // Wake-koppeling: de kinematische druk van de u_ext translatie
            // eist werveling in de achtergebleven vloeistofkolom (Z-as)
            double wake_term_z = v_ind[2] * (u_ext * u_ext / (c_signal * c_signal));

            // Dot-product met dl is nu simpelweg * dz
            gamma_wake += wake_term_z * dz;
        }

        // Behoudswet: Gamma_tot = Gamma_core(u) + Gamma_wake = Gamma_0
        double gamma_new = gamma_0 - gamma_wake;

        // RELATIEVE tolerantie check (geschaald naar de originele capaciteit)
        if (std::abs(gamma_new - gamma_u) / gamma_0 < tol) {
            gamma_u = gamma_new;
            break;
        }
        gamma_u = gamma_new;
    }

    return gamma_u / (2.0 * PI * r_knot * r_knot);
}

PYBIND11_MODULE(sst_macro_wake, m) {
    m.doc() = "Fase 5: Absolute Circulation Integrator";
    m.def("equilibrate_macro_circulation", &equilibrate_macro_circulation, "Berekent omega_u via Kelvin behoud langs z-as");
}