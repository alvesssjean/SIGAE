"""Porta de persistência Repositorio e implementação em memória (ADR-004)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from core.atendimento import Atendimento
from core.lista_encadeada import ListaEncadeada
from core.medico import Medico
from core.paciente import Paciente


class DadosCarregados:
    """Pacote imutável com os registros carregados para rehidratação do núcleo."""

    __slots__ = (
        "pacientes",
        "medicos",
        "atendimentos",
        "ultimo_paciente_id",
        "ultimo_medico_id",
        "ultimo_atendimento_id",
        "relogio_logico",
    )

    def __init__(
        self,
        pacientes: ListaEncadeada,
        medicos: ListaEncadeada,
        atendimentos: ListaEncadeada,
        ultimo_paciente_id: int,
        ultimo_medico_id: int,
        ultimo_atendimento_id: int,
        relogio_logico: int,
    ) -> None:
        self.pacientes = pacientes
        self.medicos = medicos
        self.atendimentos = atendimentos
        self.ultimo_paciente_id = ultimo_paciente_id
        self.ultimo_medico_id = ultimo_medico_id
        self.ultimo_atendimento_id = ultimo_atendimento_id
        self.relogio_logico = relogio_logico


class Repositorio:
    """Porta de persistência injetada no núcleo Sistema."""

    @contextmanager
    def transacao(self) -> Iterator[None]:
        yield

    def salvar_paciente(self, paciente: Paciente) -> None:
        raise NotImplementedError

    def salvar_medico(self, medico: Medico) -> None:
        raise NotImplementedError

    def salvar_atendimento(self, atendimento: Atendimento) -> None:
        raise NotImplementedError

    def salvar_contadores(
        self,
        ultimo_paciente_id: int,
        ultimo_medico_id: int,
        ultimo_atendimento_id: int,
        relogio_logico: int,
    ) -> None:
        raise NotImplementedError

    def carregar_tudo(self) -> DadosCarregados:
        raise NotImplementedError


class RepositorioMemoria(Repositorio):
    """Repositório sem persistência em disco (usado em testes e como fallback)."""

    @contextmanager
    def transacao(self) -> Iterator[None]:
        yield

    def salvar_paciente(self, paciente: Paciente) -> None:
        return None

    def salvar_medico(self, medico: Medico) -> None:
        return None

    def salvar_atendimento(self, atendimento: Atendimento) -> None:
        return None

    def salvar_contadores(
        self,
        ultimo_paciente_id: int,
        ultimo_medico_id: int,
        ultimo_atendimento_id: int,
        relogio_logico: int,
    ) -> None:
        return None

    def carregar_tudo(self) -> DadosCarregados:
        return DadosCarregados(
            pacientes=ListaEncadeada(),
            medicos=ListaEncadeada(),
            atendimentos=ListaEncadeada(),
            ultimo_paciente_id=0,
            ultimo_medico_id=0,
            ultimo_atendimento_id=0,
            relogio_logico=0,
        )
