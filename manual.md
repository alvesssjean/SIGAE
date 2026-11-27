# Manual de Uso — SIGAE WEB

Guia prático de operação das telas da interface web e reprodução dos cenários de defesa. Todos os dados são fictícios.

## Preparação

Para iniciar com o banco limpo antes de reproduzir qualquer cenário:

```bash
python manage.py resetar_demo
python manage.py runserver --noreload --nothreading
```

Para carregar dados fictícios de demonstração (3 médicos A/B/C e 8 pacientes de prioridades 1 a 5):

```bash
python manage.py resetar_demo
python manage.py popular_demo
python manage.py runserver --noreload --nothreading
```

## Telas disponíveis

| Tela | Rota | Funcionalidades |
|---|---|---|
| **Painel geral** | `/` | Totais de pacientes por situação, contagem de médicos livres/ocupados, próximo paciente da fila, lista de médicos, atendimentos em andamento e botão **Chamar próximo**. |
| **Pacientes** | `/pacientes/` | Cadastro de paciente (ID e horário local automáticos; o nome aceita só letras, espaços, hífen e apóstrofo, com pelo menos 2 letras, e é salvo no padrão "Maria da Silva"), consulta por ID via Tabela Hash, tabela geral e botão **Cancelar** (se *Aguardando*, cancela o cadastro; se *Em atendimento*, abre uma página de confirmação e, ao confirmar, cancela o atendimento e devolve à fila atrás das Emergências; o botão some quando o médico atual já cancelou aquele paciente). |
| **Triagem/Fila** | `/triagem/` | Fila por ordem de chamada (Min-Heap, destacando o próximo e pacientes em *Retorno*), fila por ordem de chegada (Árvore Rubro-Negra), formulário **Reclassificar** e botão **Chamar próximo paciente**. |
| **Médicos** | `/medicos/` | Cadastro de médicos clínicos (ID automático; nome com as mesmas regras do paciente; CRM no formato **CRM/UF 000000**, com UF escolhida na lista e número só com dígitos, gerado automaticamente se ficar em branco e recusado se já existir na mesma UF), consulta por ID via Tabela Hash e listagem com situação e atendimentos concluídos. |
| **Atendimentos** | `/atendimentos/` | Lista de atendimentos em andamento com botões **Concluir** e **Cancelar** (o botão Cancelar é ocultado quando o médico atual já cancelou aquele paciente anteriormente). |
| **Histórico** | `/historico/` | Totais por situação, atendimentos concluídos por médico, histórico cronológico de todas as chegadas (RB-Tree histórico), atendimentos encerrados (concluídos e cancelados) e pacientes cancelados. |
| **Diagnóstico** | `/diagnostico/` | Resultado de `validar_indices()`, capacidade, fator de carga e colisões das Tabelas Hash, validação e altura das Árvores Rubro-Negras e raízes dos dois Min-Heaps. |

## Reprodução dos cenários de teste pela interface

Parta sempre de `python manage.py resetar_demo`:

1. **Distribuição equilibrada (M1):**
   - Em **Médicos**, cadastre `Dra. A`, `Dr. B` e `Dra. C`.
   - Em **Pacientes**, cadastre 3 pacientes com prioridade `3 - Urgente`.
   - Em **Painel geral**, clique em **Chamar próximo** 3 vezes.
   - **Esperado:** as 3 chamadas são atribuídas em ordem a A, B e C.

2. **Menor carga após conclusões (M2) e cancelamento sem incremento (C3):**
   - A partir do cenário 1, cadastre um 4º paciente.
   - Em **Atendimentos**, conclua os atendimentos de A e B, e cancele o de C.
   - Em **Painel geral**, clique em **Chamar próximo**.
   - **Esperado:** C permanece com 0 concluídos e recebe a próxima chamada (A e B têm 1).

3. **Empate de contadores (M3):**
   - Com 3 médicos (A, B, C) e 5 pacientes, chame os 3 primeiros (A recebe `seq=1`, B `seq=2`, C `seq=3`).
   - Em **Atendimentos**, conclua fora de ordem (C, depois B, depois A).
   - Chame mais dois pacientes.
   - **Esperado:** vence quem está há mais tempo sem receber paciente (menor `seq` na chamada): A e depois B.

4. **Médico ocupado (M4) e sem médico disponível (M5):**
   - Com 1 médico e 2 pacientes, clique em **Chamar próximo** (o médico fica *Em atendimento*).
   - Clique em **Chamar próximo** novamente.
   - **Esperado:** mensagem informando que não há médicos disponíveis; o segundo paciente permanece intacto na fila.

5. **Prioridade clínica (P1) e reclassificação (B):**
   - Cadastre pacientes com prioridades `5`, `3` e `4`.
   - Em **Triagem/Fila**, reclassifique o paciente de prioridade `4` para `1 - Emergência`.
   - **Esperado:** ele assume imediatamente a 1ª posição na fila por prioridade sem duplicação, preservando a ordem original na fila por chegada.

6. **Cancelamento de atendimento — devolvido atrás das Emergências (K1, K2):**
   - Cadastre 1 médico e 1 paciente `4 - Pouco urgente`, e chame-o.
   - Cadastre um paciente `2 - Muito urgente` e um `1 - Emergência`.
   - Em **Atendimentos**, clique em **Cancelar**.
   - Em **Triagem/Fila**, confira a ordem: **Emergência → Devolvido (Retorno) → Muito urgente**.

7. **Cancelamento uma vez por médico sem bloqueio (K3, K4, K5):**
   - Com apenas 1 médico e 1 paciente: chame e cancele o atendimento.
   - Chame novamente: o mesmo médico recebe o paciente de volta (sem bloqueio).
   - Em **Atendimentos**, observe que o botão **Cancelar** não é mais exibido para esse médico/paciente (e qualquer tentativa via núcleo retorna `EstadoInvalido`).
   - Se outro médico assumir o paciente, esse outro médico ainda pode cancelar uma vez.

8. **Persistência após reinício (X2):**
   - Interrompa o servidor (`Ctrl+C`) e execute novamente `python manage.py runserver --noreload --nothreading`.
   - Acesse **Painel geral**, **Triagem/Fila** e **Diagnóstico**: filas, contadores, médicos e histórico permanecem idênticos e com `validar_indices()` OK.
