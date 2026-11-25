# ADR-002: Fator de carga e redimensionamento

**Status:** Proposto (mudar para Aceito após aprovação do grupo)

## Contexto
Cadeias longas degradam a busca; o enunciado exige redimensionamento.

## Decisão
Ao ultrapassar fator de carga 0,75, a capacidade passa ao próximo primo >= 2 x a atual (7, 17, 37). Os nós existentes são religados.

## Alternativas consideradas
Dobrar sem usar primo: tende a concentrar chaves em poucos buckets.

## Consequências
Redimensionar custa O(n), amortizado O(1) por inserção.
