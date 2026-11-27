"""T50 / H15 / H06: testes de integração do cancelamento de atendimento (uma vez por médico)."""

import pytest

from core.atendimento import CANCELADO as ATEND_CANCELADO
from core.erros import EstadoInvalido
from core.medico import DISPONIVEL
from core.paciente import AGUARDANDO
from tests.apoio import (
    assert_consistente,
    cadastrar_medicos,
    cadastrar_pacientes,
    ids,
    novo_sistema,
)


def test_cancelar_devolve_atras_das_emergencias_e_mantem_chegada():
    s = novo_sistema()
    a, _, _ = cadastrar_medicos(s)
    p_devolvido, p_muito_urgente = cadastrar_pacientes(s, 4, 2)
    # p_muito_urgente tem prioridade 2 -> chamado primeiro; vamos cadastrar p_devolvido como 2 e depois outro 2
    s2 = novo_sistema()
    ma, _, _ = cadastrar_medicos(s2)
    (devolvido,) = cadastrar_pacientes(s2, 4)
    atend = s2.chamar_proximo()
    muito_urgente = s2.cadastrar_paciente("Ficticio Muito Urgente", 2)
    urgente = s2.cadastrar_paciente("Ficticio Urgente", 3)

    cancelado = s2.cancelar_atendimento(atend.id)
    assert cancelado.status == ATEND_CANCELADO
    assert cancelado.fim is not None
    assert s2.consultar_paciente(devolvido.id).situacao == AGUARDANDO
    assert s2.consultar_paciente(devolvido.id).retorno is True
    assert s2.consultar_medico(ma.id).situacao == DISPONIVEL
    assert s2.consultar_medico(ma.id).concluidos == 0
    assert s2.consultar_medico(ma.id).seq_ultima_atribuicao == 1

    # Sem Emergência: devolvido fica em 1º
    assert ids(s2.listar_fila_prioridade()) == [
        devolvido.id,
        muito_urgente.id,
        urgente.id,
    ]
    # Na RB espera, mantém posição de chegada original (devolvido chegou primeiro)
    assert ids(s2.listar_fila_chegada()) == [
        devolvido.id,
        muito_urgente.id,
        urgente.id,
    ]

    # Com uma Emergência: devolvido fica em 2º
    emergencia = s2.cadastrar_paciente("Ficticio Emergencia", 1)
    assert ids(s2.listar_fila_prioridade()) == [
        emergencia.id,
        devolvido.id,
        muito_urgente.id,
        urgente.id,
    ]
    assert_consistente(s2)


def test_mesmo_medico_pode_receber_novamente_mas_nao_cancelar_duas_vezes():
    s = novo_sistema()
    m1 = s.cadastrar_medico("Ana Ficticia", "")
    (p1,) = cadastrar_pacientes(s, 3)

    a1 = s.chamar_proximo()
    assert a1.medico_id == m1.id
    s.cancelar_atendimento(a1.id)

    a2 = s.chamar_proximo()
    assert a2.medico_id == m1.id
    assert a2.paciente_id == p1.id
    assert s.consultar_paciente(p1.id).retorno is False

    with pytest.raises(EstadoInvalido):
        s.cancelar_atendimento(a2.id)
    assert ids(s.listar_atendimentos_ativos()) == [a2.id]
    assert_consistente(s)


def test_outro_medico_pode_cancelar_uma_vez():
    s = novo_sistema()
    m1, m2, _ = cadastrar_medicos(s)
    (p1,) = cadastrar_pacientes(s, 3)

    a1 = s.chamar_proximo()
    assert a1.medico_id == m1.id
    s.cancelar_atendimento(a1.id)

    a2 = s.chamar_proximo()
    assert a2.medico_id == m2.id
    s.cancelar_atendimento(a2.id)

    assert len(s.consultar_paciente(p1.id).medicos_que_cancelaram) == 2
    assert_consistente(s)


def test_cancelar_atendimento_encerrado_da_erro():
    s = novo_sistema()
    cadastrar_medicos(s)
    cadastrar_pacientes(s, 3)
    a1 = s.chamar_proximo()
    s.concluir_atendimento(a1.id)

    with pytest.raises(EstadoInvalido):
        s.cancelar_atendimento(a1.id)
    assert_consistente(s)


def test_cancelar_paciente_em_atendimento_delega_para_cancelar_atendimento():
    s = novo_sistema()
    cadastrar_medicos(s)
    (p1,) = cadastrar_pacientes(s, 3)
    s.chamar_proximo()

    s.cancelar_paciente(p1.id)
    assert s.consultar_paciente(p1.id).situacao == AGUARDANDO
    assert s.consultar_paciente(p1.id).retorno is True
    assert ids(s.listar_atendimentos_ativos()) == []
    assert_consistente(s)
