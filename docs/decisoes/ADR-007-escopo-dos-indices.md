# ADR-007: Escopo dos índices e mutabilidade do Paciente

**Status:** Aceito (24/11/2026)

## Contexto
Pacientes chamados ou encerrados precisam continuar consultáveis.

## Decisão
A Hash guarda todos; RB espera e Heap só os Aguardando; uma segunda RBTree (histórico) guarda todas as chegadas. Paciente é mutável, mas só `sistema.py` altera prioridade, situação, `retorno` e `medicos_que_cancelaram`.

## Alternativas consideradas
Remover o paciente de tudo ao chamar (documento base): conflita com o enunciado. Paciente imutável: exigiria substituir o objeto em cada índice.

## Consequências
Invariante: IDs da RB espera = IDs do Heap = IDs Aguardando na Hash.
