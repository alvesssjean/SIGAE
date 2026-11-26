"""T47 / H27: garante que core/ não usa coleções prontas (ADR-010)."""

import ast
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parents[2] / "core"
NOS_PROIBIDOS = (ast.List, ast.ListComp, ast.Dict, ast.DictComp, ast.Set, ast.SetComp)
NOMES_PROIBIDOS = {"list", "dict", "set", "frozenset", "sorted"}

# Remover a entrada quando a task correspondente for mesclada.
PENDENTES: dict[str, str] = {}


def violacoes(caminho: Path) -> list:
    arvore = ast.parse(caminho.read_text(encoding="utf-8-sig"), filename=str(caminho))
    achados = []
    for no in ast.walk(arvore):
        motivo = None
        if isinstance(no, NOS_PROIBIDOS):
            motivo = type(no).__name__
        elif isinstance(no, ast.Name) and no.id in NOMES_PROIBIDOS:
            motivo = f"nome '{no.id}'"
        elif isinstance(no, ast.arguments) and no.kwarg is not None:
            motivo = "**kwargs"
        elif isinstance(no, ast.Attribute) and no.attr == "split":
            motivo = ".split"
        elif isinstance(no, ast.Import):
            if any(a.name == "heapq" for a in no.names):
                motivo = "import heapq"
        elif isinstance(no, ast.ImportFrom) and no.module == "heapq":
            motivo = "import heapq"
        if motivo:
            linha = getattr(no, "lineno", "?")
            achados.append(f"{caminho.name}:{linha}: {motivo}")
    return achados


def arquivos():
    for caminho in sorted(CORE.glob("*.py")):
        marcas = ()
        if caminho.name in PENDENTES:
            marcas = (pytest.mark.xfail(reason=PENDENTES[caminho.name]),)
        yield pytest.param(caminho, id=caminho.name, marks=marcas)


@pytest.mark.parametrize("caminho", list(arquivos()))
def test_sem_estruturas_prontas(caminho):
    assert violacoes(caminho) == []
