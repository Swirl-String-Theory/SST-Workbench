from pathlib import Path
import sst_counterpulley.orbit as orbit
import sst_counterpulley.monodromy as monodromy
import sst_counterpulley.blind_gates as gates


def test_v04_blind_modules_have_no_alpha_target():
    needle='137.'+'035'
    symbol='ALPHA_INV'+'_BENCHMARK'
    for mod in (orbit,monodromy,gates):
        text=Path(mod.__file__).read_text(encoding='utf-8')
        assert needle not in text
        assert symbol not in text
