"""Cenários M1 a M5, C3 e C4: médicos."""

import pytest

from tests.apoio import assert_consistente, cadastrar_medicos, cadastrar_pacientes, ids, novo_sistema

pytestmark = pytest.mark.xfail(reason="aguarda T18/T21/T50")


def test_distribuicao_equilibrada():
    s = novo_sistema()
    a, b, c = cadastrar_medicos(s)
    cadastrar_pacientes(s, 3, 3, 3)
    assert [s.chamar_proximo().medico_id for _ in range(3)] == [a.id, b.id, c.id]
    assert_consistente(s)


def test_menor_carga_apos_conclusao():
    s = novo_sistema()
    a, b, c = cadastrar_medicos(s)
    cadastrar_pacientes(s, 3, 3, 3, 3)
    a1, a2, a3 = (s.chamar_proximo() for _ in range(3))
    s.concluir_atendimento(a1.id)
    s.concluir_atendimento(a2.id)
    s.cancelar_atendimento(a3.id)
    # C segue com 0 concluídos; A e B têm 1
    assert s.chamar_proximo().medico_id == c.id
    assert_consistente(s)


def test_desempate_tempo_e_id():
    s = novo_sistema()
    a, b, c = cadastrar_medicos(s)
    cadastrar_pacientes(s, 3, 3, 3, 3, 3)
    a1, a2, a3 = (s.chamar_proximo() for _ in range(3))
    # conclui fora de ordem: vale o momento da chamada (ADR-006)
    for atendimento in (a3, a2, a1):
        s.concluir_atendimento(atendimento.id)
    assert s.chamar_proximo().medico_id == a.id
    assert s.chamar_proximo().medico_id == b.id
    assert_consistente(s)


def test_medico_ocupado():
    s = novo_sistema()
    a, b, _ = cadastrar_medicos(s)
    cadastrar_pacientes(s, 3, 3)
    assert s.chamar_proximo().medico_id == a.id
    assert s.chamar_proximo().medico_id == b.id
    assert_consistente(s)


def test_sem_medico_disponivel():
    from core.erros import SemMedicoDisponivel

    s = novo_sistema()
    (p,) = cadastrar_pacientes(s, 2)
    with pytest.raises(SemMedicoDisponivel):
        s.chamar_proximo()
    assert s.proximo_paciente().id == p.id
    assert ids(s.listar_fila_chegada()) == [p.id]
    assert_consistente(s)


def test_cancelamento_nao_conta():
    s = novo_sistema()
    a, _, _ = cadastrar_medicos(s)
    p1, p2 = cadastrar_pacientes(s, 3, 4)
    atendimento = s.chamar_proximo()
    s.cancelar_atendimento(atendimento.id)
    s.cancelar_paciente(p2.id)
    assert s.consultar_medico(a.id).concluidos == 0
    assert_consistente(s)


def test_medico_nao_altera_ordem_pacientes():
    s = novo_sistema()
    cadastrar_medicos(s)
    p1, p2 = cadastrar_pacientes(s, 5, 1)
    assert s.chamar_proximo().paciente_id == p2.id
    assert s.chamar_proximo().paciente_id == p1.id
    assert_consistente(s)
