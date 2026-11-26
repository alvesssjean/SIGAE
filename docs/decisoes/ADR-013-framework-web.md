# ADR-003 · Framework da interface web

**Status:** Aceito
**Data:** 26/11/2026
**Decisores:** Equipe SIGAE (4 integrantes) · Professor (cliente)

## Contexto

A seção 9.2 do documento base previa Flask ou FastAPI para a interface HTML,
como complemento opcional ao terminal. Posteriormente, o professor alterou a
exigência: a interface visual passou a ser obrigatória.

## Decisão

A interface web será desenvolvida com **Django**, em `web/`, consumindo
exclusivamente `core/sistema.py` (`SistemaSigae`). A interface nunca acessa
`rbtree`, `heap` ou `hash_table` diretamente.

## Consequências

- A seção 9.2 do documento base passa a prever Django como dependência
  permitida (além de `pytest`), sem banco de dados e sem autenticação.
- A interface visual deixa de ser complemento e passa a ser entrega obrigatória.
  O terminal (`cli/menu.py`) continua obrigatório e tem prioridade de
  concorrência de tempo.
- O cronograma é revisto: a interface web entra na Iteração 3, com entrega
  até 27/11. Se o prazo apertar, o escopo da interface é reduzido para as sete
  operações mínimas (cadastrar, consultar, reclassificar, atender, listar,
  cancelar, validar), sem refinamentos visuais.
- Os testes de aceitação A, B e C não mudam.

## Alternativas consideradas

- **Flask/FastAPI:** descartado após a mudança de exigência, por exigir mais
  código manual de template e formulário para a mesma entrega.
