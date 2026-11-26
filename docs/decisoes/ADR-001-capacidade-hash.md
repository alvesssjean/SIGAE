# ADR-001: Capacidade e função de dispersão da Hash

**Status:** Aceito (24/11/2026)

## Contexto
Pacientes precisam de consulta rápida por ID, com Hash implementada pela equipe (enunciado §2).

## Decisão
Capacidade inicial 7, `h(id) = id % capacidade`, encadeamento separado com nós próprios.

## Alternativas consideradas
Endereçamento aberto: remoção exige marcadores e dificulta a demonstração das colisões.

## Consequências
Busca O(1) em média e O(n) no pior caso. IDs 101 e 108 colidem com capacidade 7, o que permite demonstrar a colisão.
