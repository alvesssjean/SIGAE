"""T06 / H21 / H02: testes unitários da Tabela Hash."""

import pytest

from core.hash_table import HashTable


def test_inserir_buscar_remover_basico():
    t = HashTable(capacidade=7)
    t.inserir(10, "dez")
    t.inserir(20, "vinte")
    assert t.tamanho() == 2
    assert len(t) == 2
    assert t.contem(10) is True
    assert 20 in t
    assert t.buscar(10) == "dez"
    assert t.buscar(20) == "vinte"
    assert t.buscar(999) is None
    assert t.remover(10) is True
    assert t.contem(10) is False
    assert t.buscar(10) is None
    assert t.tamanho() == 1
    t.validar()


def test_colisao_101_e_108_capacidade_7():
    t = HashTable(capacidade=7)
    t.inserir(101, "paciente-101")
    t.inserir(108, "paciente-108")
    assert 101 % 7 == 108 % 7
    assert t.buscar(101) == "paciente-101"
    assert t.buscar(108) == "paciente-108"
    est = t.estatisticas()
    assert est.capacidade == 7
    assert est.buckets_ocupados == 1
    assert est.maior_cadeia == 2
    assert est.total_colisoes == 1
    t.validar()


def test_redimensiona_ao_ultrapassar_fator_carga_e_recalcula_buckets():
    t = HashTable(capacidade=7)
    # 5 itens: 5/7 = 0.714 <= 0.75 (não redimensiona)
    for chave in range(1, 6):
        t.inserir(chave, f"v{chave}")
    assert t.capacidade() == 7
    assert t.fator_carga() == pytest.approx(5 / 7)

    # 6º item: 6/7 > 0.75 -> redimensiona para próximo primo >= 14 (17)
    t.inserir(6, "v6")
    assert t.capacidade() == 17
    assert t.tamanho() == 6
    assert t.fator_carga() == pytest.approx(6 / 17)

    # Inserir mais até ultrapassar 0.75 de 17 (13 itens -> 37)
    for chave in range(7, 25):
        t.inserir(chave, f"v{chave}")
    assert t.capacidade() == 37
    assert t.fator_carga() <= 0.75

    for chave in range(1, 25):
        assert t.buscar(chave) == f"v{chave}"
    t.validar()


def test_remover_inicio_meio_fim_da_cadeia():
    t = HashTable(capacidade=7)
    # Todos no bucket 3 (3, 10, 17)
    t.inserir(3, "tres")
    t.inserir(10, "dez")
    t.inserir(17, "dezessete")
    t.validar()

    # Cadeia tem 17 -> 10 -> 3 (inserção no início)
    # Remove meio (10)
    assert t.remover(10) is True
    assert t.buscar(10) is None
    assert t.buscar(3) == "tres"
    assert t.buscar(17) == "dezessete"
    t.validar()

    # Remove fim (3)
    assert t.remover(3) is True
    assert t.buscar(3) is None
    assert t.buscar(17) == "dezessete"
    t.validar()

    # Remove início (17)
    assert t.remover(17) is True
    assert t.tamanho() == 0
    t.validar()


def test_remover_inexistente_retorna_false():
    t = HashTable(capacidade=7)
    t.inserir(1, "um")
    assert t.remover(99) is False
    assert t.tamanho() == 1
    t.validar()


def test_duplicata_rejeitada():
    t = HashTable(capacidade=7)
    t.inserir(42, "a")
    with pytest.raises(ValueError):
        t.inserir(42, "b")
    assert t.buscar(42) == "a"
    assert t.tamanho() == 1
    t.validar()


def test_valores_e_ids_geradores_sem_devolver_list():
    t = HashTable(capacidade=7)
    t.inserir(1, "a")
    t.inserir(2, "b")
    t.inserir(3, "c")

    gen_valores = t.valores()
    gen_ids = t.ids()
    assert not isinstance(gen_valores, list)
    assert not isinstance(gen_ids, list)
    assert set(gen_valores) == {"a", "b", "c"}
    assert set(gen_ids) == {1, 2, 3}


def test_atualizar_existente():
    t = HashTable(capacidade=7)
    t.inserir(5, "antigo")
    t.atualizar(5, "novo")
    assert t.buscar(5) == "novo"
    assert t.tamanho() == 1
    t.validar()
