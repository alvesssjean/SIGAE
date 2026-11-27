"""Views Django do SIGAE WEB (T29-T35, T37).

Regra de arquitetura: views só chamam obter_sistema() e nunca importam
rbtree, heap, hash_table ou models. Toda mutação segue POST -> redirect -> GET.
"""

from typing import Any, Callable, Optional

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from core.erros import (
    ErroValidacao,
    EstadoInvalido,
    FilaVazia,
    NaoEncontrado,
    SemMedicoDisponivel,
)
from core.paciente import AGUARDANDO, CANCELADO, EM_ATENDIMENTO
from web.atendimento.servico import obter_sistema

ERROS_DOMINIO = (
    ErroValidacao,
    EstadoInvalido,
    FilaVazia,
    SemMedicoDisponivel,
    NaoEncontrado,
)

OPCOES_PRIORIDADE = (
    (1, "1 - Emergência"),
    (2, "2 - Muito urgente"),
    (3, "3 - Urgente"),
    (4, "4 - Pouco urgente"),
    (5, "5 - Não urgente"),
)


def _executar(
    request: HttpRequest,
    operacao: Callable[[], Any],
    mensagem_sucesso: Optional[Callable[[Any], str]] = None,
) -> Any:
    """Executa uma operação do núcleo convertendo erros de domínio em messages.error."""
    try:
        resultado = operacao()
    except ERROS_DOMINIO as exc:
        messages.error(request, str(exc))
        return None
    if mensagem_sucesso is not None:
        messages.success(request, mensagem_sucesso(resultado))
    return resultado


def _ler_inteiro(valor: str, nome_campo: str) -> int:
    texto = (valor or "").strip()
    if not texto or not texto.lstrip("-").isdigit():
        raise ErroValidacao(f"{nome_campo} deve ser um número inteiro válido")
    return int(texto)


def _enriquecer_atendimentos(sistema: Any, atendimentos_lista: Any) -> list[dict[str, Any]]:
    linhas = []
    for atendimento in atendimentos_lista:
        paciente = sistema.consultar_paciente(atendimento.paciente_id)
        medico = sistema.consultar_medico(atendimento.medico_id)
        pode_cancelar = not paciente.medicos_que_cancelaram.contem(medico.id)
        linhas.append(
            {
                "atendimento": atendimento,
                "paciente": paciente,
                "medico": medico,
                "pode_cancelar": pode_cancelar,
            }
        )
    return linhas


def _atendimento_ativo_de(sistema: Any, paciente_id: int) -> Optional[dict[str, Any]]:
    """Linha enriquecida do atendimento em andamento do paciente, se houver."""
    for item in _enriquecer_atendimentos(sistema, sistema.listar_atendimentos_ativos()):
        if item["paciente"].id == paciente_id:
            return item
    return None


def _linhas_pacientes(sistema: Any) -> list[dict[str, Any]]:
    """Pacientes com a indicação de que o cancelamento ainda é permitido.

    Para quem está Em atendimento, o cancelamento some quando o médico atual
    já cancelou esse paciente uma vez (ADR-012), como na tela Atendimentos.
    """
    bloqueados = {
        item["paciente"].id
        for item in _enriquecer_atendimentos(sistema, sistema.listar_atendimentos_ativos())
        if not item["pode_cancelar"]
    }
    return [
        {"paciente": p, "pode_cancelar": p.id not in bloqueados}
        for p in sistema.listar_pacientes()
    ]


def _destino_seguro(request: HttpRequest, padrao: str) -> str:
    origem = (request.POST.get("origem") or "").strip()
    if origem in ("painel", "triagem", "pacientes", "medicos", "atendimentos", "historico"):
        return origem
    return padrao


def painel(request: HttpRequest) -> HttpResponse:
    sistema = obter_sistema()
    indicadores = sistema.indicadores()
    proximo = sistema.proximo_paciente()
    medicos = sistema.listar_medicos()
    ativos = _enriquecer_atendimentos(sistema, sistema.listar_atendimentos_ativos())
    return render(
        request,
        "atendimento/painel.html",
        {
            "tela_ativa": "painel",
            "indicadores": indicadores,
            "proximo": proximo,
            "medicos": medicos,
            "atendimentos_ativos": ativos,
        },
    )


def chamar_proximo(request: HttpRequest) -> HttpResponse:
    destino = _destino_seguro(request, "painel")
    if request.method == "POST":
        sistema = obter_sistema()

        def mensagem(atendimento: Any) -> str:
            paciente = sistema.consultar_paciente(atendimento.paciente_id)
            medico = sistema.consultar_medico(atendimento.medico_id)
            return (
                f"Atendimento #{atendimento.id} iniciado: paciente #{paciente.id} "
                f"({paciente.nome}) atribuído a {medico.nome} ({medico.registro})."
            )

        _executar(request, sistema.chamar_proximo, mensagem)
    return redirect(destino)


def pacientes(request: HttpRequest) -> HttpResponse:
    sistema = obter_sistema()
    if request.method == "POST":
        nome = request.POST.get("nome", "")
        prioridade_raw = request.POST.get("prioridade", "")

        def cadastrar() -> Any:
            prioridade = _ler_inteiro(prioridade_raw, "prioridade")
            return sistema.cadastrar_paciente(nome, prioridade)

        _executar(
            request,
            cadastrar,
            lambda p: (
                f"Paciente #{p.id} ({p.nome}) cadastrado com prioridade "
                f"{p.prioridade} ({p.descricao_prioridade}) às {p.horario}."
            ),
        )
        return redirect(_destino_seguro(request, "pacientes"))

    paciente_buscado = None
    buscar_id = (request.GET.get("buscar_id") or "").strip()
    if buscar_id:

        def consultar() -> Any:
            pid = _ler_inteiro(buscar_id, "ID do paciente")
            return sistema.consultar_paciente(pid)

        paciente_buscado = _executar(request, consultar)

    return render(
        request,
        "atendimento/pacientes.html",
        {
            "tela_ativa": "pacientes",
            "linhas": _linhas_pacientes(sistema),
            "paciente_buscado": paciente_buscado,
            "buscar_id": buscar_id,
            "opcoes_prioridade": OPCOES_PRIORIDADE,
            "SIT_AGUARDANDO": AGUARDANDO,
            "SIT_EM_ATENDIMENTO": EM_ATENDIMENTO,
        },
    )


def cancelar_paciente(request: HttpRequest, paciente_id: int) -> HttpResponse:
    sistema = obter_sistema()
    if request.method != "POST":
        # GET: página de confirmação explicando o efeito antes de cancelar (T31).
        paciente = _executar(request, lambda: sistema.consultar_paciente(paciente_id))
        if paciente is None:
            return redirect("pacientes")
        if paciente.situacao not in (AGUARDANDO, EM_ATENDIMENTO):
            messages.error(
                request, "não é possível cancelar paciente já concluído ou cancelado"
            )
            return redirect("pacientes")
        return render(
            request,
            "atendimento/confirmar_cancelamento.html",
            {
                "tela_ativa": "pacientes",
                "paciente": paciente,
                "item": _atendimento_ativo_de(sistema, paciente.id),
                "SIT_EM_ATENDIMENTO": EM_ATENDIMENTO,
            },
        )

    def cancelar() -> Any:
        antes = sistema.consultar_paciente(paciente_id).situacao
        paciente = sistema.cancelar_paciente(paciente_id)
        return (antes, paciente)

    def mensagem(res: Any) -> str:
        antes, paciente = res
        if antes == EM_ATENDIMENTO:
            return (
                f"Atendimento do paciente #{paciente.id} ({paciente.nome}) cancelado: "
                "ele voltou para a frente da fila, logo atrás das Emergências."
            )
        return f"Cadastro do paciente #{paciente.id} ({paciente.nome}) cancelado."

    _executar(request, cancelar, mensagem)
    return redirect("pacientes")


def triagem(request: HttpRequest) -> HttpResponse:
    sistema = obter_sistema()
    if request.method == "POST":
        pid_raw = request.POST.get("paciente_id", "")
        nova_raw = request.POST.get("nova_prioridade", "")

        def reclassificar() -> Any:
            pid = _ler_inteiro(pid_raw, "ID do paciente")
            nova = _ler_inteiro(nova_raw, "nova prioridade")
            return sistema.reclassificar(pid, nova)

        _executar(
            request,
            reclassificar,
            lambda p: (
                f"Paciente #{p.id} ({p.nome}) reclassificado para prioridade "
                f"{p.prioridade} ({p.descricao_prioridade})."
            ),
        )
        return redirect("triagem")

    return render(
        request,
        "atendimento/triagem.html",
        {
            "tela_ativa": "triagem",
            "fila_prioridade": sistema.listar_fila_prioridade(),
            "fila_chegada": sistema.listar_fila_chegada(),
            "proximo": sistema.proximo_paciente(),
            "opcoes_prioridade": OPCOES_PRIORIDADE,
        },
    )


def medicos(request: HttpRequest) -> HttpResponse:
    sistema = obter_sistema()
    if request.method == "POST":
        nome = request.POST.get("nome", "")
        registro = request.POST.get("registro", "")

        _executar(
            request,
            lambda: sistema.cadastrar_medico(nome, registro),
            lambda m: f"Médico #{m.id} ({m.nome} · {m.registro}) cadastrado como {m.situacao}.",
        )
        return redirect(_destino_seguro(request, "medicos"))

    medico_buscado = None
    buscar_id = (request.GET.get("buscar_id") or "").strip()
    if buscar_id:

        def consultar() -> Any:
            mid = _ler_inteiro(buscar_id, "ID do médico")
            return sistema.consultar_medico(mid)

        medico_buscado = _executar(request, consultar)

    return render(
        request,
        "atendimento/medicos.html",
        {
            "tela_ativa": "medicos",
            "medicos": sistema.listar_medicos(),
            "medico_buscado": medico_buscado,
            "buscar_id": buscar_id,
        },
    )


def atendimentos(request: HttpRequest) -> HttpResponse:
    sistema = obter_sistema()
    ativos = _enriquecer_atendimentos(sistema, sistema.listar_atendimentos_ativos())
    return render(
        request,
        "atendimento/atendimentos.html",
        {
            "tela_ativa": "atendimentos",
            "atendimentos_ativos": ativos,
        },
    )


def concluir_atendimento(request: HttpRequest, atendimento_id: int) -> HttpResponse:
    if request.method == "POST":
        sistema = obter_sistema()
        _executar(
            request,
            lambda: sistema.concluir_atendimento(atendimento_id),
            lambda a: f"Atendimento #{a.id} concluído com sucesso.",
        )
    return redirect("atendimentos")


def cancelar_atendimento(request: HttpRequest, atendimento_id: int) -> HttpResponse:
    if request.method == "POST":
        sistema = obter_sistema()
        _executar(
            request,
            lambda: sistema.cancelar_atendimento(atendimento_id),
            lambda a: (
                f"Atendimento #{a.id} cancelado: o paciente voltou para a frente da fila, "
                "logo atrás das Emergências, e o médico retornou a Disponível sem incremento no contador."
            ),
        )
    return redirect("atendimentos")


def historico(request: HttpRequest) -> HttpResponse:
    sistema = obter_sistema()
    indicadores = sistema.indicadores()
    chegadas = sistema.listar_historico_chegadas()
    encerrados = _enriquecer_atendimentos(sistema, sistema.historico_atendimentos())
    pacientes_cancelados = [
        p for p in sistema.listar_pacientes() if p.situacao == CANCELADO
    ]
    return render(
        request,
        "atendimento/historico.html",
        {
            "tela_ativa": "historico",
            "indicadores": indicadores,
            "chegadas": chegadas,
            "encerrados": encerrados,
            "pacientes_cancelados": pacientes_cancelados,
        },
    )


def diagnostico(request: HttpRequest) -> HttpResponse:
    sistema = obter_sistema()
    diag = sistema.diagnostico()
    medicos_disponiveis_ordem = sorted(
        (m for m in sistema.listar_medicos() if m.situacao == "Disponível"),
        key=lambda m: m.chave_heap(),
    )
    return render(
        request,
        "atendimento/diagnostico.html",
        {
            "tela_ativa": "diagnostico",
            "diag": diag,
            "rb_espera_lista": sistema.listar_fila_chegada(),
            "rb_historico_lista": sistema.listar_historico_chegadas(),
            "heap_pacientes_lista": sistema.listar_fila_prioridade(),
            "heap_medicos_lista": medicos_disponiveis_ordem,
        },
    )
