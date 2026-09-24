import numpy as np


def wrap_phase(x):
    return (float(x) + np.pi) % (2.0 * np.pi) - np.pi


def circulation_delay_control(n=2048, mode=7, phase_rad=0.73):
    """
    Dimensionless analytic periodic circulation control.

    Gamma(t) = sin(mode*t), t in [0,2*pi).
    The delayed state is Gamma(t-tau), with mode*tau = phase_rad.
    """
    n = int(n)
    mode = int(mode)
    t = 2.0 * np.pi * np.arange(n, dtype=float) / n
    tau = float(phase_rad) / float(mode)
    gamma = np.sin(mode * t)
    gamma_delayed = np.sin(mode * (t - tau))
    memory = gamma - gamma_delayed

    c0 = np.fft.fft(gamma)[mode]
    cd = np.fft.fft(gamma_delayed)[mode]
    recovered = wrap_phase(np.angle(c0 / cd))
    target = wrap_phase(phase_rad)
    phase_error = abs(wrap_phase(recovered - target))

    gamma_zero_delay = np.sin(mode * (t - 0.0))
    zero_memory = gamma - gamma_zero_delay

    return {
        "tau_dimensionless": tau,
        "target_phase_rad": target,
        "recovered_phase_rad": recovered,
        "phase_error_rad": phase_error,
        "memory_rms": float(np.sqrt(np.mean(memory * memory))),
        "zero_delay_memory_rms": float(np.sqrt(np.mean(zero_memory * zero_memory))),
    }
