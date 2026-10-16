# A058 — Getter and reset-default qualification (v0.2.10)

Numerical defaults are measured in the corresponding sector context. The user-confirmed reset-default value for anonymous S3 is **1.40** and sector R2 is reset **OFF**, while its active reference is **ON**. S3 is now required to have a numeric runtime getter alias, specified only in the private axis map; setter-only verification is discontinued for this build. Sector getter aliases for R2 and R3 are similarly read back and checked.

KnotPlot parameter dumps show six decimal places. The maximum display-consistent difference between setter and getter is half a display unit, i.e. **5 × 10^-7**, with minimal floating-point parse slack. This proves **rounded getter agreement**, NOT exact internal FP64 assignment. Missing getters, wrong switch states, explicit unsafe geometry and runtime errors remain hard failures.

A historical run may be imported with an independently computed, SHA-bound qualification overlay. Import does not alter the original BLIND gate ledger or original `runlog.json`.
