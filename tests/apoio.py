"""Apoio aos testes do sistema.

Os imports de core ficam dentro das funções para que os testes em xfail sejam
coletados antes de o código existir.

NOMES ASSUMIDOS (fora do contrato do BACKLOG 2.1, combinar com I1 e I3):
  core.sistema.Sistema, core.repositorio.RepositorioMemoria,
  core.relogio.RelogioFalso, exceções em core.erros,
  constantes de situação em core.paciente / core.medico / core.atendimento,
  validar_indices() devolve objeto com o atributo booleano `ok`.
"""

INICIO = "2026-11-27 08:00:00"

NUMERAIS = ("Zero", "Um", "Dois", "Tres", "Quatro", "Cinco", "Seis", "Sete", "Oito", "Nove")
MEDICOS_FICTICIOS = ("Ana Ficticia", "Bruno Ficticio", "Carla Ficticia")


def nome_paciente(numero):
    """Nome válido e único sem dígitos: 12 -> "Paciente Um Dois"."""
    return "Paciente " + " ".join(NUMERAIS[int(d)] for d in str(numero))


def novo_sistema(repositorio=None):
    from core.relogio import RelogioFalso
    from core.repositorio import RepositorioMemoria
    from core.sistema import Sistema

    return Sistema(repositorio or RepositorioMemoria(), relogio=RelogioFalso(INICIO))


def ids(itens):
    return [item.id for item in itens]


def assert_consistente(sistema):
    assert sistema.validar_indices().ok


def cadastrar_medicos(sistema):
    return [
        sistema.cadastrar_medico(nome, "")
        for nome in MEDICOS_FICTICIOS
    ]


def cadastrar_pacientes(sistema, *prioridades):
    return [
        sistema.cadastrar_paciente(nome_paciente(i), prioridade)
        for i, prioridade in enumerate(prioridades, start=1)
    ]
