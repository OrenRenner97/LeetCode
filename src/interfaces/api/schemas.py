"""Общие типы полей, переиспользуемые роутерами."""
from typing import Annotated

from pydantic import Field

Backend = Annotated[
    str | None,
    Field(
        description="Реализация алгоритма: `python` | `numpy` | `numba` | `c` | `cuda`. "
                    "По умолчанию `auto`: самая быстрая для этого размера входа (см. `GET /backends`).",
        examples=[None, "python", "numba"],
    ),
]
