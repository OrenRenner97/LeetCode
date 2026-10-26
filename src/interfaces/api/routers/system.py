from fastapi import APIRouter
from pydantic import BaseModel, Field

from algos import arithmetic, hashing

router = APIRouter(tags=["system"])


class Health(BaseModel):
    status: str = Field(description="`ok`, если процесс жив", examples=["ok"])


@router.get("/health", summary="Проверка живости")
def health() -> Health:
    """Liveness-проба для балансировщика или Kubernetes. Не трогает бизнес-логику."""
    return Health(status="ok")


@router.get("/backends", summary="Доступные реализации алгоритмов")
def backends() -> dict[str, list[str]]:
    """Какие backend'ы каждого алгоритма доступны **на этом сервере**, в порядке приоритета `auto`.

    Зависит от окружения: нет numba → нет `numba`, не собран `libalgos.so` → нет `c`, нет GPU → нет `cuda`.
    """
    funcs = [hashing.find_pair_with_sum, arithmetic.add_digits, arithmetic.sub_digits, arithmetic.sum_limbs]
    if hasattr(hashing, "find_pairs_batch"):
        funcs.append(hashing.find_pairs_batch)
    return {f.__name__: f.backends for f in funcs}
