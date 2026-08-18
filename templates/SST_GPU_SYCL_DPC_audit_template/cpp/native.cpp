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
#ifdef SST_HAVE_SYCL
#include <sycl/sycl.hpp>
#include <memory>
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
    // OpenMP 2.0 (MSVC /openmp) has no reduction(min:); thread-local min + merge.
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

#ifdef SST_HAVE_SYCL
struct QueueState {
    std::unique_ptr<sycl::queue> queue;
    std::string device_name{"none"};
    bool is_gpu = false;
    bool reused = false;
};

QueueState g_queue;

QueueState* peek_queue() {
    return g_queue.queue ? &g_queue : nullptr;
}

QueueState& queue_state(bool allow_cpu) {
    if (g_queue.queue) {
        g_queue.reused = true;
        if (!g_queue.is_gpu && !allow_cpu) {
            throw std::runtime_error("SYCL queue is CPU-only; pass allow_sycl_cpu=True or use a GPU.");
        }
        return g_queue;
    }
    sycl::device dev;
    try {
        dev = sycl::device(sycl::gpu_selector_v);
    } catch (...) {
        if (!allow_cpu) {
            throw std::runtime_error("No SYCL GPU visible (check ONEAPI_DEVICE_SELECTOR=level_zero:0).");
        }
        dev = sycl::device(sycl::default_selector_v);
    }
    g_queue.queue = std::make_unique<sycl::queue>(dev);
    g_queue.device_name = dev.get_info<sycl::info::device::name>();
    g_queue.is_gpu = dev.is_gpu();
    return g_queue;
}

void vec_add_sycl(const double* a, const double* b, double* c, py::ssize_t n, bool allow_cpu) {
    auto& st = queue_state(allow_cpu);
    sycl::buffer<double, 1> A(const_cast<double*>(a), sycl::range<1>(static_cast<size_t>(n)));
    sycl::buffer<double, 1> B(const_cast<double*>(b), sycl::range<1>(static_cast<size_t>(n)));
    sycl::buffer<double, 1> C(c, sycl::range<1>(static_cast<size_t>(n)));
    st.queue->submit([&](sycl::handler& h) {
        auto accA = A.get_access<sycl::access_mode::read>(h);
        auto accB = B.get_access<sycl::access_mode::read>(h);
        auto accC = C.get_access<sycl::access_mode::write>(h);
        h.parallel_for(sycl::range<1>(static_cast<size_t>(n)), [=](sycl::id<1> i) { accC[i] = accA[i] + accB[i]; });
    });
    st.queue->wait();
}

double min_abs_sycl(const double* x, py::ssize_t n, bool allow_cpu) {
    if (n <= 0) {
        return std::numeric_limits<double>::infinity();
    }
    auto& st = queue_state(allow_cpu);
    double result = std::numeric_limits<double>::infinity();
    {
        sycl::buffer<double, 1> X(const_cast<double*>(x), sycl::range<1>(static_cast<size_t>(n)));
        sycl::buffer<double, 1> R(&result, sycl::range<1>(1));
        st.queue->submit([&](sycl::handler& h) {
            auto acc = X.get_access<sycl::access_mode::read>(h);
            auto red = sycl::reduction(R, h, sycl::minimum<double>());
            h.parallel_for(sycl::range<1>(static_cast<size_t>(n)), red, [=](sycl::id<1> i, auto& minv) {
                minv.combine(sycl::fabs(acc[i]));
            });
        });
        st.queue->wait();
    }
    return result;
}

void biot_savart_sycl(
    const double* p,
    py::ssize_t n,
    const double* q,
    py::ssize_t m,
    double gamma,
    double core,
    double* vel,
    bool allow_cpu
) {
    auto& st = queue_state(allow_cpu);
    const double scale = gamma / (4.0 * PI);
    const double a2 = core * core;
    const size_t N = static_cast<size_t>(n);
    const size_t M = static_cast<size_t>(m);
    // Per-call buffers on a process-lifetime queue. Sticky filament: swap for USM malloc_device.
    sycl::buffer<double, 1> P(const_cast<double*>(p), sycl::range<1>(N * 3));
    sycl::buffer<double, 1> Q(const_cast<double*>(q), sycl::range<1>(M * 3));
    sycl::buffer<double, 1> V(vel, sycl::range<1>(M * 3));
    st.queue->submit([&](sycl::handler& h) {
        auto accP = P.get_access<sycl::access_mode::read>(h);
        auto accQ = Q.get_access<sycl::access_mode::read>(h);
        auto accV = V.get_access<sycl::access_mode::write>(h);
        h.parallel_for(sycl::range<1>(M), [=](sycl::id<1> mm) {
            const size_t i = mm[0];
            const double x = accQ[3 * i];
            const double y = accQ[3 * i + 1];
            const double z = accQ[3 * i + 2];
            double vx = 0.0, vy = 0.0, vz = 0.0;
            for (size_t s = 0; s < N; ++s) {
                const size_t t = (s + 1) % N;
                const double ax = accP[3 * s], ay = accP[3 * s + 1], az = accP[3 * s + 2];
                const double bx = accP[3 * t], by = accP[3 * t + 1], bz = accP[3 * t + 2];
                const double dlx = bx - ax, dly = by - ay, dlz = bz - az;
                const double mx = 0.5 * (ax + bx), my = 0.5 * (ay + by), mz = 0.5 * (az + bz);
                const double rx = x - mx, ry = y - my, rz = z - mz;
                const double D = rx * rx + ry * ry + rz * rz + a2;
                const double inv3 = 1.0 / (D * sycl::sqrt(D));
                const double crx = dly * rz - dlz * ry;
                const double cry = dlz * rx - dlx * rz;
                const double crz = dlx * ry - dly * rx;
                vx += scale * crx * inv3;
                vy += scale * cry * inv3;
                vz += scale * crz * inv3;
            }
            accV[3 * i] = vx;
            accV[3 * i + 1] = vy;
            accV[3 * i + 2] = vz;
        });
    });
    st.queue->wait();
}
#endif

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
#ifdef SST_HAVE_SYCL
        if (use_sycl) {
            vec_add_sycl(static_cast<const double*>(ba.ptr), static_cast<const double*>(bb.ptr), static_cast<double*>(bo.ptr), ba.size, allow_sycl_cpu);
            timer.stop("sycl");
        } else
#else
        (void)use_sycl;
        (void)allow_sycl_cpu;
#endif
        {
            vec_add_host(static_cast<const double*>(ba.ptr), static_cast<const double*>(bb.ptr), static_cast<double*>(bo.ptr), ba.size);
            timer.stop(host_backend_name());
        }
    }
    return out;
}

double min_abs_py(
    py::array_t<double, py::array::c_style | py::array::forcecast> x,
    bool use_sycl,
    bool allow_sycl_cpu
) {
    auto bx = x.request();
    ScopedTimer timer;
    double result = 0.0;
    {
        py::gil_scoped_release release;
#ifdef SST_HAVE_SYCL
        if (use_sycl) {
            result = min_abs_sycl(static_cast<const double*>(bx.ptr), bx.size, allow_sycl_cpu);
            timer.stop("sycl");
        } else
#else
        (void)use_sycl;
        (void)allow_sycl_cpu;
#endif
        {
            result = min_abs_host(static_cast<const double*>(bx.ptr), bx.size);
            timer.stop(host_backend_name());
        }
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
#ifdef SST_HAVE_SYCL
        if (use_sycl) {
            biot_savart_sycl(p, n, q, m, gamma, core, static_cast<double*>(bv.ptr), allow_sycl_cpu);
            timer.stop("sycl");
        } else
#else
        (void)use_sycl;
        (void)allow_sycl_cpu;
#endif
        {
            biot_savart_host(p, n, q, m, gamma, core, static_cast<double*>(bv.ptr));
            timer.stop(host_backend_name());
        }
    }
    return vel;
}

py::dict backend_info() {
    py::dict d;
#ifdef SST_HAVE_SYCL
    d["sycl_compiled"] = true;
    if (QueueState* st = peek_queue()) {
        d["device_name"] = st->device_name;
        d["is_gpu"] = st->is_gpu;
        d["queue_reused"] = st->reused;
    } else {
        try {
            sycl::device dev(sycl::gpu_selector_v);
            d["device_name"] = dev.get_info<sycl::info::device::name>();
            d["is_gpu"] = dev.is_gpu();
        } catch (...) {
            d["device_name"] = "no-gpu-yet";
            d["is_gpu"] = false;
        }
        d["queue_reused"] = false;
    }
#else
    d["sycl_compiled"] = false;
    d["device_name"] = "host";
    d["is_gpu"] = false;
    d["queue_reused"] = false;
#endif
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
    return d;
}

bool probe_sycl_gpu() {
#ifdef SST_HAVE_SYCL
    try {
        sycl::device dev(sycl::gpu_selector_v);
        return dev.is_gpu();
    } catch (...) {
        return false;
    }
#else
    return false;
#endif
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "GPU-first SYCL/OpenMP Biot-Savart template (replace biot_savart with your kernel).";
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
#ifdef SST_HAVE_SYCL
    m.attr("sycl_compiled") = true;
#else
    m.attr("sycl_compiled") = false;
#endif
#ifdef _OPENMP
    m.attr("openmp_compiled") = true;
#else
    m.attr("openmp_compiled") = false;
#endif
}
