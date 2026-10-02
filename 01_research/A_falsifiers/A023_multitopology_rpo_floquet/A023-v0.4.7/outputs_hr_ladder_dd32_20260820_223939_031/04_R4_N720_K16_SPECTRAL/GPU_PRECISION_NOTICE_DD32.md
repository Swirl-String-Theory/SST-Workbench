# DD32 / FP32x2 precision notice

This campaign used experimental double-single arithmetic: every device scalar is represented by two FP32 values (hi + lo), with compensated addition/multiplication/division/sqrt and DD accumulation. This is **not IEEE FP64**. CPU/OpenMP FP64 remains the reference until campaign-level parity is demonstrated.
