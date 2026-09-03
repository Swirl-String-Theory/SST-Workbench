try:
    from ._native import velocity, energy_sum
    NATIVE_AVAILABLE=True
except Exception:
    NATIVE_AVAILABLE=False
    velocity=energy_sum=None
