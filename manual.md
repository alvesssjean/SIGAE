# Manual do SIGAE WEB

> Rascunho. Confirmar cada passo na interface pronta antes da entrega.

## Telas
| Tela | O que fazer |
|---|---|
| Painel geral | ver totais, próximo paciente e médicos; chamar próximo |
| Pacientes | cadastrar, buscar por ID, listar, cancelar |
| Triagem/Fila | ver filas por prioridade e chegada; reclassificar; chamar |
| Médicos | cadastrar, listar, consultar |
| Atendimentos | concluir ou cancelar atendimentos em andamento |
| Histórico | indicadores, chegadas e atendimentos encerrados |

## Cenários (partir sempre de dados limpos)
1. **Distribuição equilibrada:** cadastrar médicos A, B e C e três pacientes; chamar três vezes. Esperado: A, B, C.
2. **Menor carga:** concluir os atendimentos de A e B, cancelar o de C, chamar. Esperado: C.
3. **Prioridade:** cadastrar prioridades 5, 1 e 3; chamar. Esperado: 1, 3, 5.
4. **Sem médico:** chamar sem médico disponível. Esperado: mensagem e fila inalterada.
5. **Reclassificação:** alterar um paciente para Emergência. Esperado: sobe na fila sem duplicar.
6. **Cancelamento:** cancelar um atendimento. Esperado: paciente atrás das Emergências; médico livre com o mesmo contador.
7. **Segundo cancelamento pelo mesmo médico:** Esperado: recusado.
