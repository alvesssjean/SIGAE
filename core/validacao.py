"""Validação e padronização dos dados de cadastro: nomes e registro CRM.

Sem coleções prontas (ADR-010): os nomes são percorridos caractere a caractere
e as partes ficam numa ListaEncadeada.
"""

from __future__ import annotations

from typing import Optional

from core.erros import ErroValidacao
from core.lista_encadeada import ListaEncadeada

NOME_TAMANHO_MAXIMO = 100

# Preposições e conjunção que ficam em minúsculas no meio do nome.
PARTICULAS = ("de", "da", "do", "das", "dos", "e")

# Separadores aceitos dentro de uma parte do nome: Ana-Clara, D'Ávila.
HIFEN = "-"
APOSTROFO = "'"
APOSTROFO_TIPOGRAFICO = "’"

UFS = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
    "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
)
UF_PADRAO = "RJ"
CRM_DIGITOS = 6
CRM_NUMERO_MAXIMO = 999999


def _eh_letra(c: str) -> bool:
    """Letra do alfabeto latino, com ou sem acento (exclui ª e º)."""
    return c.isalpha() and ord(c) < 0x250 and c not in "ªº"


def _formatar_parte(parte: str, primeira: bool) -> str:
    minuscula = parte.lower()
    if not primeira and minuscula in PARTICULAS:
        return minuscula
    resultado = ""
    maiuscula_seguinte = True
    for c in minuscula:
        if maiuscula_seguinte and _eh_letra(c):
            resultado += c.upper()
            maiuscula_seguinte = False
        else:
            resultado += c
        if c == HIFEN or c == APOSTROFO:
            maiuscula_seguinte = True
    return resultado


def _validar_parte(parte: str, rotulo: str) -> None:
    if not _eh_letra(parte[0]) or not _eh_letra(parte[len(parte) - 1]):
        raise ErroValidacao(
            f"nome do {rotulo}: hífen e apóstrofo só podem aparecer entre letras"
        )
    anterior = ""
    repeticoes = 0
    for c in parte.lower():
        if not _eh_letra(c):
            if not _eh_letra(anterior):
                raise ErroValidacao(
                    f"nome do {rotulo}: hífen e apóstrofo só podem aparecer entre letras"
                )
            repeticoes = 0
        elif c == anterior:
            repeticoes += 1
            if repeticoes >= 2:
                raise ErroValidacao(
                    f"nome do {rotulo} inválido: a mesma letra repetida três vezes seguidas"
                )
        else:
            repeticoes = 0
        anterior = c


def normalizar_nome(nome: object, rotulo: str) -> str:
    """Valida o nome e devolve no padrão de escrita: "maria DA silva" -> "Maria da Silva".

    Regras: só letras (acentuadas ou não), espaços, hífen e apóstrofo entre letras;
    sem números nem caracteres especiais; cada parte com pelo menos 2 letras, exceto
    a conjunção "e" no meio do nome; nenhuma letra repetida três vezes seguidas;
    no máximo NOME_TAMANHO_MAXIMO caracteres. Espaços repetidos viram um só.
    """
    if not isinstance(nome, str) or not nome.strip():
        raise ErroValidacao(f"nome do {rotulo} é obrigatório")

    partes = ListaEncadeada()
    atual = ""
    for c in nome.strip():
        if c.isspace():
            if atual:
                partes.anexar(atual)
                atual = ""
            continue
        if c == APOSTROFO_TIPOGRAFICO:
            c = APOSTROFO
        if c.isdigit():
            raise ErroValidacao(f"nome do {rotulo} não pode conter números")
        if not _eh_letra(c) and c != HIFEN and c != APOSTROFO:
            raise ErroValidacao(f"nome do {rotulo} não pode conter caracteres especiais")
        atual += c
    if atual:
        partes.anexar(atual)

    total = len(partes)
    resultado = ""
    posicao = 0
    for parte in partes:
        _validar_parte(parte, rotulo)
        if len(parte) < 2:
            no_meio = 0 < posicao < total - 1
            if not (no_meio and parte.lower() == "e"):
                if total == 1:
                    raise ErroValidacao(f"nome do {rotulo} deve ter pelo menos 2 letras")
                raise ErroValidacao(
                    f"nome do {rotulo}: abreviações e letras soltas não são aceitas"
                )
        if resultado:
            resultado += " "
        resultado += _formatar_parte(parte, posicao == 0)
        posicao += 1

    if len(resultado) > NOME_TAMANHO_MAXIMO:
        raise ErroValidacao(
            f"nome do {rotulo} deve ter no máximo {NOME_TAMANHO_MAXIMO} caracteres"
        )
    return resultado


def normalizar_uf(uf: object) -> str:
    """Sigla da UF do CRM em maiúsculas; vazio usa UF_PADRAO."""
    if uf is None:
        return UF_PADRAO
    if not isinstance(uf, str):
        raise ErroValidacao("UF do CRM inválida")
    sigla = uf.strip().upper()
    if not sigla:
        return UF_PADRAO
    if sigla not in UFS:
        raise ErroValidacao(f"UF do CRM inválida: {sigla}")
    return sigla


def ler_numero_crm(numero: object) -> Optional[int]:
    """Número do CRM digitado; None quando vazio (o sistema gera um automaticamente)."""
    if numero is None:
        return None
    if not isinstance(numero, str):
        raise ErroValidacao("número do CRM inválido")
    texto = numero.strip()
    if not texto:
        return None
    for c in texto:
        if c < "0" or c > "9":
            raise ErroValidacao(
                "número do CRM aceita apenas números, sem letras nem caracteres especiais"
            )
    if len(texto) > CRM_DIGITOS:
        raise ErroValidacao(f"número do CRM deve ter no máximo {CRM_DIGITOS} dígitos")
    valor = int(texto)
    if valor == 0:
        raise ErroValidacao("número do CRM não pode ser zero")
    return valor


def formatar_crm(uf: str, numero: int) -> str:
    """Máscara do registro: CRM/UF 000000."""
    return f"CRM/{uf} {numero:0{CRM_DIGITOS}d}"
