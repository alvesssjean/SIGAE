"""T20 / H08-H14: testes de integração de médicos, chamadas e conclusão."""

import pytest

from core.atendimento import CONCLUIDO as ATEND_CONCLUIDO, EM_ANDAMENTO
from core.erros import (
    ErroValidacao,
    EstadoInvalido,
    FilaVazia,
    NaoEncontrado,
    SemMedicoDisponivel,
)
from core.medico import DISPONIVEL, EM_ATENDIMENTO as MED_EM_ATENDIMENTO
from core.paciente import CONCLUIDO as PAC_CONCLUIDO, EM_ATENDIMENTO as PAC_EM_ATENDIMENTO
from tests.apoio import (
    assert_consistente,
    cadastrar_medicos,
    cadastrar_pacientes,
    ids,
    novo_sistema,
)


def test_cadastrar_consultar_listar_medico():
    s = novo_sistema()
    m1 = s.cadastrar_medico("Dra. Ficticia A", "CRM-FIC-A")
    m2 = s.cadastrar_medico("Dr. Ficticio B", "CRM-FIC-B")
    assert m1.id == 1
    assert m2.id == 2
    assert m1.situacao == DISPONIVEL
    assert m1.concluidos == 0
    assert s.consultar_medico(m1.id).nome == "Dra. Ficticia A"
    assert ids(s.listar_medicos()) == [m1.id, m2.id]

    with pytest.raises(ErroValidacao):
        s.cadastrar_medico("", "CRM-X")
    with pytest.raises(ErroValidacao):
        s.cadastrar_medico("Dr. X", "")
    with pytest.raises(NaoEncontrado):
        s.consultar_medico(999)
    assert_consistente(s)


def test_chamar_fila_vazia_e_sem_medico():
    s = novo_sistema()
    with pytest.raises(FilaVazia):
        s.chamar_proximo()

    (p,) = cadastrar_pacientes(s, 2)
    with pytest.raises(SemMedicoDisponivel):
        s.chamar_proximo()
    assert s.proximo_paciente().id == p.id
    assert ids(s.listar_fila_chegada()) == [p.id]
    assert_consistente(s)


def test_chamar_e_concluir_atendimento():
    s = novo_sistema()
    a, b, _ = cadastrar_medicos(s)
    (p1,) = cadastrar_pacientes(s, 3)

    atendimento = s.chamar_proximo()
    assert atendimento.paciente_id == p1.id
    assert atendimento.medico_id == a.id
    assert atendimento.status == EM_ANDAMENTO
    assert s.consultar_paciente(p1.id).situacao == PAC_EM_ATENDIMENTO
    assert s.consultar_medico(a.id).situacao == MED_EM_ATENDIMENTO
    assert s.consultar_medico(a.id).seq_ultima_atribuicao == 1
    assert ids(s.listar_atendimentos_ativos()) == [atendimento.id]
    assert_consistente(s)

    concluido = s.concluir_atendimento(atendimento.id)
    assert concluido.status == ATEND_CONCLUIDO
    assert concluido.fim is not None
    assert s.consultar_paciente(p1.id).situacao == PAC_CONCLUIDO
    assert s.consultar_medico(a.id).situacao == DISPONIVEL
    assert s.consultar_medico(a.id).concluidos == 1
    assert ids(s.listar_atendimentos_ativos()) == []
    assert ids(s.historico_atendimentos()) == [atendimento.id]
    assert_consistente(s)

    with pytest.raises(EstadoInvalido):
        s.concluir_atendimento(atendimento.id)

    # Indicadores e diagnóstico
    ind = s.indicadores()
    assert ind.concluidos == 1
    assert ind.medicos_disponiveis == 3
    diag = s.diagnostico()
    assert diag.consistencia.ok
    assert diag.rb_espera_valida
    assert diag.rb_historico_valida
