"""Cenários K1 a K5: cancelamento de atendimento (BACKLOG 2.3)."""

import pytest

from tests.apoio import assert_consistente, cadastrar_medicos, cadastrar_pacientes, ids, novo_sistema


def test_volta_para_a_fila():
    from core.medico import DISPONIVEL

    s = novo_sistema()
    a, _, _ = cadastrar_medicos(s)
    p1, p2 = cadastrar_pacientes(s, 2, 3)
    atendimento = s.chamar_proximo()
    s.cancelar_atendimento(atendimento.id)
    assert s.proximo_paciente().id == p1.id
    assert ids(s.listar_fila_chegada()) == [p1.id, p2.id]
    medico = s.consultar_medico(a.id)
    assert (medico.situacao, medico.concluidos) == (DISPONIVEL, 0)
    assert_consistente(s)


def test_devolvido_atras_da_emergencia():
    s = novo_sistema()
    cadastrar_medicos(s)
    (devolvido,) = cadastrar_pacientes(s, 4)
    atendimento = s.chamar_proximo()
    muito_urgente = s.cadastrar_paciente("Ficticio Muito Urgente", 2)
    s.cancelar_atendimento(atendimento.id)
    assert ids(s.listar_fila_prioridade()) == [devolvido.id, muito_urgente.id]
    emergencia = s.cadastrar_paciente("Ficticio Emergencia", 1)
    assert ids(s.listar_fila_prioridade()) == [
        emergencia.id,
        devolvido.id,
        muito_urgente.id,
    ]
    assert_consistente(s)


def atender_e_cancelar(s):
    atendimento = s.chamar_proximo()
    s.cancelar_atendimento(atendimento.id)
    return atendimento


def um_medico_um_paciente():
    s = novo_sistema()
    medico = s.cadastrar_medico("Ana Ficticia", "")
    cadastrar_pacientes(s, 3)
    return s, medico


def test_mesmo_medico_pode_atender():
    s, medico = um_medico_um_paciente()
    atender_e_cancelar(s)
    assert s.chamar_proximo().medico_id == medico.id
    assert_consistente(s)


def test_mesmo_medico_nao_cancela_duas_vezes():
    from core.erros import EstadoInvalido

    s, _ = um_medico_um_paciente()
    atender_e_cancelar(s)
    segundo = s.chamar_proximo()
    with pytest.raises(EstadoInvalido):
        s.cancelar_atendimento(segundo.id)
    assert ids(s.listar_atendimentos_ativos()) == [segundo.id]
    assert_consistente(s)


def test_outro_medico_pode_cancelar():
    s = novo_sistema()
    a, b, _ = cadastrar_medicos(s)
    cadastrar_pacientes(s, 3)
    assert atender_e_cancelar(s).medico_id == a.id
    # B e C nunca foram atribuídos (seq 0), então B vem antes de A
    segundo = atender_e_cancelar(s)
    assert segundo.medico_id == b.id
    assert_consistente(s)
