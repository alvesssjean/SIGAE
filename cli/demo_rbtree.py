import os
import re
import sys
from typing import Callable, Optional

from core.rbtree import RBInvalidaError, RBTree

DATA_DEMO = "2026-11-26"
PADRAO_HORARIO = re.compile(r"^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$")

MENU = """
=== Demonstração da Árvore Rubro-Negra ===
1) Inserir paciente
2) Remover paciente
3) Buscar paciente
4) Mostrar árvore
5) Listar por ordem de chegada
6) Validar propriedades
7) Carregar exemplo
8) Limpar árvore
0) Sair
"""

EXEMPLO = (
    ("08:00:00", 1, "Ana"),
    ("08:05:00", 2, "Bruno"),
    ("08:10:00", 3, "Carla"),
    ("08:15:00", 4, "Diego"),
    ("08:20:00", 5, "Elisa"),
    ("08:25:00", 6, "Fabio"),
    ("08:30:00", 7, "Gabi"),
)


def ativar_cores() -> bool:
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        return False
    os.system("")
    return True


def ler_chave(entrada: Callable[[str], str], saida: Callable[[str], None]):
    texto = entrada(f"Horário em {DATA_DEMO} (HH:MM ou HH:MM:SS): ").strip()
    if not PADRAO_HORARIO.match(texto):
        saida("Horário inválido. Use HH:MM ou HH:MM:SS com zero à esquerda.")
        return None
    if len(texto) == 5:
        texto += ":00"
    texto_id = entrada("ID do paciente: ").strip()
    if not (texto_id.isascii() and texto_id.isdigit()):
        saida("ID inválido. Use um número inteiro.")
        return None
    return (f"{DATA_DEMO} {texto}", int(texto_id))


def mostrar_passos(arvore: RBTree, saida: Callable[[str], None]) -> None:
    if arvore.eventos:
        for evento in arvore.eventos:
            saida(f"  - {evento}")
    else:
        saida("  (nenhum)")


def mostrar_resultado(
    arvore: RBTree, antes: str, cores: bool, saida: Callable[[str], None]
) -> None:
    saida("\nAntes:")
    saida(antes)
    saida("\nPassos (recoloração e rotações):")
    mostrar_passos(arvore, saida)
    saida("\nDepois:")
    saida(arvore.desenhar(cores))
    try:
        arvore.validar()
        saida("\nPropriedades rubro-negras: OK")
    except RBInvalidaError as erro:
        saida(f"\nPropriedades violadas: {erro}")


def carregar_exemplo(cores: bool, saida: Callable[[str], None]) -> RBTree:
    arvore = RBTree(rastrear=True)
    for horario, id_paciente, nome in EXEMPLO:
        arvore.inserir((f"{DATA_DEMO} {horario}", id_paciente), nome)
        saida(f"\nInserindo {horario} (ID {id_paciente}, {nome}):")
        mostrar_passos(arvore, saida)
    saida("\nÁrvore final:")
    saida(arvore.desenhar(cores))
    return arvore


def listar(arvore: RBTree, saida: Callable[[str], None]) -> None:
    posicao = 0
    for chave, valor in arvore.em_ordem():
        posicao += 1
        extra = f" - {valor}" if valor else ""
        saida(f"{posicao}. {chave[0]} (ID {chave[1]}){extra}")
    if posicao == 0:
        saida("(nenhum paciente)")


def main(
    entrada: Callable[[str], str] = input,
    saida: Callable[[str], None] = print,
    cores: Optional[bool] = None,
) -> None:
    if cores is None:
        cores = ativar_cores()
    arvore = RBTree(rastrear=True)
    while True:
        saida(MENU)
        try:
            opcao = entrada("Opção: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if opcao == "0":
            break
        if opcao == "1":
            chave = ler_chave(entrada, saida)
            if chave is None:
                continue
            nome = entrada("Nome (opcional): ").strip() or None
            antes = arvore.desenhar(cores)
            try:
                arvore.inserir(chave, nome)
            except ValueError as erro:
                saida(f"Não inserido: {erro}")
                continue
            mostrar_resultado(arvore, antes, cores, saida)
        elif opcao == "2":
            chave = ler_chave(entrada, saida)
            if chave is None:
                continue
            antes = arvore.desenhar(cores)
            if arvore.remover(chave):
                mostrar_resultado(arvore, antes, cores, saida)
            else:
                saida("Chave não encontrada.")
        elif opcao == "3":
            chave = ler_chave(entrada, saida)
            if chave is None:
                continue
            if chave in arvore:
                saida(f"Encontrado. Valor: {arvore.buscar(chave)!r}")
            else:
                saida("Chave não encontrada.")
        elif opcao == "4":
            saida(arvore.desenhar(cores))
        elif opcao == "5":
            listar(arvore, saida)
        elif opcao == "6":
            try:
                arvore.validar()
                saida("Propriedades rubro-negras: OK")
            except RBInvalidaError as erro:
                saida(f"Propriedades violadas: {erro}")
        elif opcao == "7":
            arvore = carregar_exemplo(cores, saida)
        elif opcao == "8":
            arvore = RBTree(rastrear=True)
            saida("Árvore limpa.")
        else:
            saida("Opção inválida.")


if __name__ == "__main__":
    main()
