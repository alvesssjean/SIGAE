"""Renderização SVG server-side das estruturas reais do núcleo para a interface web.

Não importa rbtree, heap, hash_table nem models: lê apenas os atributos dos nós
retornados por sistema.visao_estruturas().
"""

from html import escape
from typing import Any, Optional

from django.utils.safestring import SafeString, mark_safe


def _encurtar(texto: str, limite: int = 13) -> str:
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1] + "…"


def _cor_prioridade(prioridade: int) -> tuple[str, str]:
    if prioridade == 1:
        return ("#dc3545", "#fecaca")
    if prioridade == 2:
        return ("#ea580c", "#fed7aa")
    if prioridade == 3:
        return ("#ca8a04", "#fef08a")
    if prioridade == 4:
        return ("#16a34a", "#bbf7d0")
    return ("#2563eb", "#bfdbfe")


def gerar_svg_rb(raiz: Any) -> Optional[SafeString]:
    """Gera um SVG limpo da Árvore Rubro-Negra real (nós vermelhos e negros)."""
    if raiz is None:
        return None

    nos: list[dict[str, Any]] = []
    posicoes: dict[int, tuple[float, float]] = {}
    arestas: list[tuple[int, int, str]] = []
    contador = 0
    profundidade_max = 0

    dx = 92
    dy = 92
    pad_x = 56
    pad_y = 52

    def percorrer(no: Any, prof: int) -> None:
        nonlocal contador, profundidade_max
        if no is None:
            return
        if prof > profundidade_max:
            profundidade_max = prof
        percorrer(no.esq, prof + 1)
        x = pad_x + contador * dx
        y = pad_y + prof * dy
        contador += 1
        chave_obj = id(no)
        posicoes[chave_obj] = (x, y)
        nos.append({"id_obj": chave_obj, "no": no, "x": x, "y": y, "prof": prof})
        if no.esq is not None:
            arestas.append((chave_obj, id(no.esq), "E"))
        if no.dir is not None:
            arestas.append((chave_obj, id(no.dir), "D"))
        percorrer(no.dir, prof + 1)

    percorrer(raiz, 0)

    largura = max(360, pad_x * 2 + max(contador - 1, 0) * dx)
    altura = max(170, pad_y * 2 + profundidade_max * dy + 34)

    partes: list[str] = [
        f'<svg viewBox="0 0 {largura} {altura}" width="{largura}" height="{altura}" '
        f'class="sigae-svg-arvore" role="img" aria-label="Árvore Rubro-Negra">'
    ]

    for pai_id, filho_id, lado in arestas:
        x1, y1 = posicoes[pai_id]
        x2, y2 = posicoes[filho_id]
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2 - 4
        partes.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#94a3b8" stroke-width="2" />'
        )
        partes.append(
            f'<text x="{mx}" y="{my}" text-anchor="middle" '
            f'font-size="10" fill="#64748b" font-weight="600">{lado}</text>'
        )

    for info in nos:
        no = info["no"]
        x = info["x"]
        y = info["y"]
        eh_vermelho = no.cor == "V"
        fill = "#dc3545" if eh_vermelho else "#1e293b"
        stroke = "#fca5a5" if eh_vermelho else "#cbd5e1"
        paciente = no.valor
        hora = str(no.chave[0])
        hora_curta = hora[11:] if len(hora) >= 19 else hora
        pid = no.chave[1]
        nome = escape(_encurtar(getattr(paciente, "nome", f"#{pid}")))
        prio = getattr(paciente, "prioridade", None)
        situacao = escape(str(getattr(paciente, "situacao", "")))
        cor_txt = "Vermelho" if eh_vermelho else "Negro"
        dica = escape(
            f"ID #{pid} · {getattr(paciente, 'nome', '')} · Chegada: {hora} · Cor: {cor_txt}"
            + (f" · P{prio} · {situacao}" if prio is not None else "")
        )

        partes.append("<g>")
        partes.append(f"<title>{dica}</title>")
        if info["prof"] == 0:
            partes.append(
                f'<circle cx="{x}" cy="{y}" r="31" fill="none" '
                f'stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="4 3" />'
            )
            partes.append(
                f'<text x="{x}" y="{y - 36}" text-anchor="middle" '
                f'font-size="10" font-weight="700" fill="#b45309">RAIZ</text>'
            )
        partes.append(
            f'<circle cx="{x}" cy="{y}" r="25" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="2.5" />'
        )
        partes.append(
            f'<text x="{x}" y="{y - 2}" text-anchor="middle" '
            f'font-size="12" font-weight="700" fill="#ffffff">#{pid}</text>'
        )
        sub_centro = f"P{prio}" if prio is not None else no.cor
        partes.append(
            f'<text x="{x}" y="{y + 13}" text-anchor="middle" '
            f'font-size="10" font-weight="600" fill="#f8fafc">{sub_centro}</text>'
        )
        partes.append(
            f'<text x="{x}" y="{y + 40}" text-anchor="middle" '
            f'font-size="11" font-weight="600" fill="#1e293b">{nome}</text>'
        )
        partes.append(
            f'<text x="{x}" y="{y + 53}" text-anchor="middle" '
            f'font-size="10" fill="#64748b">{escape(hora_curta)}</text>'
        )
        partes.append("</g>")

    partes.append("</svg>")
    return mark_safe("".join(partes))


def gerar_svg_heap(no_raiz: Any, tipo: str = "paciente") -> Optional[SafeString]:
    """Gera um SVG da árvore binária completa ligada do Min-Heap (com posição k em bits)."""
    if no_raiz is None:
        return None

    nos: list[dict[str, Any]] = []
    posicoes: dict[int, tuple[float, float]] = {}
    arestas: list[tuple[int, int, str]] = []
    contador = 0
    profundidade_max = 0

    dx = 98
    dy = 96
    pad_x = 60
    pad_y = 54

    def percorrer(no: Any, prof: int, k: int) -> None:
        nonlocal contador, profundidade_max
        if no is None:
            return
        if prof > profundidade_max:
            profundidade_max = prof
        percorrer(no.esq, prof + 1, k * 2)
        x = pad_x + contador * dx
        y = pad_y + prof * dy
        contador += 1
        chave_obj = id(no)
        posicoes[chave_obj] = (x, y)
        nos.append({"id_obj": chave_obj, "no": no, "x": x, "y": y, "prof": prof, "k": k})
        if no.esq is not None:
            arestas.append((chave_obj, id(no.esq), "0"))
        if no.dir is not None:
            arestas.append((chave_obj, id(no.dir), "1"))
        percorrer(no.dir, prof + 1, k * 2 + 1)

    percorrer(no_raiz, 0, 1)

    largura = max(360, pad_x * 2 + max(contador - 1, 0) * dx)
    altura = max(175, pad_y * 2 + profundidade_max * dy + 38)

    partes: list[str] = [
        f'<svg viewBox="0 0 {largura} {altura}" width="{largura}" height="{altura}" '
        f'class="sigae-svg-arvore" role="img" aria-label="Min-Heap ({tipo})">'
    ]

    for pai_id, filho_id, bit in arestas:
        x1, y1 = posicoes[pai_id]
        x2, y2 = posicoes[filho_id]
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2 - 4
        partes.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#94a3b8" stroke-width="2" />'
        )
        partes.append(
            f'<text x="{mx}" y="{my}" text-anchor="middle" '
            f'font-size="10" fill="#64748b" font-weight="700">bit {bit}</text>'
        )

    for info in nos:
        item = info["no"].item
        x = info["x"]
        y = info["y"]
        k = info["k"]
        bits = format(k, "b")

        if tipo == "paciente":
            fill, stroke = _cor_prioridade(item.prioridade)
            if item.retorno and item.prioridade > 1:
                fill, stroke = ("#7c3aed", "#ddd6fe")
            linha1 = f"#{item.id} · P{item.prioridade}"
            linha2 = "RETORNO" if item.retorno else f"k={k} ({bits})"
            sub1 = escape(_encurtar(item.nome))
            sub2 = escape(f"chave={item.chave_heap()[0]},P{item.prioridade} · k={k}")
            dica = escape(
                f"Paciente #{item.id} · {item.nome} · Prioridade {item.prioridade} "
                f"· Retorno={item.retorno} · Posição k={k} (bin {bits}) · Chave={item.chave_heap()}"
            )
        else:
            fill, stroke = ("#0f766e", "#99f6e4")
            linha1 = f"#{item.id}"
            linha2 = f"{item.concluidos} conc."
            sub1 = escape(_encurtar(item.nome))
            sub2 = escape(f"seq={item.seq_ultima_atribuicao} · k={k} ({bits})")
            dica = escape(
                f"Médico #{item.id} · {item.nome} ({item.registro}) · Concluídos={item.concluidos} "
                f"· Seq={item.seq_ultima_atribuicao} · Posição k={k} (bin {bits})"
            )

        partes.append("<g>")
        partes.append(f"<title>{dica}</title>")
        if k == 1:
            partes.append(
                f'<circle cx="{x}" cy="{y}" r="33" fill="none" '
                f'stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="4 3" />'
            )
            partes.append(
                f'<text x="{x}" y="{y - 38}" text-anchor="middle" '
                f'font-size="10" font-weight="700" fill="#b45309">RAIZ (MÍNIMO)</text>'
            )
        partes.append(
            f'<circle cx="{x}" cy="{y}" r="27" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="2.5" />'
        )
        partes.append(
            f'<text x="{x}" y="{y - 2}" text-anchor="middle" '
            f'font-size="11.5" font-weight="700" fill="#ffffff">{escape(linha1)}</text>'
        )
        partes.append(
            f'<text x="{x}" y="{y + 13}" text-anchor="middle" '
            f'font-size="9.5" font-weight="600" fill="#f8fafc">{escape(linha2)}</text>'
        )
        partes.append(
            f'<text x="{x}" y="{y + 42}" text-anchor="middle" '
            f'font-size="11" font-weight="600" fill="#1e293b">{sub1}</text>'
        )
        partes.append(
            f'<text x="{x}" y="{y + 55}" text-anchor="middle" '
            f'font-size="9.5" fill="#64748b">{sub2}</text>'
        )
        partes.append("</g>")

    partes.append("</svg>")
    return mark_safe("".join(partes))


def preparar_buckets_hash(buckets_detalhados: Any, tipo: str) -> list[dict[str, Any]]:
    """Prepara os buckets da Tabela Hash para exibição visual em cadeias encadeadas."""
    resultado: list[dict[str, Any]] = []
    for indice, cadeia in buckets_detalhados:
        itens: list[dict[str, Any]] = []
        for chave_id, valor in cadeia:
            if tipo == "paciente":
                rotulo = f"#{chave_id} · {_encurtar(valor.nome, 16)}"
                detalhe = f"P{valor.prioridade} · {valor.situacao}"
            elif tipo == "medico":
                rotulo = f"#{chave_id} · {_encurtar(valor.nome, 16)}"
                detalhe = f"{valor.situacao} ({valor.concluidos} conc.)"
            else:
                rotulo = f"Atend #{chave_id}"
                detalhe = f"Pac #{valor.paciente_id} → Méd #{valor.medico_id} · {valor.status}"
            itens.append({"id": chave_id, "rotulo": rotulo, "detalhe": detalhe})
        resultado.append(
            {
                "indice": indice,
                "itens": itens,
                "tamanho": len(itens),
                "colisao": len(itens) > 1,
            }
        )
    return resultado
