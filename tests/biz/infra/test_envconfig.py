from biz.infra.envconfig import Setting, audit_env, check


def _one(raw, **kw):
    return check(Setting("X", **kw), raw)


def test_issues():
    assert _one("auto").issue == "no_digits" and _one("auto").c_value == 0
    f = _one("30s")
    assert (f.issue, f.c_value, f.py_value, f.diverges) == ("trailing", 30, None, True)
    f = _one("4294967296")
    assert (f.issue, f.c_value, f.py_value) == ("clamped", 2**31 - 1, 4294967296)
    f = _one("1_000")
    assert (f.issue, f.c_value, f.py_value) == ("trailing", 1, 1000)
    assert _one("-1", bits=8, signed=False).issue == "clamped"
    assert _one("0", min=1).issue == "out_of_range"
    assert _one("300", max=256).issue == "out_of_range"


def test_ok_and_whitespace():
    f = _one(" \t8080\n", bits=16, signed=False)
    assert (f.issue, f.c_value, f.py_value, f.diverges) == ("ok", 8080, 8080, False)
    assert _one("16 ").issue == "ok"


def test_missing():
    assert check(Setting("X"), None).issue == "missing"
    f = check(Setting("X", required=False), None)
    assert f.issue == "ok" and not f.diverges


def test_unicode_digits_diverge():
    f = _one("٣")                       # int() понимает арабско-индийскую тройку, atoi — нет
    assert (f.issue, f.c_value, f.py_value, f.diverges) == ("no_digits", 0, 3, True)


def test_audit_env_order():
    env = {"B": "2", "A": "x"}
    out = audit_env(env, [Setting("A"), Setting("B"), Setting("C")])
    assert [(f.name, f.issue) for f in out] == [("A", "no_digits"), ("B", "ok"), ("C", "missing")]


def test_demo_runs(capsys):
    from biz.infra.envconfig import demo
    demo.main()
    assert "TIMEOUT_SEC" in capsys.readouterr().out
