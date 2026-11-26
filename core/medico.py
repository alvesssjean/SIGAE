"""Entidade Medico e constantes de situação (ADR-005, ADR-006)."""

from __future__ import annotations

from core.erros import ErroValidacao

DISPONIVEL = "Disponível"
EM_ATENDIMENTO = "Em atendimento"

SITUACOES_MEDICO = (DISPONIVEL, EM_ATENDIMENTO)


class Medico:
    """Representa um médico clínico elegível para atendimento."""

    def __init__(
        self,
        medico_id: int,
        nome: str,
        registro: str,
        situacao: str = DISPONIVEL,
        concluidos: int = 0,
        seq_ultima_atribuicao: int = 0,
    ) -> None:
        if not isinstance(nome, str) or not nome.strip():
            raise ErroValidacao("nome do médico é obrigatório")
        if not isinstance(registro, str) or not registro.strip():
            raise ErroValidacao("registro profissional do médico é obrigatório")
        if situacao not in SITUACOES_MEDICO:
            raise ErroValidacao(f"situação inválida para médico: {situacao}")
        if isinstance(concluidos, bool) or not isinstance(concluidos, int) or concluidos < 0:
            raise ErroValidacao("contagem de concluídos inválida")
        if (
            isinstance(seq_ultima_atribuicao, bool)
            or not isinstance(seq_ultima_atribuicao, int)
            or seq_ultima_atribuicao < 0
        ):
            raise ErroValidacao("sequência de atribuição inválida")

        self.id: int = medico_id
        self.nome: str = nome.strip()
        self.registro: str = registro.strip()
        self.situacao: str = situacao
        self.concluidos: int = concluidos
        self.seq_ultima_atribuicao: int = seq_ultima_atribuicao

    def chave_heap(self) -> tuple[int, int, int]:
        return (self.concluidos, self.seq_ultima_atribuicao, self.id)
