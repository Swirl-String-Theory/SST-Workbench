from sst_modal_clock.focus_runner import parse_args


def test_exact_user_commandline_parses_as_python_argv():
    ns = parse_args(["L2a1", "--libraries=Gilbert,Katlas", "--min-carriers=2", "--kind=links"])
    assert ns.topology == "L2a1"
    assert ns.libraries == "Gilbert,Katlas"
    assert ns.min_carriers == 2
    assert ns.kind == "links"


def test_spaced_option_form_also_works():
    ns = parse_args(["L2a1", "--libraries", "Gilbert,Katlas", "--min-carriers", "2", "--kind", "links"])
    assert ns.libraries == "Gilbert,Katlas"
    assert ns.min_carriers == 2
    assert ns.kind == "links"
