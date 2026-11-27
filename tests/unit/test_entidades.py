"""T10 / H01 / H08: testes unitários das entidades e relógio."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest

from core.atendimento import (
    CANCELADO as ATENDIMENTO_CANCELADO,
    CONCLUIDO as ATENDIMENTO_CONCLUIDO,
    EM_ANDAMENTO,
    Atendimento,
)
from core.erros import (
    ErroValidacao,
    EstadoInvalido,
    FilaVazia,
    NaoEncontrado,
    SemMedicoDisponivel,
)
from core.medico import DISPONIVEL, EM_ATENDIMENTO as MEDICO_EM_ATENDIMENTO, Medico
from core.paciente import (
    AGUARDANDO,
    CANCELADO,
    CONCLUIDO,
    EM_ATENDIMENTO,
    Paciente,
)
from core.relogio import RelogioFalso, agora_local


@pytest.mark.parametrize("nome", ["", "   "])
def test_paciente_rejeita_nome_vazio(nome):
    with pytest.raises(ErroValidacao):
        Paciente(1, nome, "2026-11-27 08:00:00", 3)


@pytest.mark.parametrize("prioridade", [0, 6, -1, True, "3"])
def test_paciente_rejeita_prioridade_invalida(prioridade):
    with pytest.raises(ErroValidacao):
        Paciente(1, "Ficticio", "2026-11-27 08:00:00", prioridade)


def test_paciente_situacoes_e_chaves():
    p = Paciente(7, "Ficticio", "2026-11-27 08:10:00", 4)
    assert p.situacao == AGUARDANDO
    assert p.retorno is False
    assert len(p.medicos_que_cancelaram) == 0
    assert p.chave_rb() == ("2026-11-27 08:10:00", 7)
    # Classe 2 para não-emergência e não-retorno
    assert p.chave_heap() == (2, 4, "2026-11-27 08:10:00", 7)

    # Devolvido com prioridade 4 -> classe 1
    p.retorno = True
    assert p.chave_heap() == (1, 4, "2026-11-27 08:10:00", 7)

    # Emergência (prioridade 1) -> classe 0, devolvida ou não
    e = Paciente(8, "Emerg", "2026-11-27 08:15:00", 1)
    assert e.chave_heap() == (0, 1, "2026-11-27 08:15:00", 8)
    e.retorno = True
    assert e.chave_heap() == (0, 1, "2026-11-27 08:15:00", 8)
    assert e.chave_heap() < p.chave_heap()

    for sit in (AGUARDANDO, EM_ATENDIMENTO, CONCLUIDO, CANCELADO):
        assert Paciente(1, "Ok", "2026-11-27 08:00:00", 3, situacao=sit).situacao == sit


def test_medico_campos_e_chave():
    m = Medico(2, "Dra. Ficticia", "CRM-FIC-2")
    assert m.situacao == DISPONIVEL
    assert m.concluidos == 0
    assert m.seq_ultima_atribuicao == 0
    assert m.chave_heap() == (0, 0, 2)

    m.concluidos = 3
    m.seq_ultima_atribuicao = 5
    m.situacao = MEDICO_EM_ATENDIMENTO
    assert m.chave_heap() == (3, 5, 2)

    with pytest.raises(ErroValidacao):
        Medico(1, "", "CRM-1")
    with pytest.raises(ErroValidacao):
        Medico(1, "Dra.", "")


def test_atendimento_status():
    a = Atendimento(1, 10, 20, "2026-11-27 08:00:00")
    assert a.fim is None
    assert a.status == EM_ANDAMENTO
    for status in (EM_ANDAMENTO, ATENDIMENTO_CONCLUIDO, ATENDIMENTO_CANCELADO):
        assert Atendimento(1, 10, 20, "2026-11-27 08:00:00", status=status).status == status
    with pytest.raises(ErroValidacao):
        Atendimento(1, 10, 20, "2026-11-27 08:00:00", status="Invalido")


def test_excecoes_existem():
    for exc in (ErroValidacao, NaoEncontrado, EstadoInvalido, FilaVazia, SemMedicoDisponivel):
        assert issubclass(exc, Exception)


def test_relogio_local_e_falso():
    valor = agora_local()
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", valor)

    lido = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S")
    try:
        fuso = ZoneInfo("America/Sao_Paulo")
    except ZoneInfoNotFoundError:
        fuso = None
    esperado = datetime.now(fuso).replace(tzinfo=None)
    assert abs((esperado - lido).total_seconds()) < 5

    falso = RelogioFalso("2026-11-27 08:00:00")
    assert falso() == "2026-11-27 08:00:00"
    assert falso() == "2026-11-27 08:00:01"

    fixo = RelogioFalso("2026-11-27 09:00:00", passo_segundos=0)
    assert fixo() == "2026-11-27 09:00:00"
    assert fixo() == "2026-11-27 09:00:00"
    fixo.avancar(10)
    assert fixo() == "2026-11-27 09:00:10"
