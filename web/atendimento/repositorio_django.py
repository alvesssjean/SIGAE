"""Implementação da porta Repositorio usando Django ORM sobre SQLite (T24 / ADR-004).

SQLite é usado apenas como persistência: nunca usa order_by, filter ou get para
regras de negócio. carregar_tudo() lê .all() sem ordenação para o core reconstruir
as estruturas em memória.
"""

from contextlib import contextmanager
from typing import Iterator

from django.db import transaction

from core.atendimento import Atendimento
from core.lista_encadeada import ListaEncadeada
from core.medico import Medico
from core.paciente import Paciente
from core.repositorio import DadosCarregados, Repositorio
from web.atendimento.models import (
    AtendimentoModel,
    Contador,
    MedicoModel,
    PacienteModel,
)


class RepositorioDjango(Repositorio):
    """Repositório persistente baseado no ORM do Django."""

    @contextmanager
    def transacao(self) -> Iterator[None]:
        with transaction.atomic():
            yield

    def salvar_paciente(self, paciente: Paciente) -> None:
        PacienteModel.objects.update_or_create(
            id=paciente.id,
            defaults={
                "nome": paciente.nome,
                "horario": paciente.horario,
                "prioridade": paciente.prioridade,
                "situacao": paciente.situacao,
                "retorno": paciente.retorno,
            },
        )

    def salvar_medico(self, medico: Medico) -> None:
        MedicoModel.objects.update_or_create(
            id=medico.id,
            defaults={
                "nome": medico.nome,
                "registro": medico.registro,
                "situacao": medico.situacao,
                "concluidos": medico.concluidos,
                "seq_ultima_atribuicao": medico.seq_ultima_atribuicao,
            },
        )

    def salvar_atendimento(self, atendimento: Atendimento) -> None:
        AtendimentoModel.objects.update_or_create(
            id=atendimento.id,
            defaults={
                "paciente_id": atendimento.paciente_id,
                "medico_id": atendimento.medico_id,
                "inicio": atendimento.inicio,
                "fim": atendimento.fim,
                "status": atendimento.status,
            },
        )

    def salvar_contadores(
        self,
        ultimo_paciente_id: int,
        ultimo_medico_id: int,
        ultimo_atendimento_id: int,
        relogio_logico: int,
    ) -> None:
        for nome, valor in (
            ("ultimo_paciente_id", ultimo_paciente_id),
            ("ultimo_medico_id", ultimo_medico_id),
            ("ultimo_atendimento_id", ultimo_atendimento_id),
            ("relogio_logico", relogio_logico),
        ):
            Contador.objects.update_or_create(nome=nome, defaults={"valor": valor})

    def carregar_tudo(self) -> DadosCarregados:
        pacientes = ListaEncadeada()
        for reg in PacienteModel.objects.all():
            pacientes.anexar(
                Paciente(
                    paciente_id=reg.id,
                    nome=reg.nome,
                    horario=reg.horario,
                    prioridade=reg.prioridade,
                    situacao=reg.situacao,
                    retorno=reg.retorno,
                )
            )

        medicos = ListaEncadeada()
        for reg in MedicoModel.objects.all():
            medicos.anexar(
                Medico(
                    medico_id=reg.id,
                    nome=reg.nome,
                    registro=reg.registro,
                    situacao=reg.situacao,
                    concluidos=reg.concluidos,
                    seq_ultima_atribuicao=reg.seq_ultima_atribuicao,
                )
            )

        atendimentos = ListaEncadeada()
        for reg in AtendimentoModel.objects.all():
            atendimentos.anexar(
                Atendimento(
                    atendimento_id=reg.id,
                    paciente_id=reg.paciente_id,
                    medico_id=reg.medico_id,
                    inicio=reg.inicio,
                    fim=reg.fim,
                    status=reg.status,
                )
            )

        ultimo_paciente_id = 0
        ultimo_medico_id = 0
        ultimo_atendimento_id = 0
        relogio_logico = 0
        for reg in Contador.objects.all():
            if reg.nome == "ultimo_paciente_id":
                ultimo_paciente_id = reg.valor
            elif reg.nome == "ultimo_medico_id":
                ultimo_medico_id = reg.valor
            elif reg.nome == "ultimo_atendimento_id":
                ultimo_atendimento_id = reg.valor
            elif reg.nome == "relogio_logico":
                relogio_logico = reg.valor

        return DadosCarregados(
            pacientes=pacientes,
            medicos=medicos,
            atendimentos=atendimentos,
            ultimo_paciente_id=ultimo_paciente_id,
            ultimo_medico_id=ultimo_medico_id,
            ultimo_atendimento_id=ultimo_atendimento_id,
            relogio_logico=relogio_logico,
        )

    def limpar_tudo(self) -> None:
        with transaction.atomic():
            AtendimentoModel.objects.all().delete()
            PacienteModel.objects.all().delete()
            MedicoModel.objects.all().delete()
            Contador.objects.all().delete()
