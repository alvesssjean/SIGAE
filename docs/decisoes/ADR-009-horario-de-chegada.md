# ADR-009: Horário de chegada automático

**Status:** Proposto (mudar para Aceito após aprovação do grupo)

## Contexto
A ordem cronológica precisa valer entre dias, com persistência.

## Decisão
Horário local (`America/Sao_Paulo`) em texto `AAAA-MM-DD HH:MM:SS`; relógio injetável para testes.

## Alternativas consideradas
`HH:MM`: quebra a ordem entre dias. Horário digitado: sujeito a erro.

## Consequências
A ordem lexicográfica é a cronológica; empates no mesmo segundo são resolvidos pelo ID.
