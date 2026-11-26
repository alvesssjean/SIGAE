# ADR-010: Núcleo sem list, dict, set ou heapq

**Status:** Aceito (24/11/2026)

## Contexto
O enunciado proíbe estruturas prontas no lugar das exigidas; o grupo estendeu a proibição a `list`.

## Decisão
Em `core/`: sem `list`, `dict`, `set`, `frozenset`, `heapq`, `sorted`. Usar `ListaEncadeada` própria e, nos buckets, tupla imutável de sentinelas. A camada Django usa os tipos que a API exige.

## Alternativas consideradas
Vetor `ctypes` (reserva). Árvore de buckets: perde o acesso O(1).

## Consequências
Garantido por `tests/unit/test_sem_estruturas_prontas.py`.
