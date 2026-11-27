"""T20 / H08-H14: testes de integração de médicos, chamadas e conclusão."""

import pytest

from core.atendimento import CONCLUIDO as ATEND_CONCLUIDO, EM_ANDAMENTO
from core.erros import (
    ErroValidacao,
    EstadoInvalido,
    FilaVazia,
    NaoEncontrado,
    SemMedicoDisponivel,
)
from core.medico import DISPONIVEL, EM_ATENDIMENTO as MED_EM_ATENDIMENTO
from core.paciente import CONCLUIDO as PAC_CONCLUIDO, EM_ATENDIMENTO as PAC_EM_ATENDIMENTO
from tests.apoio import (
    assert_consistente,
    cadastrar_medicos,
    cadastrar_pacientes,
    ids,
    novo_sistema,
)


def test_cadastrar_consultar_listar_medico():
    s = novo_sistema()
    m1 = s.cadastrar_medico("Ana Ficticia", "123")
    m2 = s.cadastrar_medico("bruno DA silva", "", "sp")
    assert m1.id == 1
    assert m2.id == 2
    assert m1.situacao == DISPONIVEL
    assert m1.concluidos == 0
    assert s.consultar_medico(m1.id).nome == "Ana Ficticia"
    assert ids(s.listar_medicos()) == [m1.id, m2.id]

    with pytest.raises(ErroValidacao):
        s.cadastrar_medico("", "1")
    with pytest.raises(ErroValidacao):
        s.cadastrar_medico("Dr. Xavier", "")
    with pytest.raises(NaoEncontrado):
        s.consultar_medico(999)
    assert m1.registro == "CRM/RJ 000123"
    assert m2.nome == "Bruno da Silva"
    assert m2.registro == "CRM/SP 000002"
    assert_consistente(s)


def test_crm_repetido_e_recusado_sem_alterar_estado():
    s = novo_sistema()
    m1 = s.cadastrar_medico("Ana Ficticia", "4567", "RJ")
    for numero in ("4567", "004567", " 4567 "):
        with pytest.raises(ErroValidacao, match="já existe médico"):
            s.cadastrar_medico("Bruno Ficticio", numero, "rj")
    m2 = s.cadastrar_medico("Bruno Ficticio", "4567", "SP")
    assert m2.id == m1.id + 1
    assert m2.registro == "CRM/SP 004567"
    assert ids(s.listar_medicos()) == [m1.id, m2.id]
    assert_consistente(s)


def test_crm_gerado_automaticamente_e_unico():
    s = novo_sistema()
    manual = s.cadastrar_medico("Ana Ficticia", "2")
    auto1 = s.cadastrar_medico("Bruno Ficticio", "")
    auto2 = s.cadastrar_medico("Carla Ficticia", None)
    assert manual.registro == "CRM/RJ 000002"
    assert auto1.registro == "CRM/RJ 000003"
    assert auto2.registro == "CRM/RJ 000004"
    with pytest.raises(ErroValidacao, match="já existe médico"):
        s.cadastrar_medico("Diego Ficticio", "3")
    assert_consistente(s)


@pytest.mark.parametrize(
    "nome, registro, uf",
    [
        ("Dra. Ana", "", "RJ"),
        ("Ana 2", "", "RJ"),
        ("A", "", "RJ"),
        ("Ana Ficticia", "12.345", "RJ"),
        ("Ana Ficticia", "CRM123", "RJ"),
        ("Ana Ficticia", "1234567", "RJ"),
        ("Ana Ficticia", "", "XX"),
    ],
)
def test_cadastro_de_medico_invalido_nao_consome_id(nome, registro, uf):
    s = novo_sistema()
    with pytest.raises(ErroValidacao):
        s.cadastrar_medico(nome, registro, uf)
    assert s.cadastrar_medico("Ana Ficticia", "").id == 1
    assert_consistente(s)


def test_chamar_fila_vazia_e_sem_medico():
    s = novo_sistema()
    with pytest.raises(FilaVazia):
        s.chamar_proximo()

    (p,) = cadastrar_pacientes(s, 2)
    with pytest.raises(SemMedicoDisponivel):
        s.chamar_proximo()
    assert s.proximo_paciente().id == p.id
    assert ids(s.listar_fila_chegada()) == [p.id]
    assert_consistente(s)


def test_chamar_e_concluir_atendimento():
    s = novo_sistema()
    a, b, _ = cadastrar_medicos(s)
    (p1,) = cadastrar_pacientes(s, 3)

    atendimento = s.chamar_proximo()
    assert atendimento.paciente_id == p1.id
    assert atendimento.medico_id == a.id
    assert atendimento.status == EM_ANDAMENTO
    assert s.consultar_paciente(p1.id).situacao == PAC_EM_ATENDIMENTO
    assert s.consultar_medico(a.id).situacao == MED_EM_ATENDIMENTO
    assert s.consultar_medico(a.id).seq_ultima_atribuicao == 1
    assert ids(s.listar_atendimentos_ativos()) == [atendimento.id]
    assert_consistente(s)

    concluido = s.concluir_atendimento(atendimento.id)
    assert concluido.status == ATEND_CONCLUIDO
    assert concluido.fim is not None
    assert s.consultar_paciente(p1.id).situacao == PAC_CONCLUIDO
    assert s.consultar_medico(a.id).situacao == DISPONIVEL
    assert s.consultar_medico(a.id).concluidos == 1
    assert ids(s.listar_atendimentos_ativos()) == []
    assert ids(s.historico_atendimentos()) == [atendimento.id]
    assert_consistente(s)

    with pytest.raises(EstadoInvalido):
        s.concluir_atendimento(atendimento.id)

    # Indicadores e diagnóstico
    ind = s.indicadores()
    assert ind.concluidos == 1
    assert ind.medicos_disponiveis == 3
    diag = s.diagnostico()
    assert diag.consistencia.ok
    assert diag.rb_espera_valida
    assert diag.rb_historico_valida
