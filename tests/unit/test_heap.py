"""T08 / H03 / H04: testes unitários do MinHeap sem vetor."""

import random

import pytest

from core.heap import MinHeap


class ItemTeste:
    def __init__(self, item_id: int, prioridade: int, horario: str):
        self.id = item_id
        self.prioridade = prioridade
        self.horario = horario

    def chave(self):
        return (self.prioridade, self.horario, self.id)


def novo_heap():
    return MinHeap(chave=lambda x: x.chave(), id_de=lambda x: x.id)


def test_heap_vazio():
    h = novo_heap()
    assert h.tamanho() == 0
    assert len(h) == 0
    assert h.raiz() is None
    assert h.extrair_minimo() is None
    assert list(h.itens()) == []
    h.validar()


def test_extracao_crescente_e_desempates():
    h = novo_heap()
    itens = [
        ItemTeste(4, 3, "08:10"),
        ItemTeste(2, 1, "08:05"),
        ItemTeste(5, 1, "08:00"),
        ItemTeste(3, 2, "08:00"),
        ItemTeste(1, 2, "08:00"),
    ]
    for item in itens:
        h.inserir(item)
        h.validar()

    extraidos = []
    while h.tamanho() > 0:
        extraidos.append(h.extrair_minimo().id)
        h.validar()

    # (1, 08:00, 5), (1, 08:05, 2), (2, 08:00, 1), (2, 08:00, 3), (3, 08:10, 4)
    assert extraidos == [5, 2, 1, 3, 4]


def test_alterar_prioridade_subindo_e_descendo():
    h = novo_heap()
    a = ItemTeste(1, 3, "08:00")
    b = ItemTeste(2, 4, "08:01")
    c = ItemTeste(3, 5, "08:02")
    d = ItemTeste(4, 2, "08:03")
    for item in (a, b, c, d):
        h.inserir(item)

    assert h.raiz().id == 4

    # Subir c (id 3) para prioridade 1
    c.prioridade = 1
    h.alterar_prioridade(3)
    h.validar()
    assert h.raiz().id == 3

    # Descer c (id 3) para prioridade 5 novamente
    c.prioridade = 5
    h.alterar_prioridade(3)
    h.validar()
    assert h.raiz().id == 4


def test_remover_no_do_meio():
    h = novo_heap()
    for i in range(1, 11):
        h.inserir(ItemTeste(i, (i % 5) + 1, f"08:{i:02d}"))
        h.validar()

    removido = h.remover(5)
    assert removido.id == 5
    assert h.contem(5) is False
    assert h.tamanho() == 9
    h.validar()

    chaves = []
    while h.tamanho() > 0:
        chaves.append(h.extrair_minimo().chave())
        h.validar()
    assert chaves == sorted(chaves)


def test_id_duplicado_rejeitado():
    h = novo_heap()
    h.inserir(ItemTeste(1, 3, "08:00"))
    with pytest.raises(ValueError):
        h.inserir(ItemTeste(1, 2, "08:01"))
    assert h.tamanho() == 1
    h.validar()


def test_500_operacoes_aleatorias():
    rng = random.Random(2026)
    h = novo_heap()
    ativos = {}
    prox_id = 1

    for _ in range(500):
        op = rng.choices(
            ["inserir", "extrair", "alterar", "remover"],
            weights=[45, 20, 20, 15],
        )[0]
        if op == "inserir" or not ativos:
            item = ItemTeste(prox_id, rng.randint(1, 5), f"08:{rng.randint(0, 59):02d}")
            prox_id += 1
            h.inserir(item)
            ativos[item.id] = item
        elif op == "extrair":
            esperado = min(ativos.values(), key=lambda x: x.chave())
            obtido = h.extrair_minimo()
            assert obtido.id == esperado.id
            del ativos[obtido.id]
        elif op == "alterar":
            alvo_id = rng.choice(list(ativos.keys()))
            ativos[alvo_id].prioridade = rng.randint(1, 5)
            h.alterar_prioridade(alvo_id)
        else:
            alvo_id = rng.choice(list(ativos.keys()))
            removido = h.remover(alvo_id)
            assert removido.id == alvo_id
            del ativos[alvo_id]

        h.validar()
        assert h.tamanho() == len(ativos)
        if ativos:
            esperado_raiz = min(ativos.values(), key=lambda x: x.chave())
            assert h.raiz().id == esperado_raiz.id
        else:
            assert h.raiz() is None
