# ADR-011: Django 5.2 e testes sem pytest-django

**Status:** Aceito (24/11/2026)

## Contexto
A entrega é uma aplicação web e as máquinas têm versões diferentes de Python.

## Decisão
`Django>=5.2,<6`, sem DRF; pytest com `conftest.py` próprio.

## Alternativas consideradas
Flask ou FastAPI (documento base); Django 6 (exige Python 3.12).

## Consequências
Fixtures de banco são mantidas pela equipe.
