"""Relógio local e relógio determinístico para testes (ADR-009)."""

from __future__ import annotations

from datetime import datetime, timedelta, tzinfo
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

FORMATO_HORARIO = "%Y-%m-%d %H:%M:%S"
FUSO_HORARIO = "America/Sao_Paulo"


def _fuso_local() -> Optional[tzinfo]:
    """Fuso do ADR-009; sem base de fusos instalada, cai no relógio da máquina."""
    try:
        return ZoneInfo(FUSO_HORARIO)
    except ZoneInfoNotFoundError:
        return None


def agora_local() -> str:
    """Devolve o horário atual de America/Sao_Paulo em ISO AAAA-MM-DD HH:MM:SS."""
    return datetime.now(_fuso_local()).strftime(FORMATO_HORARIO)


class RelogioFalso:
    """Relógio determinístico injetável para testes unitários, integração e aceitação."""

    def __init__(
        self,
        inicio: str = "2026-11-27 08:00:00",
        passo_segundos: int = 1,
    ) -> None:
        self._atual: datetime = datetime.strptime(inicio, FORMATO_HORARIO)
        self._passo_segundos: int = passo_segundos

    def __call__(self) -> str:
        texto = self._atual.strftime(FORMATO_HORARIO)
        if self._passo_segundos:
            self._atual = self._atual + timedelta(seconds=self._passo_segundos)
        return texto

    def avancar(self, segundos: int = 1) -> None:
        self._atual = self._atual + timedelta(seconds=segundos)

    def definir(self, horario: str) -> None:
        self._atual = datetime.strptime(horario, FORMATO_HORARIO)
