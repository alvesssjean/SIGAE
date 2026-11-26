# ADR-006: Desempate de médicos por relógio lógico

**Status:** Aceito (24/11/2026)

## Contexto
Empate de concluídos favorece quem está há mais tempo sem receber paciente (enunciado §4).

## Decisão
Chave `(concluidos, seq_ultima_atribuicao, id)`. O contador incrementa a cada chamada; nunca atribuído vale 0; não volta atrás no cancelamento; é persistido.

## Alternativas consideradas
Relógio de parede: empates e testes não reproduzíveis. Contar a partir da conclusão: descartado pelo grupo.

## Consequências
Distribuição determinística e testável.
