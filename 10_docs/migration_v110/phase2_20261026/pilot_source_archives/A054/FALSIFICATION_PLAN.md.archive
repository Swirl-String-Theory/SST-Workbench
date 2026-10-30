# A054-v0.5.1 falsification plan

The decisive question remains whether one globally frozen, target-free state selector maps independently sourced representatives of the same topology to the same stationary and stable endpoint.

v0.5.1 changes no provider/topology scientific threshold from v0.5.0. It changes the numerical definition of the variational test so the object being differentiated is exactly the object accepted by the line search and later tested for local stability:

\[
U_c(q;X)=\widehat H_a(\mathcal N[\mathcal R(X+\delta X(q))]).
\]

For each carrier, the registered global Armijo/trust-region ladder must either (a) find a topology-preserving descent step, (b) reach stationarity, (c) demonstrate a topology-proxy constraint block, or (d) return `UNRESOLVED_NUMERICAL`. Case (d) is not a scientific FAIL.

For stationary endpoints, local stability is promotable only if Hessians at `eps`, `eps/2`, and `eps/4` have a consistent sign class and the two finest matrices satisfy the preregistered relative-L2 tolerance. Ringdown then uses the same constrained objective.

Scientific FAIL never aborts later diagnostics. Infrastructure/provenance failures remain fail-closed.

Resolved negative outcomes are: a numerically qualified selector does not reach the registered stationary fraction; resolved providers remain separated; a converged stationary Hessian is a saddle; bounded ringdown fails; provider-spread collapse fails; or topology/clearance proxies block the registered path. Numerical inability to establish descent or Hessian sign is UNRESOLVED, not negative physical evidence.
