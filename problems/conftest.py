"""Во всех задачах файлы называются одинаково (solution.py, alternatives.py),
и без сброса Python отдаст закэшированный модуль от предыдущей задачи."""
import sys

import pytest

_SHARED_NAMES = ("solution", "alternatives")


@pytest.hookimpl(tryfirst=True)
def pytest_collectstart(collector):
    if isinstance(collector, pytest.Module):
        for name in _SHARED_NAMES:
            sys.modules.pop(name, None)
