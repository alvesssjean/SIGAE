# ADR-014: Adendo ao ADR-004, persistência em SQLite

**Status:** Aceito (26/11/2026)

## Contexto
O documento base (§3) mantinha o estado só em memória. O professor aceitou SQLite e execução local (BACKLOG §9.1, resposta 4), e o enunciado (§4) pede preservar o total de atendimentos de cada médico "enquanto durar a sessão ou persistência do sistema". O ADR-004 definiu a porta `Repositorio`; este adendo registra o que é gravado e como o estado volta.

## Decisão
SQLite acessado pelo ORM do Django, só dentro de `web/` (`models.py` e `repositorio_django.py`), implementando a porta `Repositorio`. Os IDs vêm do núcleo, sem autoincremento do banco.

| Tabela | Campos |
|---|---|
| `sigae_paciente` | id, nome, horario, prioridade, situacao, retorno |
| `sigae_medico` | id, nome, registro, situacao, concluidos, seq_ultima_atribuicao |
| `sigae_atendimento` | id, paciente_id, medico_id, inicio, fim, status |
| `sigae_contador` | ultimo_paciente_id, ultimo_medico_id, ultimo_atendimento_id, relogio_logico |

- `medicos_que_cancelaram` não tem tabela: é reconstruída a partir dos atendimentos Cancelados (paciente_id, medico_id), conforme o ADR-012.
- Cada operação de `Sistema` grava dentro de `repositorio.transacao()` (`transaction.atomic()`), com `update_or_create` pelo ID; se algo falhar, o banco desfaz e as compensações do ADR-003 restauram a memória.
- Na inicialização, `obter_sistema()` chama `Sistema.carregar(RepositorioDjango())`, que lê cada tabela com `.all()`, sem ordenação, e reconstrói as três Hash, as duas Rubro-Negras, os dois Heaps, os contadores e o relógio lógico.
- O banco nunca responde busca nem ordenação de regra de negócio (ADR-004).

## Alternativas consideradas
Gravar só os pacientes (versão proposta deste ADR): no reinício perderia médicos, contadores, relógio lógico e atendimentos, descumprindo o enunciado §4. Arquivo JSON: sem transação atômica junto com o rollback.

## Consequências
Execução em processo único (`runserver --noreload --nothreading`). Os testes de aceitação continuam em memória com `RepositorioMemoria`; a persistência é coberta por `tests/integracao/test_rehidratacao.py` e `tests/integracao/test_consistencia_sqlite.py`. `db.sqlite3` fica fora do repositório e é criado por `migrate`; `resetar_demo` e `popular_demo` passam pelo `Sistema`.
