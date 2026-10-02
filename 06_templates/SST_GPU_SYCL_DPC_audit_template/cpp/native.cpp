#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

namespace {

constexpr double PI = 3.141592653589793238462643383279502884;

double g_last_ms = 0.0;
std::string g_last_backend = "serial";

struct ScopedTimer {
    std::chrono::steady_clock::time_point t0{std::chrono::steady_clock::now()};
    void stop(const std::string& backend) {
        auto t1 = std::chrono::steady_clock::now();
        g_last_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        g_last_backend = backend;
    }
};

const double* ptr_nx3(py::array_t<double, py::array::c_style | py::array::forcecast>& arr, py::ssize_t& n) {
    auto b = arr.request();
    if (b.ndim != 2 || b.shape[1] != 3) {
        throw std::runtime_error("array must be Nx3");
    }
    n = b.shape[0];
    return static_cast<const double*>(b.ptr);
}

void biot_one(const double* p, py::ssize_t n, const double* x, double scale, double a2, double* out) {
    double vx = 0.0, vy = 0.0, vz = 0.0;
    for (py::ssize_t s = 0; s < n; ++s) {
        py::ssize_t t = (s + 1) % n;
        double ax = p[3 * s], ay = p[3 * s + 1], az = p[3 * s + 2];
        double bx = p[3 * t], by = p[3 * t + 1], bz = p[3 * t + 2];
        double dlx = bx - ax, dly = by - ay, dlz = bz - az;
        double mx = 0.5 * (ax + bx), my = 0.5 * (ay + by), mz = 0.5 * (az + bz);
        double rx = x[0] - mx, ry = x[1] - my, rz = x[2] - mz;
        double D = rx * rx + ry * ry + rz * rz + a2;
        double inv3 = 1.0 / (D * std::sqrt(D));
        double crx = dly * rz - dlz * ry;
        double cry = dlz * rx - dlx * rz;
        double crz = dlx * ry - dly * rx;
        vx += scale * crx * inv3;
        vy += scale * cry * inv3;
        vz += scale * crz * inv3;
    }
    out[0] = vx;
    out[1] = vy;
    out[2] = vz;
}

void vec_add_host(const double* a, const double* b, double* c, py::ssize_t n) {
#ifdef _OPENMP
#pragma omp parallel for if (n > 256)
#endif
    for (long long i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

double min_abs_host(const double* x, py::ssize_t n) {
    double dmin = std::numeric_limits<double>::infinity();
    if (n <= 0) {
        return dmin;
    }
#ifdef _OPENMP
#pragma omp parallel if (n > 256)
#endif
    {
        double thread_min = std::numeric_limits<double>::infinity();
#ifdef _OPENMP
#pragma omp for schedule(static) nowait
#endif
        for (long long i = 0; i < n; ++i) {
            thread_min = std::min(thread_min, std::abs(x[i]));
        }
#ifdef _OPENMP
#pragma omp critical
#endif
        { dmin = std::min(dmin, thread_min); }
    }
    return dmin;
}

void biot_savart_host(const double* p, py::ssize_t n, const double* q, py::ssize_t m, double gamma, double core, double* vel) {
    const double scale = gamma / (4.0 * PI);
    const double a2 = core * core;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) if (m > 64)
#endif
    for (long long mm = 0; mm < m; ++mm) {
        biot_one(p, n, q + 3 * mm, scale, a2, vel + 3 * mm);
    }
}

std::string host_backend_name() {
#ifdef _OPENMP
    return "openmp";
#else
    return "serial";
#endif
}

}  // namespace

py::array_t<double> vec_add(
    py::array_t<double, py::array::c_style | py::array::forcecast> a,
    py::array_t<double, py::array::c_style | py::array::forcecast> b,
    bool use_sycl,
    bool allow_sycl_cpu
) {
    (void)use_sycl;
    (void)allow_sycl_cpu;
    auto ba = a.request();
    auto bb = b.request();
    if (ba.size != bb.size) {
        throw std::runtime_error("vec_add: a and b must have the same length");
    }
    py::array_t<double> out(ba.size);
    auto bo = out.request();
    ScopedTimer timer;
    {
        py::gil_scoped_release release;
        vec_add_host(static_cast<const double*>(ba.ptr), static_cast<const double*>(bb.ptr), static_cast<double*>(bo.ptr), ba.size);
        timer.stop(host_backend_name());
    }
    return out;
}

double min_abs_py(
    py::array_t<double, py::array::c_style | py::array::forcecast> x,
    bool use_sycl,
    bool allow_sycl_cpu
) {
    (void)use_sycl;
    (void)allow_sycl_cpu;
    auto bx = x.request();
    ScopedTimer timer;
    double result = 0.0;
    {
        py::gil_scoped_release release;
        result = min_abs_host(static_cast<const double*>(bx.ptr), bx.size);
        timer.stop(host_backend_name());
    }
    return result;
}

py::array_t<double> biot_savart(
    py::array_t<double, py::array::c_style | py::array::forcecast> points,
    py::array_t<double, py::array::c_style | py::array::forcecast> queries,
    double gamma,
    double core,
    bool use_sycl,
    bool allow_sycl_cpu
) {
    (void)use_sycl;
    (void)allow_sycl_cpu;
    py::ssize_t n = 0, m = 0;
    const double* p = ptr_nx3(points, n);
    const double* q = ptr_nx3(queries, m);
    if (n < 2) {
        throw std::runtime_error("need >=2 filament points");
    }
    py::array_t<double> vel({m, static_cast<py::ssize_t>(3)});
    auto bv = vel.request();
    ScopedTimer timer;
    {
        py::gil_scoped_release release;
        biot_savart_host(p, n, q, m, gamma, core, static_cast<double*>(bv.ptr));
        timer.stop(host_backend_name());
    }
    return vel;
}

py::dict backend_info() {
    py::dict d;
    d["sycl_compiled"] = false;
    d["device_name"] = "host";
    d["is_gpu"] = false;
    d["queue_reused"] = false;
#ifdef _OPENMP
    d["openmp_compiled"] = true;
    d["openmp_max_threads"] = omp_get_max_threads();
#else
    d["openmp_compiled"] = false;
    d["openmp_max_threads"] = 1;
#endif
    d["last_backend"] = g_last_backend;
    d["last_kernel_ms"] = g_last_ms;
    d["backend"] = g_last_backend;
    d["gpu_via"] = "external_sycl_worker";
    return d;
}

bool probe_sycl_gpu() {
    // GPU lives in sst_sycl_worker.exe, not in this host .pyd.
    return false;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "Host/OpenMP Biot-Savart; GPU via external sst_sycl_worker.exe";
    m.def("vec_add", &vec_add, py::arg("a"), py::arg("b"), py::arg("use_sycl") = false, py::arg("allow_sycl_cpu") = false);
    m.def("min_abs", &min_abs_py, py::arg("x"), py::arg("use_sycl") = false, py::arg("allow_sycl_cpu") = false);
    m.def(
        "biot_savart",
        &biot_savart,
        py::arg("points"),
        py::arg("queries"),
        py::arg("gamma") = 1.0,
        py::arg("core") = 1.0,
        py::arg("use_sycl") = false,
        py::arg("allow_sycl_cpu") = false
    );
    m.def("backend_info", &backend_info);
    m.def("probe_sycl_gpu", &probe_sycl_gpu);
    m.attr("sycl_compiled") = false;
#ifdef _OPENMP
    m.attr("openmp_compiled") = true;
#else
    m.attr("openmp_compiled") = false;
#endif
}
