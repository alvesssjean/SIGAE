"""Entidade Atendimento e constantes de status."""

from __future__ import annotations

from typing import Optional

from core.erros import ErroValidacao

EM_ANDAMENTO = "Em andamento"
CONCLUIDO = "Concluído"
CANCELADO = "Cancelado"

STATUS_ATENDIMENTO = (EM_ANDAMENTO, CONCLUIDO, CANCELADO)


class Atendimento:
    """Representa o vínculo entre paciente e médico em um atendimento."""

    def __init__(
        self,
        atendimento_id: int,
        paciente_id: int,
        medico_id: int,
        inicio: str,
        fim: Optional[str] = None,
        status: str = EM_ANDAMENTO,
    ) -> None:
        if not isinstance(inicio, str) or not inicio.strip():
            raise ErroValidacao("horário de início do atendimento é obrigatório")
        if status not in STATUS_ATENDIMENTO:
            raise ErroValidacao(f"status inválido para atendimento: {status}")

        self.id: int = atendimento_id
        self.paciente_id: int = paciente_id
        self.medico_id: int = medico_id
        self.inicio: str = inicio.strip()
        self.fim: Optional[str] = fim
        self.status: str = status
