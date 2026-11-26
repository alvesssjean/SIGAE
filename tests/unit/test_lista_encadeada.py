import pytest

from core.lista_encadeada import ListaEncadeada


def test_lista_vazia():
    lista = ListaEncadeada()
    assert len(lista) == 0
    assert not lista
    assert list(lista) == []
    assert lista.cabeca is None and lista.cauda is None


def test_anexar_mantem_ordem_de_insercao():
    lista = ListaEncadeada()
    for n in (1, 2, 3):
        lista.anexar(n)
    assert list(lista) == [1, 2, 3]
    assert len(lista) == 3
    assert lista
    assert lista.cabeca.valor == 1
    assert lista.cauda.valor == 3


def test_inserir_inicio_coloca_na_frente():
    lista = ListaEncadeada()
    lista.inserir_inicio(1)
    lista.inserir_inicio(2)
    lista.anexar(3)
    assert list(lista) == [2, 1, 3]
    assert lista.cauda.valor == 3


def test_inserir_inicio_em_lista_vazia_define_cauda():
    lista = ListaEncadeada()
    lista.inserir_inicio("a")
    assert lista.cabeca is lista.cauda
    lista.anexar("b")
    assert list(lista) == ["a", "b"]


def test_uso_como_pilha():
    pilha = ListaEncadeada()
    for n in (1, 2, 3):
        pilha.inserir_inicio(n)
    assert pilha.remover_inicio() == 3
    assert pilha.remover_inicio() == 2
    assert pilha.remover_inicio() == 1
    assert len(pilha) == 0
    assert not pilha


def test_remover_inicio_vazio_levanta():
    with pytest.raises(IndexError):
        ListaEncadeada().remover_inicio()


def test_remover_ultimo_zera_cabeca_e_cauda():
    lista = ListaEncadeada()
    lista.anexar(1)
    lista.remover_inicio()
    assert lista.cabeca is None and lista.cauda is None
    lista.anexar(2)
    assert list(lista) == [2]


def test_anexar_depois_de_remover_continua_correto():
    lista = ListaEncadeada()
    for n in (1, 2, 3):
        lista.anexar(n)
    lista.remover_inicio()
    lista.anexar(4)
    assert list(lista) == [2, 3, 4]
    assert len(lista) == 3


def test_contem():
    lista = ListaEncadeada()
    for n in (10, 20, 30):
        lista.anexar(n)
    assert lista.contem(20)
    assert not lista.contem(99)
    assert 20 in lista


def test_iteracao_pode_ser_repetida():
    lista = ListaEncadeada()
    for n in (1, 2):
        lista.anexar(n)
    assert list(lista) == list(lista) == [1, 2]
