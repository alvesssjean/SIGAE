"""T36 (parte estática): views só falam com o serviço; ORM não decide regra."""

import ast
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[2] / "web"
VIEWS = WEB / "atendimento" / "views.py"
MODULOS_PROIBIDOS = {"rbtree", "heap", "hash_table", "models"}


@pytest.mark.skipif(not VIEWS.exists(), reason="aguarda T14")
def test_views_nao_importam_estruturas_nem_models():
    achados = []
    for no in ast.walk(ast.parse(VIEWS.read_text(encoding="utf-8"))):
        if isinstance(no, ast.Import):
            nomes = [a.name for a in no.names]
        elif isinstance(no, ast.ImportFrom):
            nomes = [no.module or ""] + [a.name for a in no.names]
        else:
            continue
        for nome in nomes:
            if MODULOS_PROIBIDOS & set(nome.split(".")):
                achados.append(f"linha {no.lineno}: {nome}")
    assert achados == []


@pytest.mark.skipif(not WEB.exists(), reason="aguarda T14")
def test_orm_nao_decide_regra_de_negocio():
    achados = []
    for caminho in WEB.rglob("*.py"):
        if "migrations" in caminho.parts:
            continue
        arvore = ast.parse(caminho.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            if not (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)):
                continue
            alvo = ast.unparse(no.func)
            orm = no.func.attr in ("order_by", "filter") or alvo.endswith(".objects.get")
            if orm:
                achados.append(f"{caminho.name}:{no.lineno}: {alvo}")
    assert achados == []
