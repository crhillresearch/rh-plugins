from pathlib import Path
import importlib.util
import sys
from fractions import Fraction

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("ce_backend",ROOT/"backend.py")
B=importlib.util.module_from_spec(spec); sys.modules[spec.name]=B; spec.loader.exec_module(B)


def test_short_curve_group_law_and_membership():
    E=B.WeierstrassModel.from_json('["0","0","0","-1","0"]')
    P=(Fraction(0),Fraction(0))
    assert E.on_curve(P)
    assert E.add(P,P) is B.INF


def test_generalized_curve_formula():
    E=B.WeierstrassModel.from_json('["0","0","1","-1","0"]')
    P=(Fraction(0),Fraction(0))
    assert E.on_curve(P)
    R=E.add(P,P)
    assert R is not B.INF
    assert E.on_curve(R)


def test_equation_text_generalized():
    E=B.WeierstrassModel.from_json('["1","2","3","4","5"]')
    text=E.equation_text()
    assert "xy" in text and "x²" in text and "y" in text


def test_load_curve_converts_sqlite_row_to_plain_dict():
    import sqlite3
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.execute("""CREATE TABLE curves (
        id INTEGER PRIMARY KEY,
        a_invariants_json TEXT,
        exact_rank INTEGER,
        descent_lower INTEGER,
        generic_lower INTEGER
    )""")
    db.execute("INSERT INTO curves VALUES (?, ?, ?, ?, ?)", (1, '["0","0","0","-1","0"]', None, 1, None))
    row,model=B.load_curve(db,1)
    assert type(row) is dict
    assert row["id"]==1
    assert model.on_curve((Fraction(0),Fraction(0)))


def test_exact_pair_cache_contains_third_intersection_and_sum():
    E=B.WeierstrassModel.from_json('["0","0","0","-1","0"]')
    # y^2=x^3-x: P=(-1,0), Q=(0,0), P+Q=(1,0); third intersection is also (1,0).
    pts=[
        B.PointRecord("1",Fraction(-1),Fraction(0),exact_verified=True),
        B.PointRecord("2",Fraction(0),Fraction(0),exact_verified=True),
    ]
    pairs,cap=B.exact_pair_constructions(E,pts,max_points=10)
    assert cap==2
    item=pairs["1|2"]
    assert item["line"]["lambda_exact"]=="0"
    assert item["third"]["x_exact"]=="1"
    assert item["third"]["y_exact"]=="0"
    assert item["result"]["x_exact"]=="1"
    assert item["result"]["y_exact"]=="0"


def test_generalized_negation_in_pair_cache_is_exact():
    E=B.WeierstrassModel.from_json('["0","0","1","-1","0"]')
    P=B.PointRecord("1",Fraction(0),Fraction(0),exact_verified=True)
    pairs,_=B.exact_pair_constructions(E,[P],max_points=2)
    item=pairs["1|1"]
    if item["result"] is not None:
        R=(B.Q(item["third"]["x_exact"]), B.Q(item["third"]["y_exact"]))
        S=(B.Q(item["result"]["x_exact"]), B.Q(item["result"]["y_exact"]))
        assert E.negate(R)==S
        assert E.on_curve(R) and E.on_curve(S)


def test_point_categories_are_conservative():
    g=B.PointRecord("g",Fraction(0),Fraction(0),role="generator",exact_verified=True)
    c=B.PointRecord("c",Fraction(0),Fraction(0),role="candidate",independence_status="unknown",exact_verified=True)
    r=B.PointRecord("r",Fraction(0),Fraction(0),role="candidate",independence_status="rigorous_independent",exact_verified=True)
    assert g.is_generator and g.in_selected_subgroup
    assert not c.is_generator and not c.in_selected_subgroup
    assert r.in_selected_subgroup


def test_smart_bounds_ignore_extreme_outlier_but_fit_all_does_not():
    E=B.WeierstrassModel.from_json('["0","0","0","-1","0"]')
    pts=[B.PointRecord(str(i),Fraction(i),Fraction(0)) for i in range(10)]
    pts.append(B.PointRecord("x",Fraction(10**12),Fraction(0)))
    smart=B.choose_bounds(E,pts,mode="Smart")
    all_bounds=B.choose_bounds(E,pts,mode="All stored points")
    assert smart[1] < 100
    assert all_bounds[1] > 10**11


def test_plot_payload_contains_filters_and_bounded_pair_cache():
    E=B.WeierstrassModel.from_json('["0","0","0","-1","0"]')
    pts=[
        B.PointRecord("1",Fraction(-1),Fraction(0),role="generator",rigorous_independent=True),
        B.PointRecord("2",Fraction(0),Fraction(0),role="candidate"),
        B.PointRecord("3",Fraction(1),Fraction(0),role="candidate"),
    ]
    payload=B.plot_payload(E,pts,bounds=(-3,3),pair_cache_points=2)
    assert len(payload["points"])==3
    assert payload["pair_cache_points"]==2
    assert payload["points"][0]["is_generator"] is True
    assert payload["points"][0]["in_subgroup"] is True
    assert payload["points"][2]["interactive"] is False
    assert "1|2" in payload["pair_constructions"]
    assert "1|3" not in payload["pair_constructions"]


def test_qstr_formats_coordinates_beyond_python_int_string_limit():
    digit_limit = sys.get_int_max_str_digits() if hasattr(sys, "get_int_max_str_digits") else None
    huge = Fraction(10**5000 + 1, 1)
    text = B.qstr(huge)
    assert len(text) == 5001
    assert text.startswith("1")
    assert text.endswith("1")
    assert text.count("/") == 0

    rational = Fraction(10**5000 + 1, 10**4500 + 3)
    text = B.qstr(rational)
    numerator, denominator = text.split("/", 1)
    assert len(numerator) > 4300
    assert len(denominator) > 4300
    if digit_limit is not None:
        assert sys.get_int_max_str_digits() == digit_limit
