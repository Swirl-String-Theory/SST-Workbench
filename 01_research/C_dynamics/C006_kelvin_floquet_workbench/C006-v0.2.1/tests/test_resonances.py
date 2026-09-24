from sst_kelvin_workbench.kelvin import enumerate_resonances


def test_resonance_enumerator_conserves_mode_sum():
    freqs={2:1.2,3:2.1,4:3.6,5:5.4,6:7.5}
    for order in [4,6]:
        rows=enumerate_resonances(freqs,order,top_n=30)
        assert rows
        for r in rows:
            assert sum(r['incoming']) == sum(r['outgoing'])
            assert sorted(r['incoming']) != sorted(r['outgoing'])
