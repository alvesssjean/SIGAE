"""Serviço singleton que inicializa e rehidrata o Sistema uma única vez (T25)."""

import threading
from typing import Optional

from core.sistema import Sistema
from web.atendimento.repositorio_django import RepositorioDjango

_lock = threading.Lock()
_sistema: Optional[Sistema] = None


def obter_sistema() -> Sistema:
    global _sistema
    if _sistema is None:
        with _lock:
            if _sistema is None:
                _sistema = Sistema.carregar(RepositorioDjango())
    return _sistema


def resetar_sistema() -> None:
    global _sistema
    with _lock:
        _sistema = None
