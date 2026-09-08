try:
    from ._native import biot_savart_velocity
    HAVE_NATIVE=True
except Exception:
    biot_savart_velocity=None
    HAVE_NATIVE=False
