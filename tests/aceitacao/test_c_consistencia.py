"""Cenários C e C2: consistência sem registros órfãos."""

import pytest

from tests.apoio import assert_consistente, cadastrar_medicos, cadastrar_pacientes, ids, novo_sistema

pytestmark = pytest.mark.xfail(reason="aguarda T18/T21/T50")


def test_atender_concluir_e_cancelar():
    s = novo_sistema()
    cadastrar_medicos(s)
    p1, p2, p3, p4 = cadastrar_pacientes(s, 1, 2, 3, 4)
    a1 = s.chamar_proximo()
    a2 = s.chamar_proximo()
    s.concluir_atendimento(a1.id)
    s.cancelar_atendimento(a2.id)
    s.cancelar_paciente(p4.id)
    assert ids(s.listar_fila_chegada()) == [p2.id, p3.id]
    assert ids(s.listar_atendimentos_ativos()) == []
    assert_consistente(s)


def test_fluxo_misto():
    from core.paciente import AGUARDANDO, CANCELADO, CONCLUIDO

    s = novo_sistema()
    cadastrar_medicos(s)
    p1, p2, p3 = cadastrar_pacientes(s, 2, 3, 4)
    s.reclassificar(p3.id, 1)
    a1 = s.chamar_proximo()
    assert a1.paciente_id == p3.id
    s.concluir_atendimento(a1.id)
    s.cancelar_paciente(p2.id)
    assert s.consultar_paciente(p1.id).situacao == AGUARDANDO
    assert s.consultar_paciente(p2.id).situacao == CANCELADO
    assert s.consultar_paciente(p3.id).situacao == CONCLUIDO
    assert ids(s.listar_historico_chegadas()) == [p1.id, p2.id, p3.id]
    assert_consistente(s)
