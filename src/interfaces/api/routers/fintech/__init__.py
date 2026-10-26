"""Отрасль fintech: один файл = один модуль из biz.fintech."""
from fastapi import APIRouter

from . import antifraud, reconciliation

router = APIRouter(prefix="/fintech")
router.include_router(reconciliation.router)
router.include_router(antifraud.router)
