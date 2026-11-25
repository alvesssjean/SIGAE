"""Cenários B e P1: prioridade dos pacientes."""

import pytest

from tests.apoio import assert_consistente, cadastrar_medicos, cadastrar_pacientes, ids, novo_sistema

pytestmark = pytest.mark.xfail(reason="aguarda T18/T21/T50")


def test_reclassificar_atualiza_a_raiz():
    s = novo_sistema()
    p1, p2, p3 = cadastrar_pacientes(s, 3, 4, 5)
    s.reclassificar(p3.id, 1)
    assert s.proximo_paciente().id == p3.id
    s.reclassificar(p2.id, 1)
    # mesma prioridade: vence quem chegou antes
    assert s.proximo_paciente().id == p2.id
    assert ids(s.listar_fila_prioridade()) == [p2.id, p3.id, p1.id]
    assert_consistente(s)


def test_ordem_de_chamada():
    s = novo_sistema()
    cadastrar_medicos(s)
    p1, p2, p3 = cadastrar_pacientes(s, 5, 1, 3)
    chamados = [s.chamar_proximo().paciente_id for _ in range(3)]
    assert chamados == [p2.id, p3.id, p1.id]
    assert_consistente(s)
