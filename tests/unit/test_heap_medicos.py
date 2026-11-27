"""T15 / H10 / H11 / H12: testes unitários do Heap de médicos."""

from core.heap import MinHeap
from core.medico import Medico


def novo_heap_medicos():
    return MinHeap(chave=lambda m: m.chave_heap(), id_de=lambda m: m.id)


def test_ordem_inicial_por_id():
    h = novo_heap_medicos()
    c = Medico(3, "Dra. C", "CRM-C")
    a = Medico(1, "Dra. A", "CRM-A")
    b = Medico(2, "Dr. B", "CRM-B")
    for m in (c, a, b):
        h.inserir(m)

    assert [h.extrair_minimo().id for _ in range(3)] == [1, 2, 3]
    h.validar()


def test_desempate_por_seq_ultima_atribuicao_e_id():
    h = novo_heap_medicos()
    a = Medico(1, "Dra. A", "CRM-A")
    b = Medico(2, "Dr. B", "CRM-B")
    c = Medico(3, "Dra. C", "CRM-C")

    # Todos com 1 concluído, mas atribuídos em momentos diferentes
    a.concluidos = 1
    a.seq_ultima_atribuicao = 3
    b.concluidos = 1
    b.seq_ultima_atribuicao = 1
    c.concluidos = 1
    c.seq_ultima_atribuicao = 2

    for m in (a, b, c):
        h.inserir(m)

    assert [h.extrair_minimo().id for _ in range(3)] == [2, 3, 1]
    h.validar()


def test_reinsercao_apos_conclusao_vai_para_posicao_certa():
    h = novo_heap_medicos()
    a = Medico(1, "Dra. A", "CRM-A")
    b = Medico(2, "Dr. B", "CRM-B")
    c = Medico(3, "Dra. C", "CRM-C")
    for m in (a, b, c):
        h.inserir(m)

    # A é chamado (seq=1), conclui (+1) e volta pro heap
    chamado = h.extrair_minimo()
    assert chamado.id == 1
    chamado.seq_ultima_atribuicao = 1
    chamado.concluidos += 1
    h.inserir(chamado)
    h.validar()

    # Próximos devem ser B (0, 0, 2), C (0, 0, 3) e só depois A (1, 1, 1)
    assert [h.extrair_minimo().id for _ in range(3)] == [2, 3, 1]
    h.validar()
