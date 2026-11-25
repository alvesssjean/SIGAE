# ADR-012: Cancelamento de atendimento

**Status:** Proposto (mudar para Aceito após aprovação do grupo)

## Contexto
O enunciado cita cancelar o atendimento, mas não define o destino do paciente.

## Decisão
O paciente volta à fila logo atrás das Emergências, com a chave `(classe, prioridade, horario, id)`: classe 0 Emergência, 1 devolvido, 2 demais. Cada médico cancela o mesmo paciente no máximo uma vez, sem bloqueio de nova atribuição. O médico volta a Disponível sem somar atendimento.

Exemplo: com E (Emergência), M (Muito urgente), D (devolvido, Pouco urgente) e U (Urgente), a ordem é E, D, M, U.

## Alternativas consideradas
Bloquear o médico que cancelou; colocar o devolvido no topo absoluto. Ambas descartadas.

## Consequências
O devolvido passa à frente das prioridades 2 a 5 porque já tinha sido chamado. Emergências nunca são ultrapassadas. Aberto (P14): um devolvido Emergência segue a ordem normal entre Emergências.
