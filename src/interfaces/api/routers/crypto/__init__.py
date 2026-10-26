"""Отрасль crypto: один файл = один модуль из biz.crypto."""
from fastapi import APIRouter

from . import ledger

router = APIRouter(prefix="/crypto")
router.include_router(ledger.router)
