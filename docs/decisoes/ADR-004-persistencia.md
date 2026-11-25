# ADR-004: Porta Repositorio e SQLite apenas como persistência

**Status:** Proposto (mudar para Aceito após aprovação do grupo)

## Contexto
O estado deve sobreviver ao reinício sem que o banco substitua as estruturas exigidas.

## Decisão
O core usa a porta `Repositorio` (`RepositorioMemoria` ou `RepositorioDjango` com `transaction.atomic`). O estado é rehidratado na inicialização, por carga completa e sem ordenação. Execução em processo único: `runserver --noreload --nothreading`.

## Alternativas consideradas
Consultar o banco para ordenar ou buscar: proibido, pois substituiria as estruturas.

## Consequências
Se a persistência não ficar pronta, o sistema entrega com `RepositorioMemoria` e isso é registrado como limitação.
