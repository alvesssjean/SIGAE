"""T17 (par com I3): operações de pacientes. H01, H02, H03, H05, H06."""

import pytest

from tests.apoio import assert_consistente, cadastrar_pacientes, ids, novo_sistema

pytestmark = pytest.mark.xfail(reason="aguarda T18")


def test_cadastrar_gera_id_e_horario_e_indexa():
    from core.paciente import AGUARDANDO

    s = novo_sistema()
    p = s.cadastrar_paciente("Ficticio", 3)
    assert p.situacao == AGUARDANDO
    assert p.horario.startswith("2026-11-27")
    assert s.consultar_paciente(p.id).id == p.id
    assert s.proximo_paciente().id == p.id
    assert ids(s.listar_fila_chegada()) == [p.id]
    assert ids(s.listar_historico_chegadas()) == [p.id]
    assert_consistente(s)


@pytest.mark.parametrize("nome, prioridade", [("", 3), ("X", 0), ("X", 6)])
def test_invalido_nao_altera_nada_nem_o_contador(nome, prioridade):
    from core.erros import ErroValidacao

    s = novo_sistema()
    p1 = s.cadastrar_paciente("Antes", 3)
    with pytest.raises(ErroValidacao):
        s.cadastrar_paciente(nome, prioridade)
    p2 = s.cadastrar_paciente("Depois", 3)
    assert p2.id == p1.id + 1
    assert ids(s.listar_pacientes()) == [p1.id, p2.id]
    assert_consistente(s)


def test_consultar_inexistente():
    from core.erros import NaoEncontrado

    with pytest.raises(NaoEncontrado):
        novo_sistema().consultar_paciente(999)


def test_reclassificar_sem_duplicar():
    s = novo_sistema()
    p1, p2 = cadastrar_pacientes(s, 3, 4)
    s.reclassificar(p2.id, 2)
    assert ids(s.listar_fila_prioridade()) == [p2.id, p1.id]
    assert ids(s.listar_fila_chegada()) == [p1.id, p2.id]
    assert_consistente(s)


def test_listar_prioridade_nao_altera_o_heap():
    s = novo_sistema()
    cadastrar_pacientes(s, 5, 1, 3)
    assert ids(s.listar_fila_prioridade()) == ids(s.listar_fila_prioridade())
    assert_consistente(s)


def test_cancelar_aguardando():
    from core.erros import EstadoInvalido
    from core.paciente import CANCELADO

    s = novo_sistema()
    p1, p2 = cadastrar_pacientes(s, 1, 3)
    s.cancelar_paciente(p1.id)
    assert s.consultar_paciente(p1.id).situacao == CANCELADO
    assert ids(s.listar_fila_chegada()) == [p2.id]
    assert s.proximo_paciente().id == p2.id
    assert ids(s.listar_historico_chegadas()) == [p1.id, p2.id]
    with pytest.raises(EstadoInvalido):
        s.cancelar_paciente(p1.id)
    assert_consistente(s)
