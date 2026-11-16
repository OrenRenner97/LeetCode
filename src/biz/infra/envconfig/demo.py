"""Демо: python -m biz.infra.envconfig.demo"""
from .audit import Setting, audit_env

ENV = {
    "WORKERS": "auto",
    "TIMEOUT_SEC": "30s",
    "MAX_BODY_BYTES": "4294967296",
    "PORT": " 8080\n",
    "BATCH": "1_000",
    "RETRIES": "-1",
    "POOL": "16",
}
SETTINGS = [
    Setting("WORKERS", min=1, max=256),
    Setting("TIMEOUT_SEC", min=1),
    Setting("MAX_BODY_BYTES"),
    Setting("PORT", bits=16, signed=False, min=1),
    Setting("BATCH", min=1),
    Setting("RETRIES", bits=8, signed=False),
    Setting("POOL", min=1, max=64),
    Setting("CACHE_MB"),
]


def main() -> None:
    print(f"{'переменная':<15} {'значение':<14} {'C atoi':>11} {'Python int':>11}  проблема")
    for f in audit_env(ENV, SETTINGS):
        py = "—" if f.raw is None else ("ошибка" if f.py_value is None else f.py_value)
        c = "—" if f.c_value is None else f.c_value
        mark = "≠" if f.diverges else " "
        print(f"{f.name:<15} {f.raw!r:<14} {c!s:>11} {mark}{py!s:>10}  {f.issue}: {f.message}")


if __name__ == "__main__":
    main()
