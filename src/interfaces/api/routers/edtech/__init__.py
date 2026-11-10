"""Отрасль edtech: один файл = один модуль из biz.edtech."""
from fastapi import APIRouter

from . import railfence

router = APIRouter(prefix="/edtech")
router.include_router(railfence.router)
