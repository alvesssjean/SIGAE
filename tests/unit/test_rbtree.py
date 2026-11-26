import inspect
import math
import random

import pytest

from core.lista_encadeada import ListaEncadeada
from core.rbtree import NEGRO, VERMELHO, No, RBInvalidaError, RBTree, rotulo


def k(n: int):
    return (f"2026-11-26 {n // 60:02d}:{n % 60:02d}:00", n)


def chaves(t):
    return [c for c, _ in t.em_ordem()]


def eventos(t):
    return [e for e in t.eventos]


def no(n, cor, esq=None, dir=None):
    x = No(k(n), cor=cor)
    x.esq, x.dir = esq, dir
    for filho in (esq, dir):
        if filho is not None:
            filho.pai = x
    return x


def montar(raiz):
    t = RBTree()
    t._raiz = raiz

    def contar(x):
        return 0 if x is None else 1 + contar(x.esq) + contar(x.dir)

    t._tamanho = contar(raiz)
    return t


def forma(x):
    if x is None:
        return None
    return (x.chave[1], x.cor, forma(x.esq), forma(x.dir))


def construir(*ns):
    t = RBTree()
    for n in ns:
        t.inserir(k(n))
    return t


def test_validar_aceita_arvore_valida():
    t = montar(no(2, NEGRO, no(1, VERMELHO), no(3, VERMELHO)))
    t.validar()
    assert t.esta_valida()


def test_validar_aceita_arvore_vazia():
    RBTree().validar()


def test_validar_rejeita_raiz_vermelha():
    with pytest.raises(RBInvalidaError, match="raiz"):
        montar(no(2, VERMELHO)).validar()


def test_validar_rejeita_dois_vermelhos_seguidos():
    t = montar(no(3, NEGRO, no(2, VERMELHO, no(1, VERMELHO))))
    with pytest.raises(RBInvalidaError, match="vermelhos seguidos"):
        t.validar()


def test_validar_rejeita_altura_negra_diferente():
    t = montar(no(2, NEGRO, no(1, NEGRO)))
    with pytest.raises(RBInvalidaError, match="altura negra"):
        t.validar()


def test_validar_rejeita_ordem_violada():
    t = montar(no(2, NEGRO, no(3, VERMELHO)))
    with pytest.raises(RBInvalidaError, match="ordem"):
        t.validar()


def test_validar_rejeita_tamanho_incoerente():
    t = montar(no(2, NEGRO, no(1, VERMELHO), no(3, VERMELHO)))
    t._tamanho = 99
    with pytest.raises(RBInvalidaError, match="tamanho"):
        t.validar()


def test_esta_valida_devolve_false_em_vez_de_levantar():
    assert montar(no(2, VERMELHO)).esta_valida() is False


def test_arvore_vazia():
    t = RBTree()
    assert len(t) == 0
    assert chaves(t) == []
    assert t.altura() == 0
    assert t.buscar(k(1)) is None
    assert k(1) not in t


def test_em_ordem_de_arvore_montada():
    t = montar(no(2, NEGRO, no(1, VERMELHO), no(3, VERMELHO)))
    assert chaves(t) == [k(1), k(2), k(3)]
    assert t.altura() == 2
    assert k(3) in t and k(9) not in t


def test_em_ordem_e_gerador():
    assert inspect.isgenerator(RBTree().em_ordem())


def test_em_ordem_percorre_por_sucessor_em_arvore_grande():
    t = RBTree()
    for n in range(3000):
        t.inserir(("2026-11-26 00:00:00", n), n)
    assert [v for _, v in t.em_ordem()] == list(range(3000))


def test_inserir_na_vazia_raiz_negra():
    t = construir(1)
    assert forma(t._raiz) == (1, NEGRO, None, None)
    assert len(t) == 1
    t.validar()


def test_inserir_pai_negro_sem_correcao():
    t = construir(2, 1)
    assert forma(t._raiz) == (2, NEGRO, (1, VERMELHO, None, None), None)
    t.validar()


def test_inserir_tio_vermelho_apenas_recolore():
    t = construir(10, 5, 15, 1)
    assert forma(t._raiz) == (
        10,
        NEGRO,
        (5, NEGRO, (1, VERMELHO, None, None), None),
        (15, NEGRO, None, None),
    )
    t.validar()


ESPERADO_APOS_ROTACAO = (2, NEGRO, (1, VERMELHO, None, None), (3, VERMELHO, None, None))


@pytest.mark.parametrize(
    "ordem",
    [(3, 2, 1), (1, 2, 3), (3, 1, 2), (1, 3, 2)],
    ids=["LL", "RR", "LR", "RL"],
)
def test_inserir_tio_negro_rotacoes(ordem):
    t = construir(*ordem)
    assert forma(t._raiz) == ESPERADO_APOS_ROTACAO
    t.validar()


def test_inserir_rotacao_em_subarvore_profunda():
    t = construir(10, 5, 20, 1, 7, 15, 30, 25, 27)
    t.validar()
    assert chaves(t) == [k(n) for n in sorted([10, 5, 20, 1, 7, 15, 30, 25, 27])]


def test_inserir_ordena_por_horario_e_depois_id():
    t = RBTree()
    chaves_inseridas = [
        ("2026-11-26 10:00:00", 1),
        ("2026-11-26 09:30:00", 2),
        ("2026-11-26 09:30:00", 1),
        ("2026-11-26 08:05:00", 3),
    ]
    for chave in chaves_inseridas:
        t.inserir(chave)
    assert chaves(t) == [
        ("2026-11-26 08:05:00", 3),
        ("2026-11-26 09:30:00", 1),
        ("2026-11-26 09:30:00", 2),
        ("2026-11-26 10:00:00", 1),
    ]
    t.validar()


def test_inserir_mesmo_segundo_desempata_por_id():
    t = RBTree()
    for id_paciente in (5, 3, 4):
        t.inserir(("2026-11-26 08:00:00", id_paciente))
    assert [c[1] for c in chaves(t)] == [3, 4, 5]
    t.validar()


def test_inserir_chaves_de_dias_diferentes_em_ordem_cronologica():
    t = RBTree()
    for chave in [
        ("2026-11-26 00:00:00", 2),
        ("2026-11-25 23:59:59", 1),
        ("2026-12-01 07:00:00", 3),
        ("2026-11-26 00:00:01", 4),
    ]:
        t.inserir(chave)
    assert [c[1] for c in chaves(t)] == [1, 2, 4, 3]
    t.validar()


def test_inserir_guarda_valor_e_buscar_devolve():
    t = RBTree()
    t.inserir(k(1), valor=7)
    assert t.buscar(k(1)) == 7
    assert t.buscar(k(2)) is None


def test_em_ordem_devolve_pares_chave_valor():
    t = RBTree()
    t.inserir(k(2), valor="b")
    t.inserir(k(1), valor="a")
    assert list(t.em_ordem()) == [(k(1), "a"), (k(2), "b")]


def test_inserir_duplicada_levanta_e_nao_altera():
    t = construir(5, 3, 8)
    antes = (forma(t._raiz), list(t.em_ordem()), len(t))
    with pytest.raises(ValueError):
        t.inserir(k(5), valor=99)
    assert (forma(t._raiz), list(t.em_ordem()), len(t)) == antes
    assert t.buscar(k(5)) is None
    t.validar()


def _checar_altura(t):
    assert t.altura() <= 2 * math.log2(len(t) + 1)


@pytest.mark.parametrize(
    "gerar",
    [
        lambda: list(range(1, 201)),
        lambda: list(range(200, 0, -1)),
        lambda: random.Random(42).sample(range(1, 1001), 300),
    ],
    ids=["crescente", "decrescente", "aleatoria"],
)
def test_inserir_volume_mantem_propriedades(gerar):
    ns = gerar()
    t = RBTree()
    for i, n in enumerate(ns, start=1):
        t.inserir(k(n))
        t.validar()
        assert len(t) == i
    assert chaves(t) == [k(n) for n in sorted(ns)]
    _checar_altura(t)


def test_remover_inexistente_devolve_false():
    t = construir(1, 2, 3)
    assert t.remover(k(9)) is False
    assert len(t) == 3
    t.validar()


def test_remover_em_arvore_vazia_devolve_false():
    assert RBTree().remover(k(1)) is False


def test_remover_unica_chave_deixa_vazia():
    t = construir(1)
    assert t.remover(k(1)) is True
    assert len(t) == 0 and chaves(t) == []
    t.validar()


def test_remover_folha_vermelha():
    t = construir(2, 1, 3)
    assert t.remover(k(1)) is True
    assert chaves(t) == [k(2), k(3)]
    t.validar()


def test_remover_folha_negra_faz_correcao():
    t = construir(10, 5, 15, 1)
    assert t.remover(k(15)) is True
    assert chaves(t) == [k(1), k(5), k(10)]
    t.validar()


def test_remover_no_com_um_filho():
    t = construir(10, 5, 15, 20)
    assert forma(t._raiz) == (
        10,
        NEGRO,
        (5, NEGRO, None, None),
        (15, NEGRO, None, (20, VERMELHO, None, None)),
    )
    assert t.remover(k(15)) is True
    assert forma(t._raiz) == (
        10,
        NEGRO,
        (5, NEGRO, None, None),
        (20, NEGRO, None, None),
    )
    t.validar()


def test_remover_no_com_dois_filhos():
    t = construir(10, 5, 15, 3, 7, 12, 20)
    assert t.remover(k(10)) is True
    assert k(10) not in t
    assert chaves(t) == [k(n) for n in (3, 5, 7, 12, 15, 20)]
    t.validar()


def test_remover_raiz_repetidamente():
    t = construir(*range(1, 32))
    while len(t):
        t.remover(t._raiz.chave)
        t.validar()


@pytest.mark.parametrize("semente", [1, 2, 3])
def test_remover_aleatorio_validando_a_cada_passo(semente):
    rnd = random.Random(semente)
    ns = rnd.sample(range(1, 500), 150)
    t = construir(*ns)
    restantes = set(ns)
    for n in rnd.sample(ns, 150):
        assert t.remover(k(n)) is True
        restantes.discard(n)
        t.validar()
        assert chaves(t) == [k(x) for x in sorted(restantes)]
    assert len(t) == 0


def test_remover_e_reinserir_mesma_chave():
    t = construir(1, 2, 3)
    assert t.remover(k(2)) is True
    t.inserir(k(2))
    assert chaves(t) == [k(1), k(2), k(3)]
    t.validar()


def test_remover_e_reinserir_com_a_chave_original_mantem_a_ordem_de_chegada():
    t = construir(*range(1, 21))
    valor = "paciente 7"
    t.inserir(k(100), valor)
    assert t.remover(k(100)) is True
    t.inserir(k(100), valor)
    assert chaves(t) == [k(n) for n in list(range(1, 21)) + [100]]
    assert t.buscar(k(100)) == valor
    t.validar()


def test_remover_valida_altura_e_tamanho_no_volume():
    rnd = random.Random(7)
    ns = rnd.sample(range(0, 1440), 600)
    t = construir(*ns)
    for n in rnd.sample(ns, 400):
        t.remover(k(n))
    t.validar()
    assert len(t) == 200
    _checar_altura(t)


def test_remover_guarda_valores_dos_que_ficam():
    t = RBTree()
    for n in range(1, 40):
        t.inserir(k(n), valor=f"p{n}")
    for n in range(1, 40, 2):
        t.remover(k(n))
    assert [v for _, v in t.em_ordem()] == [f"p{n}" for n in range(2, 40, 2)]
    t.validar()


def test_duas_instancias_sao_independentes():
    espera, historico = RBTree(), RBTree()
    for n in (1, 2, 3):
        espera.inserir(k(n))
        historico.inserir(k(n))
    espera.remover(k(2))
    assert chaves(espera) == [k(1), k(3)]
    assert chaves(historico) == [k(1), k(2), k(3)]


def test_sem_rastreio_eventos_ficam_vazios():
    t = RBTree()
    for n in (3, 2, 1):
        t.inserir(k(n))
    assert len(t.eventos) == 0
    assert not t.eventos


def test_eventos_sao_lista_encadeada():
    t = RBTree(rastrear=True)
    t.inserir(k(1))
    assert isinstance(t.eventos, ListaEncadeada)
    assert len(t.eventos) >= 1


def test_rastreio_registra_recoloracao_na_insercao():
    t = RBTree(rastrear=True)
    for n in (10, 5, 15):
        t.inserir(k(n))
    t.inserir(k(1))
    recolores = [e for e in eventos(t) if e.startswith("recolorir")]
    assert len(recolores) == 4
    assert any("caso 1" in e for e in eventos(t))
    assert f"recolorir {rotulo(k(5))}: vermelho -> negro" in eventos(t)


def test_rastreio_registra_rotacao_na_insercao():
    t = RBTree(rastrear=True)
    for n in (3, 2, 1):
        t.inserir(k(n))
    assert any("rotação à direita" in e for e in eventos(t))
    assert any("caso 3" in e for e in eventos(t))


def test_rastreio_zigue_zague_faz_duas_rotacoes():
    t = RBTree(rastrear=True)
    for n in (3, 1, 2):
        t.inserir(k(n))
    rotacoes = [e for e in eventos(t) if e.startswith("rotação")]
    assert len(rotacoes) == 2
    assert any("caso 2" in e for e in eventos(t))


def test_eventos_sao_da_ultima_operacao():
    t = RBTree(rastrear=True)
    t.inserir(k(1))
    t.inserir(k(2))
    assert eventos(t)[0].startswith(f"inserir {rotulo(k(2))}")
    t.remover(k(2))
    assert eventos(t)[0].startswith(f"remover {rotulo(k(2))}")
    assert t.remover(k(99)) is False
    assert eventos(t) == []


def test_rastreio_registra_casos_da_remocao():
    t = RBTree(rastrear=True)
    for n in range(1, 16):
        t.inserir(k(n))
    casos = set()
    for n in range(1, 16):
        t.remover(k(n))
        casos.update(e.split(":")[0] for e in eventos(t) if e.startswith("caso"))
    assert {"caso 2", "caso 4"} <= casos


def test_rastreio_remocao_nao_altera_resultado():
    a, b = RBTree(), RBTree(rastrear=True)
    ns = random.Random(3).sample(range(0, 1440), 300)
    for n in ns:
        a.inserir(k(n))
        b.inserir(k(n))
    for n in ns[:150]:
        a.remover(k(n))
        b.remover(k(n))
    assert list(a.em_ordem()) == list(b.em_ordem())
    assert forma(a._raiz) == forma(b._raiz)


def test_desenhar_arvore_vazia():
    assert RBTree().desenhar() == "(árvore vazia)"


def test_desenhar_mostra_cores_e_lados():
    t = construir(2, 1, 3)
    linhas = t.desenhar().splitlines()
    assert linhas[0] == f"{rotulo(k(2))} [N]"
    assert linhas[1] == f"|-- E: {rotulo(k(1))} [V]"
    assert linhas[2] == f"`-- D: {rotulo(k(3))} [V]"
    assert len(linhas) == 3


def test_desenhar_so_filho_direito_e_ultimo_ramo():
    t = construir(1, 2)
    linhas = t.desenhar().splitlines()
    assert linhas == [f"{rotulo(k(1))} [N]", f"`-- D: {rotulo(k(2))} [V]"]


def test_desenhar_arvore_maior_tem_uma_linha_por_no():
    t = construir(*range(1, 16))
    assert len(t.desenhar().splitlines()) == 15


def test_desenhar_com_cores_usa_codigos_ansi():
    t = construir(2, 1, 3)
    assert "\033[91m" in t.desenhar(cores=True)
    assert "\033[7m" in t.desenhar(cores=True)
    assert "\033[" not in t.desenhar()
