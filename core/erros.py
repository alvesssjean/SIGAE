"""Exceções de domínio do núcleo SIGAE."""

from __future__ import annotations


class ErroSigae(Exception):
    """Exceção base de domínio do SIGAE."""


class ErroValidacao(ErroSigae):
    """Dados de entrada inválidos."""


class NaoEncontrado(ErroSigae):
    """Registro não encontrado pelo identificador informado."""


class EstadoInvalido(ErroSigae):
    """Operação não permitida para o estado atual do registro."""


class FilaVazia(ErroSigae):
    """Não há pacientes aguardando na fila."""


class SemMedicoDisponivel(ErroSigae):
    """Não há médicos disponíveis para chamada."""
