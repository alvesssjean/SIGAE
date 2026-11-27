"""T38 / H07 / H20: consistência entre estruturas em memória e SQLite em 200 operações."""

import random

from core.medico import DISPONIVEL
from core.paciente import AGUARDANDO, CANCELADO, CONCLUIDO, EM_ATENDIMENTO
from core.relogio import RelogioFalso
from core.sistema import Sistema
from tests.apoio import NUMERAIS, nome_paciente


def test_consistencia_200_operacoes_estruturas_e_sqlite(banco):
    from web.atendimento.models import AtendimentoModel, MedicoModel, PacienteModel
    from web.atendimento.repositorio_django import RepositorioDjango

    rng = random.Random(42)
    repo = RepositorioDjango()
    s = Sistema.carregar(repo, relogio=RelogioFalso("2026-11-27 08:00:00"))

    for i in range(1, 5):
        s.cadastrar_medico(f"Medico Ficticio {NUMERAIS[i]}", "")

    for passo in range(1, 201):
        aguardando = [p for p in s.listar_pacientes() if p.situacao == AGUARDANDO]
        ativos = list(s.listar_atendimentos_ativos())
        medicos_livres = [m for m in s.listar_medicos() if m.situacao == DISPONIVEL]

        escolhas = ["cadastrar"]
        if aguardando:
            escolhas.extend(["reclassificar", "cancelar_paciente"])
        if aguardando and medicos_livres:
            escolhas.extend(["chamar", "chamar"])
        if ativos:
            escolhas.extend(["concluir", "cancelar_atendimento"])

        acao = rng.choice(escolhas)
        if acao == "cadastrar":
            s.cadastrar_paciente(nome_paciente(passo), rng.randint(1, 5))
        elif acao == "reclassificar":
            alvo = rng.choice(aguardando)
            s.reclassificar(alvo.id, rng.randint(1, 5))
        elif acao == "cancelar_paciente":
            alvo = rng.choice(aguardando)
            s.cancelar_paciente(alvo.id)
        elif acao == "chamar":
            s.chamar_proximo()
        elif acao == "concluir":
            atend = rng.choice(ativos)
            s.concluir_atendimento(atend.id)
        elif acao == "cancelar_atendimento":
            atend = rng.choice(ativos)
            pac = s.consultar_paciente(atend.paciente_id)
            if not pac.medicos_que_cancelaram.contem(atend.medico_id):
                s.cancelar_atendimento(atend.id)
            else:
                s.concluir_atendimento(atend.id)

        if passo % 20 == 0:
            assert s.validar_indices().ok

    assert s.validar_indices().ok

    # Comparação final: Hash vs RB espera vs Heap pacientes vs SQLite
    ids_hash_aguardando = {
        p.id for p in s.listar_pacientes() if p.situacao == AGUARDANDO
    }
    ids_rb_espera = {p.id for p in s.listar_fila_chegada()}
    ids_heap_pacientes = {p.id for p in s.listar_fila_prioridade()}
    assert ids_hash_aguardando == ids_rb_espera == ids_heap_pacientes

    # Leitura do SQLite apenas para verificação
    db_pacientes = list(PacienteModel.objects.all())
    for situacao in (AGUARDANDO, EM_ATENDIMENTO, CONCLUIDO, CANCELADO):
        ids_mem = {p.id for p in s.listar_pacientes() if p.situacao == situacao}
        ids_db = {p.id for p in db_pacientes if p.situacao == situacao}
        assert ids_mem == ids_db

    db_medicos = list(MedicoModel.objects.all())
    ids_med_disp_mem = {m.id for m in s.listar_medicos() if m.situacao == DISPONIVEL}
    ids_med_disp_db = {m.id for m in db_medicos if m.situacao == DISPONIVEL}
    assert ids_med_disp_mem == ids_med_disp_db

    db_atendimentos = list(AtendimentoModel.objects.all())
    ids_atend_mem = {a.id for a in s.listar_atendimentos_ativos()} | {
        a.id for a in s.historico_atendimentos()
    }
    ids_atend_db = {a.id for a in db_atendimentos}
    assert ids_atend_mem == ids_atend_db

    # Verifica que um novo Sistema rehidratado também é consistente e igual
    s_rehidratado = Sistema.carregar(RepositorioDjango())
    assert s_rehidratado.validar_indices().ok
    assert [p.id for p in s_rehidratado.listar_fila_prioridade()] == [
        p.id for p in s.listar_fila_prioridade()
    ]
    assert [p.id for p in s_rehidratado.listar_fila_chegada()] == [
        p.id for p in s.listar_fila_chegada()
    ]
