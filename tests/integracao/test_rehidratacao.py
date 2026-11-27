"""T24 e T25 / H19 / H20: testes de persistência transacional e rehidratação do SQLite."""

import pytest

from core.erros import EstadoInvalido
from core.relogio import RelogioFalso
from core.sistema import Sistema
from tests.apoio import assert_consistente, ids


def _estado(s: Sistema):
    prox = s.proximo_paciente()
    ind = s.indicadores()
    return (
        [(p.id, p.nome, p.horario, p.prioridade, p.situacao, p.retorno, list(p.medicos_que_cancelaram)) for p in s.listar_pacientes()],
        [(m.id, m.nome, m.registro, m.situacao, m.concluidos, m.seq_ultima_atribuicao) for m in s.listar_medicos()],
        ids(s.listar_fila_chegada()),
        ids(s.listar_fila_prioridade()),
        ids(s.listar_historico_chegadas()),
        [(a.id, a.paciente_id, a.medico_id, a.status, a.inicio, a.fim) for a in s.listar_atendimentos_ativos()],
        [(a.id, a.paciente_id, a.medico_id, a.status, a.inicio, a.fim) for a in s.historico_atendimentos()],
        None if prox is None else prox.id,
        (ind.aguardando, ind.em_atendimento, ind.concluidos, ind.cancelados),
    )


def test_rehidratacao_preserva_estado_completo_e_cancelamentos(banco):
    from web.atendimento.repositorio_django import RepositorioDjango

    repo = RepositorioDjango()
    relogio = RelogioFalso("2026-11-27 08:00:00")
    s1 = Sistema.carregar(repo, relogio=relogio)

    m1 = s1.cadastrar_medico("Ana Ficticia", "")
    m2 = s1.cadastrar_medico("Bruno Ficticio", "")
    p1 = s1.cadastrar_paciente("Paciente Um", 4)
    p2 = s1.cadastrar_paciente("Paciente Dois", 2)
    p3 = s1.cadastrar_paciente("Paciente Tres", 5)
    p4 = s1.cadastrar_paciente("Paciente Quatro", 1)

    # Chama p4 (Emergência -> m1) e conclui
    a1 = s1.chamar_proximo()
    assert a1.paciente_id == p4.id
    s1.concluir_atendimento(a1.id)

    # Chama p2 (Muito urgente -> m2) e cancela (devolvido volta ao topo atrás das Emergências)
    a2 = s1.chamar_proximo()
    assert a2.paciente_id == p2.id
    s1.cancelar_atendimento(a2.id)

    # Reclassifica p3 e cancela cadastro de p1
    s1.reclassificar(p3.id, 3)
    s1.cancelar_paciente(p1.id)

    # Novo atendimento ativo: chama p2 (devolvido -> m1, pois m2 teve 0 concluídos e seq=2, m1 teve 1 concluído; m2 é escolhido!)
    a3 = s1.chamar_proximo()
    assert a3.paciente_id == p2.id
    assert a3.medico_id == m2.id
    assert_consistente(s1)

    # Simula reinício do servidor: novo Sistema rehidratado do mesmo SQLite
    s2 = Sistema.carregar(RepositorioDjango(), relogio=relogio)
    assert_consistente(s2)
    assert _estado(s2) == _estado(s1)

    # Regra de cancelamento continua valendo após reinício (m2 já cancelou p2!)
    with pytest.raises(EstadoInvalido):
        s2.cancelar_atendimento(a3.id)

    # Contadores de ID continuam crescentes sem colidir
    novo = s2.cadastrar_paciente("Paciente Cinco", 2)
    assert novo.id == 5
    assert_consistente(s2)


def test_falha_injetada_na_transacao_nao_deixa_linha_parcial_no_sqlite(banco):
    from web.atendimento.models import AtendimentoModel, MedicoModel, PacienteModel
    from web.atendimento.repositorio_django import RepositorioDjango

    class FalhaPersist(Exception):
        pass

    class RepositorioFalhaContadores(RepositorioDjango):
        def salvar_contadores(self, *args):
            raise FalhaPersist("falha após gravar entidades")

    repo = RepositorioFalhaContadores()
    s = Sistema.carregar(repo, relogio=RelogioFalso("2026-11-27 08:00:00"))

    with pytest.raises(FalhaPersist):
        s.cadastrar_paciente("Nao Deve Persistir", 2)

    assert PacienteModel.objects.count() == 0
    assert MedicoModel.objects.count() == 0
    assert AtendimentoModel.objects.count() == 0
    assert len(s.listar_pacientes()) == 0
    assert_consistente(s)
