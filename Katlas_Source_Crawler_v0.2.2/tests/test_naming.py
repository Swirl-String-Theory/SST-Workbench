from katlas_source.naming import parse_identity, object_relpath

def main():
    cases = {
        ("knot", "3_1"): "knots/03/3_1",
        ("knot", "9_2"): "knots/09/9_2",
        ("knot", "10_51"): "knots/10/rolfsen/0051-0100/10_51",
        ("knot", "K11a367"): "knots/11/alternating/0351-0400/K11a367",
        ("knot", "K12n888"): "knots/12/nonalternating/0851-0900/K12n888",
        ("link", "L9a55"): "links/09/L9a55",
        ("link", "L10n113"): "links/10/nonalternating/0101-0150/L10n113",
        ("link", "L12a1"): "links/12/alternating/0001-0050/L12a1",
    }
    for (kind, kid), expected in cases.items():
        ident = parse_identity(kind, kid); assert ident is not None
        got = object_relpath(ident).as_posix(); assert got == expected, (kid, got, expected)
    ident = parse_identity("knot", "L6a4"); assert ident is not None and ident.kind == "link"
    print("PASS naming tests")

if __name__ == "__main__": main()
