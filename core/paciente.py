"""Entidade Paciente e constantes de situação (ADR-007, ADR-012)."""

from __future__ import annotations

from core.erros import ErroValidacao
from core.lista_encadeada import ListaEncadeada

AGUARDANDO = "Aguardando"
EM_ATENDIMENTO = "Em atendimento"
CONCLUIDO = "Concluído"
CANCELADO = "Cancelado"

SITUACOES_PACIENTE = (AGUARDANDO, EM_ATENDIMENTO, CONCLUIDO, CANCELADO)

PRIORIDADE_MINIMA = 1
PRIORIDADE_MAXIMA = 5
PRIORIDADE_EMERGENCIA = 1


def validar_prioridade(prioridade: int) -> int:
    if isinstance(prioridade, bool) or not isinstance(prioridade, int):
        raise ErroValidacao("prioridade deve ser um inteiro de 1 a 5")
    if prioridade < PRIORIDADE_MINIMA or prioridade > PRIORIDADE_MAXIMA:
        raise ErroValidacao("prioridade deve estar entre 1 e 5")
    return prioridade


def nome_prioridade(prioridade: int) -> str:
    if prioridade == 1:
        return "Emergência"
    if prioridade == 2:
        return "Muito urgente"
    if prioridade == 3:
        return "Urgente"
    if prioridade == 4:
        return "Pouco urgente"
    if prioridade == 5:
        return "Não urgente"
    return f"Prioridade {prioridade}"


class Paciente:
    """Representa um paciente no fluxo de pronto atendimento."""

    def __init__(
        self,
        paciente_id: int,
        nome: str,
        horario: str,
        prioridade: int,
        situacao: str = AGUARDANDO,
        retorno: bool = False,
    ) -> None:
        if not isinstance(nome, str) or not nome.strip():
            raise ErroValidacao("nome do paciente é obrigatório")
        if not isinstance(horario, str) or not horario.strip():
            raise ErroValidacao("horário de chegada é obrigatório")
        validar_prioridade(prioridade)
        if situacao not in SITUACOES_PACIENTE:
            raise ErroValidacao(f"situação inválida para paciente: {situacao}")

        self.id: int = paciente_id
        self.nome: str = nome.strip()
        self.horario: str = horario.strip()
        self.prioridade: int = prioridade
        self.situacao: str = situacao
        self.retorno: bool = bool(retorno)
        self.medicos_que_cancelaram: ListaEncadeada = ListaEncadeada()

    def chave_rb(self) -> tuple[str, int]:
        return (self.horario, self.id)

    def chave_heap(self) -> tuple[int, int, str, int]:
        if self.prioridade == PRIORIDADE_EMERGENCIA:
            classe = 0
        elif self.retorno:
            classe = 1
        else:
            classe = 2
        return (classe, self.prioridade, self.horario, self.id)

    @property
    def descricao_prioridade(self) -> str:
        return nome_prioridade(self.prioridade)
