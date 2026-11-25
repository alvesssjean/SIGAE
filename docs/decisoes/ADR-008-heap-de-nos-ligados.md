# ADR-008: Heap como árvore completa de nós ligados

**Status:** Proposto (mudar para Aceito após aprovação do grupo)

## Contexto
`list` é proibida no núcleo e é preciso reposicionar ou remover por ID.

## Decisão
Árvore binária completa com nós `item, pai, esq, dir`; a posição k é achada pelos bits de k; o mapa id→nó usa a HashTable do projeto.

## Alternativas consideradas
Vetor em `list`: proibido pela decisão do ADR-010.

## Consequências
Inserir, extrair, alterar e remover em O(log n), com o mapa O(1) em média.
