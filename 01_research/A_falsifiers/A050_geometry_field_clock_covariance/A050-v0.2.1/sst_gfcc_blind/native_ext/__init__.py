try:
    from ._native import filament_field as _filament_field
    HAVE_NATIVE = True
except Exception:
    _filament_field = None
    HAVE_NATIVE = False

def filament_field(eval_points, curve_points, core):
    if not HAVE_NATIVE:
        raise RuntimeError("native extension is not built")
    return _filament_field(eval_points, curve_points, core)
