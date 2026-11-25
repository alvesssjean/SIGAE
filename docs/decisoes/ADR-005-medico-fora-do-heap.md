# ADR-005: Médico ocupado fica fora do Heap

**Status:** Proposto (mudar para Aceito após aprovação do grupo)

## Contexto
Um médico Em atendimento não pode ser escolhido.

## Decisão
Ele sai do Heap de médicos na chamada e é reinserido ao concluir ou cancelar o atendimento.

## Alternativas consideradas
Mantê-lo no Heap e pular os ocupados: a raiz deixaria de ser sempre elegível.

## Consequências
A raiz é sempre o médico a escolher; heap vazio significa ausência de médico disponível.
