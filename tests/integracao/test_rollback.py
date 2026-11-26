"""T19 / H19: uma falha no meio da operação não altera o estado.

A parte de falha em estrutura assume os métodos HashTable.inserir,
RBTree.inserir e MinHeap.inserir.
"""

import importlib

import pytest

from tests.apoio import assert_consistente, ids, novo_sistema


class Falha(Exception):
    pass


def falhar_uma_vez(original):
    """Falha só na primeira chamada, para não derrubar as compensações."""
    chamadas = []

    def falso(*args):
        if not chamadas:
            chamadas.append(1)
            raise Falha()
        return original(*args)

    return falso


def repositorio_que_falha():
    from core.repositorio import RepositorioMemoria

    class RepositorioFalho(RepositorioMemoria):
        ligado = False

        def _talvez(self):
            if self.ligado:
                raise Falha()

        def salvar_paciente(self, *a):
            self._talvez()

        def salvar_medico(self, *a):
            self._talvez()

        def salvar_atendimento(self, *a):
            self._talvez()

        def salvar_contadores(self, *a):
            self._talvez()

    return RepositorioFalho()


def foto(s):
    """Estado observável pela API pública."""
    proximo = s.proximo_paciente()
    return (
        [(p.id, p.situacao, p.prioridade, p.retorno) for p in s.listar_pacientes()],
        [(m.id, m.situacao, m.concluidos, m.seq_ultima_atribuicao) for m in s.listar_medicos()],
        ids(s.listar_fila_chegada()),
        ids(s.listar_fila_prioridade()),
        ids(s.listar_historico_chegadas()),
        [(a.id, a.status) for a in s.listar_atendimentos_ativos()],
        [(a.id, a.status) for a in s.historico_atendimentos()],
        None if proximo is None else proximo.id,
    )


def cenario(repositorio=None):
    """Um atendimento ativo, um paciente na fila e um médico livre."""
    s = novo_sistema(repositorio)
    s.cadastrar_medico("Dr. Ficticio A", "CRM-FIC-A")
    s.cadastrar_medico("Dr. Ficticio B", "CRM-FIC-B")
    s.cadastrar_paciente("Ficticio 1", 2)
    s.cadastrar_paciente("Ficticio 2", 3)
    atendimento = s.chamar_proximo()
    return s, atendimento


OPERACOES = {
    "cadastrar_paciente": lambda s, a: s.cadastrar_paciente("Novo", 3),
    "cadastrar_medico": lambda s, a: s.cadastrar_medico("Novo", "CRM-FIC-N"),
    "reclassificar": lambda s, a: s.reclassificar(2, 1),
    "cancelar_paciente": lambda s, a: s.cancelar_paciente(2),
    "chamar_proximo": lambda s, a: s.chamar_proximo(),
    "concluir_atendimento": lambda s, a: s.concluir_atendimento(a.id),
    "cancelar_atendimento": lambda s, a: s.cancelar_atendimento(a.id),
}


@pytest.mark.parametrize("nome", OPERACOES)
def test_falha_na_gravacao(nome):
    repositorio = repositorio_que_falha()
    s, atendimento = cenario(repositorio)
    antes = foto(s)
    repositorio.ligado = True
    with pytest.raises(Falha):
        OPERACOES[nome](s, atendimento)
    repositorio.ligado = False
    assert foto(s) == antes
    assert_consistente(s)


@pytest.mark.parametrize(
    "operacao, modulo, classe",
    [
        ("cadastrar_paciente", "core.rbtree", "RBTree"),
        ("cadastrar_paciente", "core.heap", "MinHeap"),
        ("cadastrar_medico", "core.heap", "MinHeap"),
        ("cancelar_atendimento", "core.heap", "MinHeap"),
        ("concluir_atendimento", "core.heap", "MinHeap"),
    ],
)
def test_falha_em_estrutura(monkeypatch, operacao, modulo, classe):
    s, atendimento = cenario()
    antes = foto(s)
    alvo = getattr(importlib.import_module(modulo), classe)
    with monkeypatch.context() as m:
        m.setattr(alvo, "inserir", falhar_uma_vez(alvo.inserir))
        with pytest.raises(Falha):
            OPERACOES[operacao](s, atendimento)
    assert foto(s) == antes
    assert_consistente(s)
