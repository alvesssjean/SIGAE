# ADR-003: Rollback por pilha de compensações

**Status:** Proposto (mudar para Aceito após aprovação do grupo)

## Contexto
Cada operação altera várias estruturas e o banco; uma falha no meio não pode deixar registros órfãos.

## Decisão
Validar sem efeitos, aplicar, gravar e compensar em caso de falha:

    validar(entrada)                      # nenhum efeito
    desfazer = ListaEncadeada()           # usada como pilha
    try:
        para cada passo:
            aplicar(passo)
            desfazer.inserir_inicio(inverso(passo))
        com repositorio.transacao():
            gravar()
    se falhar:
        enquanto desfazer: desfazer.remover_inicio()()
        relançar

## Alternativas consideradas
Copiar todas as estruturas antes de cada operação: custo O(n) por operação.

## Consequências
Todo passo novo precisa de uma compensação, coberta por tests/integracao/test_rollback.py.
