# sst55_numeric_demo.py
# Reproducible numerical demonstration for SST-55
# Generates:
#   fig_SST55_branch_survival.pdf
#   fig_SST55_branch_count.pdf
#   fig_SST55_time_domain.pdf
#
# Dependencies: numpy, matplotlib
#
# Usage:
#   python3 sst55_numeric_demo.py

import math
import numpy as np
import matplotlib.pyplot as plt

def roots_theta(theta0: float, K: float, n_grid: int = 12000):
    # Solve g(theta)=theta-theta0+K*sin(theta)=0 for theta in [theta0-K, theta0+K]
    a, b = theta0 - K, theta0 + K
    if K == 0.0:
        return [theta0]

    xs = np.linspace(a, b, n_grid)
    g  = xs - theta0 + K*np.sin(xs)

    roots = []

    # Bracketed roots (sign changes)
    for i in range(len(xs)-1):
        if g[i] * g[i+1] < 0:
            lo, hi = xs[i], xs[i+1]
            glo, ghi = g[i], g[i+1]
            for _ in range(70):
                mid = 0.5*(lo+hi)
                gmid = mid - theta0 + K*math.sin(mid)
                if glo*gmid <= 0:
                    hi, ghi = mid, gmid
                else:
                    lo, glo = mid, gmid
            roots.append(0.5*(lo+hi))

    # Newton seeds (captures tangencies near folds)
    for guess in np.linspace(a, b, 260):
        th = float(guess)
        for _ in range(40):
            f  = th - theta0 + K*math.sin(th)
            df = 1.0 + K*math.cos(th)
            if abs(df) < 1e-8:
                break
            th2 = th - f/df
            if th2 < a-1.0 or th2 > b+1.0:
                break
            if abs(th2-th) < 1e-12:
                break
            th = th2
        if abs(th - theta0 + K*math.sin(th)) < 1e-8:
            roots.append(th)

    # Deduplicate
    roots = sorted(roots)
    dedup = []
    for r in roots:
        if not dedup or abs(r - dedup[-1]) > 2e-3:
            dedup.append(r)
    return dedup

def is_stable(theta: float, K: float) -> bool:
    # Stability inequality: 1 + K*cos(theta) > 0
    return 1.0 + K*math.cos(theta) > 0.0

def scan_branches(theta0: float = 0.0, K_max: float = 16.0, K_step: float = 0.2):
    Ks = np.arange(0.0, K_max + 0.5*K_step, K_step)
    stable_pts = []
    unstable_pts = []
    n_stable = []

    for K in Ks:
        rts = roots_theta(theta0, float(K))
        st = 0
        for th in rts:
            if is_stable(th, float(K)):
                stable_pts.append((K, th))
                st += 1
            else:
                unstable_pts.append((K, th))
        n_stable.append((K, st))

    return np.array(stable_pts), np.array(unstable_pts), np.array(n_stable)

def simulate_dde(omega0: float = 0.0, kappa: float = 6.0, tau: float = 1.0,
                 Omega_init: float = 6.0, dt: float = 1e-3, T: float = 14.0):
    # Method-of-steps Euler integration for:
    #   dphi/dt = omega0 + kappa*sin(phi(t-tau) - phi(t))
    # with history phi(t)=Omega_init*t on t in [-tau,0].
    n_hist = int(tau/dt) + 1
    t_hist = np.linspace(-tau, 0.0, n_hist)
    phi_hist = Omega_init * t_hist

    ts = list(t_hist)
    phis = list(phi_hist)

    t = 0.0
    while t < T - 1e-12:
        phi = phis[-1]

        t_delay = t - tau
        if t_delay <= ts[0]:
            phi_delay = Omega_init * t_delay
        else:
            idx = int((t_delay - ts[0]) / dt)
            idx = min(idx, len(ts) - 2)
            t0, t1 = ts[idx], ts[idx+1]
            p0, p1 = phis[idx], phis[idx+1]
            w = (t_delay - t0) / (t1 - t0)
            phi_delay = (1.0 - w)*p0 + w*p1

        dphi = omega0 + kappa*math.sin(phi_delay - phi)
        phis.append(phi + dt*dphi)
        ts.append(t + dt)
        t += dt

    ts = np.array(ts)
    phis = np.array(phis)
    omega_inst = np.diff(phis) / dt
    t_mid = ts[1:]
    return t_mid, omega_inst

def main():
    # --- Branch scan ---
    theta0 = 0.0
    stable_pts, unstable_pts, n_stable = scan_branches(theta0=theta0, K_max=16.0, K_step=0.2)

    # Figure 1: branch survival
    plt.figure()
    if len(stable_pts) > 0:
        plt.plot(stable_pts[:,0], stable_pts[:,1], '.', label='stable roots')
    if len(unstable_pts) > 0:
        plt.plot(unstable_pts[:,0], unstable_pts[:,1], 'o', fillstyle='none', label='unstable roots')
    plt.xlabel('K = kappa*tau')
    plt.ylabel('theta = Omega*tau')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig('fig_SST55_branch_survival.pdf')

    # Figure 2: number of stable branches
    plt.figure()
    plt.plot(n_stable[:,0], n_stable[:,1], '.-')
    plt.xlabel('K = kappa*tau')
    plt.ylabel('number of stable branches')
    plt.ylim(bottom=0)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('fig_SST55_branch_count.pdf')

    # --- Time-domain verification ---
    omega0, kappa, tau = 0.0, 6.0, 1.0
    t_mid, omega_inst = simulate_dde(omega0=omega0, kappa=kappa, tau=tau, Omega_init=6.0, dt=1e-3, T=14.0)

    # Predicted stable positive-frequency root Omega* (solve Omega = omega0 - kappa*sin(Omega*tau))
    K = kappa*tau
    rts = roots_theta(theta0, K)
    stable_pos = [th for th in rts if is_stable(th, K) and th > 0.0]
    theta_star = stable_pos[0] if stable_pos else float('nan')
    Omega_star = theta_star / tau
    print(f"Predicted Omega* = {Omega_star:.6f} rad/s (theta*={theta_star:.6f})")

    # Estimate asymptotic Omega from last 20% of trajectory
    mask = t_mid > 0.8*t_mid.max()
    Omega_est = float(np.mean(omega_inst[mask]))
    print(f"Simulated Omega  = {Omega_est:.6f} rad/s  (std={float(np.std(omega_inst[mask])):.3e})")

    plt.figure()
    plt.plot(t_mid, omega_inst, '-', linewidth=1.0)
    if math.isfinite(Omega_star):
        plt.axhline(Omega_star, linestyle='--', linewidth=1.0, label=r'$\Omega_\star$ (pred.)')
        plt.legend()
    plt.xlabel('t')
    plt.ylabel('dphi/dt')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('fig_SST55_time_domain.pdf')

if __name__ == "__main__":
    main()
