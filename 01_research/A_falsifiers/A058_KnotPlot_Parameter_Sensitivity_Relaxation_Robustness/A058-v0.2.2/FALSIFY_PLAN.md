# A058 v0.2.2 falsification plan

1. Runtime-calibrate seven slider defaults and five sector toggles.
2. Verify assignment-form setters and one safe trefoil export.
3. Freeze five anonymous sector references and seven anonymous multiplier ladders.
4. Run each condition in Damped + No-Collide using adaptive `go 32` windows; no fixed terminal relaxation count.
5. Stop only on four consecutive shape+scalar plateau windows after warm-up; otherwise mark non-converged at the safety cap.
6. Compare each slider to its own sector default reference.
7. Separate final embedded-shape response, bead-parametrization response, and convergence-time response.
8. Preserve diagnostic continuation after individual condition failures.
9. Reveal GUI slider and sector semantics only after frozen blind gates.
