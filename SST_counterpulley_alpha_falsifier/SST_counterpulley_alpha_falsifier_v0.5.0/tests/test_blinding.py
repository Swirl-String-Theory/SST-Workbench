from pathlib import Path
import sst_counterpulley.dynamics as dynamics
import sst_counterpulley.blind_gates as blind_gates

def test_blind_modules_have_no_alpha_target_literal():
    for mod in (dynamics,blind_gates):
        text=Path(mod.__file__).read_text(encoding='utf-8')
        assert '137.035' not in text
        assert 'ALPHA_INV_BENCHMARK' not in text
