"""Детектор card testing: много РАЗНЫХ карт подряд с одного источника.

Алгоритм: algos.longest_unique_window (LeetCode 3) по последовательности отпечатков карт источника.
Два режима:
  CardTestingDetector          — пакетный (за день/час): один вызов longest_unique_window_batch на все источники;
  StreamingCardTestingDetector — онлайн: каждая новая попытка проверяется за O(1) амортизированно.
"""
from collections import defaultdict, deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from algos import longest_unique_window, sliding_window

from .models import Alert, PaymentAttempt, Risk, Status


@dataclass(frozen=True)
class CardTestingRule:
    min_cards: int = 5
    """От скольких разных карт подряд в одном окне поднимаем тревогу."""
    max_repeats: int = 1
    """Сколько раз одна карта может встретиться в окне. 1 — строго разные карты подряд.
    2 и больше — ловит обход «повторяю каждую карту дважды, чтобы сбить детектор»."""
    high_decline_rate: float = 0.5
    """Доля отказов в окне, начиная с которой риск HIGH (банки отклоняют мёртвые и чужие карты)."""

    def __post_init__(self):
        if self.min_cards < 2:
            raise ValueError("min_cards должен быть >= 2")
        if self.max_repeats < 1:
            raise ValueError("max_repeats должен быть >= 1")
        if not 0 <= self.high_decline_rate <= 1:
            raise ValueError("high_decline_rate должен быть в [0, 1]")


class CardTestingDetector:
    def __init__(self, rule: CardTestingRule = CardTestingRule(), backend: str | None = None):
        self.rule = rule
        self.backend = backend

    def check_source(self, attempts: Sequence[PaymentAttempt]) -> Alert | None:
        """Попытки ОДНОГО источника в хронологическом порядке → тревога или None.

        Берём самое длинное окно, где каждая карта встречается не больше max_repeats раз.
        Если в нём разных карт >= min_cards — это тревога.
        """
        cards = [a.card_fp for a in attempts]
        start, end = longest_unique_window(cards, max_repeats=self.rule.max_repeats, backend=self.backend)
        return self._alert(attempts, start, end)

    def scan(self, attempts: Iterable[PaymentAttempt]) -> list[Alert]:
        """Поток попыток (любой порядок, любые источники) → тревоги, самые опасные первыми."""
        by_source: dict[str, list[PaymentAttempt]] = defaultdict(list)
        for a in attempts:
            by_source[a.source].append(a)

        groups = list(by_source.values())
        for g in groups:
            g.sort(key=lambda a: (a.ts, a.id))  # порядок важен: окно — это подряд идущие попытки

        if hasattr(sliding_window, "longest_unique_window_batch"):
            # Один вызов на все источники (CSR): numba раздаёт источники по ядрам.
            # Отпечатки → плотные номера словарём (dictionary encoding): иначе algos отсортирует
            # миллион строк, и это съест весь выигрыш (замерено: 2.6 s против 2.0 s у python).
            ids: dict[str, int] = {}
            flat = [ids.setdefault(a.card_fp, len(ids)) for g in groups for a in g]
            offsets = [0]
            for g in groups:
                offsets.append(offsets[-1] + len(g))
            starts, ends = sliding_window.longest_unique_window_batch(
                flat, offsets, max_repeats=self.rule.max_repeats, backend=self.backend)
            found = (self._alert(g, int(s), int(e)) for g, s, e in zip(groups, starts, ends))
        else:  # нет numpy: по одному источнику
            found = (self.check_source(g) for g in groups)

        alerts = [al for al in found if al]
        return sorted(alerts, key=lambda al: (al.risk is not Risk.HIGH, -al.distinct_cards, al.source))

    def _alert(self, attempts: Sequence[PaymentAttempt], start: int, end: int) -> Alert | None:
        if end - start < self.rule.min_cards:  # разных карт не больше длины окна: дешёвый отсев
            return None
        window = tuple(attempts[start:end])
        if len({a.card_fp for a in window}) < self.rule.min_cards:
            return None
        declines = sum(a.status is Status.DECLINED for a in window)
        return Alert(attempts[0].source, _risk(declines, len(window), self.rule), window)


def _risk(declines: int, attempts: int, rule: CardTestingRule) -> Risk:
    return Risk.HIGH if declines / attempts >= rule.high_decline_rate else Risk.MEDIUM


@dataclass
class _SourceState:
    window: deque = field(default_factory=deque)  # попытки текущего окна
    count: dict = field(default_factory=dict)     # карта → сколько раз в окне
    declines: int = 0
    alerted: Risk | None = None                   # уже сообщали в этом эпизоде (и с каким риском)
    last_ts: datetime | None = None


class StreamingCardTestingDetector:
    """Онлайн-детектор: observe(attempt) на каждую попытку, тревога — в момент, когда окно становится подозрительным.

    Для каждого источника держится окно «каждая карта не больше max_repeats раз», заканчивающееся
    на последней попытке, — то же скользящее окно из LeetCode 3, только без пересчёта истории:
    каждая попытка один раз входит в окно и один раз выходит → O(1) амортизированно.

    Тревога — один раз за эпизод (пока окно подозрительное) и повторно, если риск вырос до HIGH.
    Попытки одного источника должны приходить в порядке времени (как из очереди с ключом = источник).
    """

    def __init__(self, rule: CardTestingRule = CardTestingRule()):
        self.rule = rule
        self._state: dict[str, _SourceState] = {}

    def observe(self, a: PaymentAttempt) -> Alert | None:
        st = self._state.get(a.source)
        if st is None:
            st = self._state[a.source] = _SourceState()
        st.last_ts = a.ts
        st.window.append(a)
        st.count[a.card_fp] = st.count.get(a.card_fp, 0) + 1
        st.declines += a.status is Status.DECLINED
        while st.count[a.card_fp] > self.rule.max_repeats:  # левый край ползёт, как в задаче 3
            out = st.window.popleft()
            st.count[out.card_fp] -= 1
            if not st.count[out.card_fp]:
                del st.count[out.card_fp]
            st.declines -= out.status is Status.DECLINED

        if len(st.count) < self.rule.min_cards:  # len(count) = разных карт в окне
            st.alerted = None  # эпизод закончился
            return None
        risk = _risk(st.declines, len(st.window), self.rule)
        if st.alerted is Risk.HIGH or st.alerted is risk:
            return None
        st.alerted = risk
        return Alert(a.source, risk, tuple(st.window))

    def forget_idle(self, now: datetime, max_idle: timedelta) -> int:
        """Выбросить состояние источников, молчащих дольше max_idle (иначе память растёт вечно). → сколько удалено."""
        idle = [s for s, st in self._state.items() if st.last_ts is not None and now - st.last_ts > max_idle]
        for s in idle:
            del self._state[s]
        return len(idle)

    @property
    def tracked_sources(self) -> int:
        return len(self._state)
