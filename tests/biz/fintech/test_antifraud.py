from datetime import datetime, timedelta

import pytest

from biz.fintech.antifraud import CardTestingDetector, CardTestingRule, PaymentAttempt, Risk, Status

T0 = datetime(2026, 10, 24, 12, 0)


def _attempts(source, cards, declined=(), start=0):
    """cards: строка, каждый символ — отдельная карта. declined: индексы отклонённых попыток."""
    return [
        PaymentAttempt(f"{source}-{k}", T0 + timedelta(seconds=start + k), source, f"fp-{c}", f"000{c}"[-4:],
                       100, Status.DECLINED if k in declined else Status.APPROVED)
        for k, c in enumerate(cards)
    ]


def test_card_testing_is_high_risk():
    att = _attempts("ip", "abcdefgh", declined=range(7))
    [al] = CardTestingDetector(CardTestingRule(min_cards=5)).scan(att)
    assert al.risk is Risk.HIGH and al.action == "block"
    assert al.distinct_cards == 8 and al.declines == 7


def test_normal_customer_no_alert():
    att = _attempts("user", "aababbab")  # две свои карты
    assert CardTestingDetector().scan(att) == []


def test_many_cards_but_approved_is_medium():
    [al] = CardTestingDetector(CardTestingRule(min_cards=5)).scan(_attempts("office", "abcde"))
    assert al.risk is Risk.MEDIUM and al.action == "review"


def test_window_is_the_longest_run():
    # Обычные покупки картой «a», потом перебор b..g, потом снова «a».
    att = _attempts("ip", "aaabcdefgaa", declined={3, 4, 5, 6, 7, 8})
    [al] = CardTestingDetector(CardTestingRule(min_cards=5)).scan(att)
    assert [a.card_fp for a in al.attempts] == [f"fp-{c}" for c in "abcdefg"]


def test_evasion_by_repeating_each_card():
    att = _attempts("ip", "aabbccddeeff", declined=range(12))
    assert CardTestingDetector(CardTestingRule(min_cards=5, max_repeats=1)).scan(att) == []
    [al] = CardTestingDetector(CardTestingRule(min_cards=5, max_repeats=2)).scan(att)
    assert al.distinct_cards == 6 and len(al.attempts) == 12


def test_order_and_grouping():
    # События вперемешку и из разных источников: детектор сам группирует и сортирует по времени.
    fraud = _attempts("bad", "abcdef", declined=range(6))
    office = _attempts("office", "uvwxyz")
    mixed = [x for pair in zip(reversed(fraud), office) for x in pair]
    alerts = CardTestingDetector(CardTestingRule(min_cards=5)).scan(mixed)
    assert [al.source for al in alerts] == ["bad", "office"]  # HIGH раньше MEDIUM
    assert [a.id for a in alerts[0].attempts] == [f"bad-{k}" for k in range(6)]


def test_sources_do_not_mix():
    # По 3 карты у двух источников: вместе 6, но по отдельности ниже порога.
    att = _attempts("ip1", "abc") + _attempts("ip2", "def")
    assert CardTestingDetector(CardTestingRule(min_cards=5)).scan(att) == []


@pytest.mark.parametrize("kw", [{"min_cards": 1}, {"max_repeats": 0}, {"high_decline_rate": 1.5}])
def test_rule_validation(kw):
    with pytest.raises(ValueError):
        CardTestingRule(**kw)


# ---------- пакетный путь == по одному источнику; потоковый детектор ----------
import random  # noqa: E402

from biz.fintech.antifraud import StreamingCardTestingDetector  # noqa: E402


def _random_stream(seed, sources=60, per_source=40):
    rng = random.Random(seed)
    out = []
    for s in range(sources):
        cards = "abcdefghij"[: rng.randint(1, 10)]
        seq = "".join(rng.choice(cards) for _ in range(rng.randint(1, per_source)))
        out += _attempts(f"src{s}", seq, declined={k for k in range(len(seq)) if rng.random() < 0.6}, start=s)
    return out


@pytest.mark.parametrize("k", [1, 2])
def test_batch_scan_equals_per_source(k):
    att = _random_stream(k)
    det = CardTestingDetector(CardTestingRule(min_cards=4, max_repeats=k))
    by_src = {}
    for a in sorted(att, key=lambda a: (a.ts, a.id)):
        by_src.setdefault(a.source, []).append(a)
    per_source = [al for al in (det.check_source(g) for g in by_src.values()) if al]
    key = lambda al: (al.source, al.risk, [a.id for a in al.attempts])  # noqa: E731
    assert sorted(map(key, det.scan(att))) == sorted(map(key, per_source))


def test_streaming_same_sources_as_batch_for_k1():
    # При k = 1 «есть окно с >= min_cards разными картами» ⇔ «самое длинное окно >= min_cards»,
    # поэтому множества подозрительных источников совпадают.
    att = sorted(_random_stream(5), key=lambda a: (a.ts, a.id))
    rule = CardTestingRule(min_cards=4)
    stream = StreamingCardTestingDetector(rule)
    streamed = {al.source for a in att if (al := stream.observe(a))}
    assert streamed == {al.source for al in CardTestingDetector(rule).scan(att)}


def test_streaming_alerts_once_and_escalates():
    det = StreamingCardTestingDetector(CardTestingRule(min_cards=3, high_decline_rate=0.5))
    att = _attempts("ip", "abcdef", declined={3, 4, 5})
    alerts = [al for a in att if (al := det.observe(a))]
    # c → MEDIUM (0 отказов), d, e — ещё MEDIUM, f → 3/6 = 0.5 → эскалация до HIGH
    assert [al.risk for al in alerts] == [Risk.MEDIUM, Risk.HIGH]


def test_streaming_forget_idle():
    det = StreamingCardTestingDetector()
    for a in _attempts("old", "ab") + _attempts("new", "cd", start=3600):
        det.observe(a)
    assert det.forget_idle(T0 + timedelta(hours=1, minutes=1), timedelta(minutes=30)) == 1
    assert det.tracked_sources == 1
