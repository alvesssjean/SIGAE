"""Cenários A e A2: colisão e redimensionamento da Hash."""

import pytest

pytestmark = pytest.mark.xfail(reason="aguarda T07")


def tabela():
    from core.hash_table import HashTable

    return HashTable(capacidade=7)


def test_colisao_101_e_108():
    t = tabela()
    t.inserir(101, "a")
    t.inserir(108, "b")
    assert 101 % t.capacidade() == 108 % t.capacidade()
    assert (t.buscar(101), t.buscar(108)) == ("a", "b")
    assert t.estatisticas()
    t.validar()


def test_redimensionamento_preserva_registros():
    t = tabela()
    for chave in range(101, 121):
        t.inserir(chave, chave)
    assert t.capacidade() > 7
    assert t.fator_carga() <= 0.75
    assert all(t.buscar(chave) == chave for chave in range(101, 121))
    t.validar()
