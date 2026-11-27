"""Validação e padronização de nomes e do registro CRM (core/validacao.py)."""

import pytest

from core.erros import ErroValidacao
from core.validacao import (
    UF_PADRAO,
    formatar_crm,
    ler_numero_crm,
    normalizar_nome,
    normalizar_uf,
)


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("Ana", "Ana"),
        ("maria DA silva", "Maria da Silva"),
        ("  JOÃO   dos   santos  ", "João dos Santos"),
        ("ana-clara d'ávila", "Ana-Clara D'Ávila"),
        ("Pedro e Paulo", "Pedro e Paulo"),
        ("Joana d’Arc", "Joana D'Arc"),
        ("Li", "Li"),
        ("Conceição Aparecida", "Conceição Aparecida"),
    ],
)
def test_nome_valido_e_padronizado(entrada, esperado):
    assert normalizar_nome(entrada, "paciente") == esperado


@pytest.mark.parametrize(
    "entrada, trecho",
    [
        ("", "obrigatório"),
        ("   ", "obrigatório"),
        (None, "obrigatório"),
        ("A", "pelo menos 2 letras"),
        ("Paciente 1", "números"),
        ("Ana2", "números"),
        ("Dra. Ana", "caracteres especiais"),
        ("Ana@Silva", "caracteres especiais"),
        ("Ana_Silva", "caracteres especiais"),
        ("João P Silva", "letras soltas"),
        ("E Silva", "letras soltas"),
        ("Maria e", "letras soltas"),
        ("-Ana", "entre letras"),
        ("Ana-", "entre letras"),
        ("Ana--Clara", "entre letras"),
        ("D'-Ávila", "entre letras"),
        ("Annna", "repetida"),
        ("Aaa", "repetida"),
        ("Ana " + "Silva " * 20, "no máximo"),
    ],
)
def test_nome_invalido(entrada, trecho):
    with pytest.raises(ErroValidacao, match=trecho):
        normalizar_nome(entrada, "médico")


def test_mensagem_cita_o_tipo_de_cadastro():
    with pytest.raises(ErroValidacao, match="nome do médico"):
        normalizar_nome("X1", "médico")


@pytest.mark.parametrize(
    "entrada, esperado",
    [("123", 123), (" 004567 ", 4567), ("999999", 999999), ("", None), ("  ", None), (None, None)],
)
def test_numero_crm_valido(entrada, esperado):
    assert ler_numero_crm(entrada) == esperado


@pytest.mark.parametrize(
    "entrada, trecho",
    [
        ("12.345", "apenas números"),
        ("12-345", "apenas números"),
        ("CRM123", "apenas números"),
        ("12 345", "apenas números"),
        ("１２３", "apenas números"),
        ("1234567", "no máximo 6"),
        ("000", "zero"),
    ],
)
def test_numero_crm_invalido(entrada, trecho):
    with pytest.raises(ErroValidacao, match=trecho):
        ler_numero_crm(entrada)


def test_uf():
    assert normalizar_uf("sp") == "SP"
    assert normalizar_uf(" mg ") == "MG"
    assert normalizar_uf("") == UF_PADRAO
    assert normalizar_uf(None) == UF_PADRAO
    with pytest.raises(ErroValidacao, match="UF"):
        normalizar_uf("XX")
    with pytest.raises(ErroValidacao, match="UF"):
        normalizar_uf("R/")


def test_mascara_crm():
    assert formatar_crm("RJ", 123) == "CRM/RJ 000123"
    assert formatar_crm("SP", 999999) == "CRM/SP 999999"
