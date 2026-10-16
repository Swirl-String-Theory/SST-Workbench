# Runtime defaults and evidence limitation — v0.2.8

A058 uses numerical defaults reported from a slider's enabled-sector context, except S3 where the current build does not return a getter. The user confirmed a reset default of **1.40** for S3 and **OFF** for R2. The numeric S3 setter must be accepted without `unknown command`; without readback that does not certify internal application.

R2-ON with S3=1.40 is the reference for both its numeric sweeps. R2-OFF at the same numeric defaults is a **distinct matched control**, not a value on a multiplicative strength ladder. If the reset parameter dump reports a contradictory value, installation rejects the run.
