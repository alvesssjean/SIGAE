# Relatório Técnico — SIGAE WEB

## 1. Objetivo

O **SIGAE WEB** (Sistema Inteligente de Gerenciamento de Atendimentos de Emergência) é um simulador acadêmico desenvolvido para a disciplina **Estrutura de Dados Avançados** (Universidade de Vassouras). O sistema gerencia a fila de pronto atendimento, triagem por prioridade clínica, distribuição equilibrada entre médicos clínicos e histórico de atendimentos utilizando estruturas de dados implementadas do zero pela equipe, sem uso de coleções prontas (`list`, `dict`, `set`, `heapq` ou `sorted`) no núcleo.

## 2. Arquitetura

```text
Navegador ── Django (views + templates HTML/CSS, sem JS, sem DRF)
                │ chama exclusivamente obter_sistema().<operação>()
                ▼
         core/sistema.py ── validar → aplicar (pilha compensações) → gravar → rollback se falhar
          │      │       │          │         │            │
         Hash   Hash  RB espera   Heap      Heap     Porta Repositorio
        pacien. méd.  + RB hist. pacien.   médicos   ├─ RepositorioMemoria (testes)
        + atend.                                     └─ RepositorioDjango (SQLite, atomic)
```

Princípios arquiteturais garantidos por testes automatizados:

- **Núcleo puro (`core/`):** não importa Django e não utiliza `list`, `dict`, `set`, `frozenset`, `heapq`, `sorted()`, `.split()` ou `**kwargs` ([ADR-010](decisoes/ADR-010-nucleo-sem-colecoes-prontas.md)).
- **Separação da interface (`web/`):** views chamam apenas `obter_sistema()`, convertem exceções de domínio em mensagens Django (sem erro 500) e seguem o padrão POST → redirect → GET.
- **SQLite apenas como persistência:** o ORM é lido somente em `carregar_tudo()` (`.all()` sem ordenação) na inicialização, nunca para consultas ou ordenações de negócio ([ADR-004](decisoes/ADR-004-persistencia.md)).

## 3. Estruturas de dados e complexidade

### 3.1 Lista Encadeada (`core/lista_encadeada.py`)

Lista simplesmente encadeada com ponteiros `cabeca`, `cauda` e `tamanho`. Implementa `__iter__`, `__len__`, `__bool__` e `__contains__`, sendo compatível com templates Django (`{% for %}` e `|length`). Utilizada como retorno das listagens do núcleo, registro de eventos da RB-Tree e pilha de compensações do rollback.

- `anexar`, `inserir_inicio`, `remover_inicio`: **O(1)**
- `contem`, `remover_valor`, iteração completa: **O(n)**

### 3.2 Árvore Rubro-Negra (`core/rbtree.py`)

Árvore binária de busca autobalanceada com inserção (casos 1, 2 e 3 simétricos) e remoção completa (transplante, sucessor e correção de duplo negro em 4 casos simétricos). Mantém duas instâncias no núcleo ([ADR-007](decisoes/ADR-007-escopo-dos-indices.md)): **RB espera** (apenas pacientes *Aguardando*) e **RB histórico** (todas as chegadas, nunca removidas), ambas indexadas pela chave `(horario_iso, id)`. O percurso `em_ordem()` é um gerador sem pilha que avança pelo sucessor via ponteiro `pai`.

- `inserir`, `remover`, `buscar`: **O(log n)**
- `em_ordem()`, `validar()`: **O(n)**

### 3.3 Min-Heap sem vetor (`core/heap.py`)

Árvore binária completa explícita com nós ligados (`item`, `pai`, `esq`, `dir`) e mapa `id -> nó` mantido na `HashTable` do projeto ([ADR-008](decisoes/ADR-008-heap-de-nos-ligados.md)). A posição `k` (`1..n`) é alcançada pelos bits de `k` (ignorando o bit mais significativo: `0` esquerda, `1` direita), e as trocas movem apenas os itens entre nós atualizando o mapa. A mesma classe `MinHeap` atende aos dois heaps:

- **Heap de pacientes:** chave `(classe, prioridade, horario, id)` ([ADR-012](decisoes/ADR-012-cancelamento-de-atendimento.md)).
- **Heap de médicos:** chave `(concluidos, seq_ultima_atribuicao, id)` ([ADR-005](decisoes/ADR-005-medico-fora-do-heap.md), [ADR-006](decisoes/ADR-006-relogio-logico.md)). Médicos ocupados saem do heap e retornam ao concluir ou cancelar o atendimento.

Complexidades:

- `raiz`: **O(1)**
- `inserir`, `extrair_minimo`, `alterar_prioridade(id)`, `remover(id)`: **O(log n)**
- `listar_fila_prioridade()` (cópia em heap auxiliar sem alterar o original): **O(n log n)**

### 3.4 Tabela Hash (`core/hash_table.py`)

Tabela Hash com função modular `h(id) = id % capacidade`, capacidade inicial 7 e encadeamento separado com nós próprios ([ADR-001](decisoes/ADR-001-capacidade-hash.md)). O vetor de buckets é uma **tupla imutável de nós-sentinela** (`tuple(Sentinela() for _ in range(cap))`), eliminando `list`. Ao ultrapassar o fator de carga de `0,75`, redimensiona para o próximo primo ≥ 2× a capacidade atual (`7 → 17 → 37 → ...`), religando os nós existentes sem alocar novos nós ([ADR-002](decisoes/ADR-002-fator-de-carga.md)).

- `inserir`, `buscar`, `remover`, `atualizar`: **O(1)** médio, **O(n)** pior caso
- `redimensionar`, `estatisticas`, `validar`: **O(n + m)**

## 4. Rollback, persistência e rehidratação

Toda operação mutável em `core/sistema.py` é protegida por `threading.Lock` e segue o fluxo do [ADR-003](decisoes/ADR-003-rollback.md):

1. Valida pré-condições sem produzir efeitos colaterais.
2. Aplica cada alteração nas estruturas em memória empilhando sua função inversa (compensação) em uma `ListaEncadeada`.
3. Persiste as entidades alteradas e os contadores dentro de `with repositorio.transacao():` (`transaction.atomic()` no `RepositorioDjango`).
4. Se qualquer passo em memória ou no banco lançar exceção, desempilha e executa todas as compensações em ordem LIFO e relança o erro, garantindo consistência integral entre memória e banco.

Na inicialização (`web/atendimento/servico.py`), `Sistema.carregar(RepositorioDjango())` lê todas as tabelas com `.all()` sem ordenação e reconstrói integralmente as três Tabelas Hash, as duas Árvores Rubro-Negras, os dois Min-Heaps, os contadores de IDs, o relógio lógico e a lista `medicos_que_cancelaram` (reconstruída a partir dos atendimentos com status *Cancelado*).

## 5. Regra de cancelamento de atendimento

Conforme o [ADR-012](decisoes/ADR-012-cancelamento-de-atendimento.md), cancelar um atendimento em andamento:

- Marca o atendimento como *Cancelado* com horário de fim.
- Devolve o paciente para *Aguardando* com `retorno = True`, reinserindo-o na RB espera (posição de chegada original) e no Heap de pacientes com `classe = 1`, ficando **logo atrás das Emergências (`classe = 0`)** e à frente das prioridades 2 a 5 (`classe = 2`).
- Devolve o médico ao estado *Disponível* e ao Heap de médicos **sem incrementar `concluidos`** e mantendo `seq_ultima_atribuicao`.
- Registra o médico em `paciente.medicos_que_cancelaram`. O mesmo médico pode atender o paciente novamente sem bloqueio, mas não pode cancelá-lo uma segunda vez (`EstadoInvalido`).

## 6. Decisões de arquitetura (ADRs)

- [ADR-001](decisoes/ADR-001-capacidade-hash.md) · Capacidade inicial e função de hash
- [ADR-002](decisoes/ADR-002-fator-de-carga.md) · Fator de carga e redimensionamento
- [ADR-003](decisoes/ADR-003-rollback.md) · Rollback por pilha de compensações
- [ADR-004](decisoes/ADR-004-persistencia.md) · Porta Repositorio e SQLite apenas como persistência
- [ADR-005](decisoes/ADR-005-medico-fora-do-heap.md) · Médico fora do heap quando ocupado
- [ADR-006](decisoes/ADR-006-relogio-logico.md) · Desempate por relógio lógico marcado na chamada
- [ADR-007](decisoes/ADR-007-escopo-dos-indices.md) · Escopo dos índices e entidade Paciente mutável
- [ADR-008](decisoes/ADR-008-heap-de-nos-ligados.md) · Heap como árvore binária completa ligada com mapa em HashTable
- [ADR-009](decisoes/ADR-009-horario-de-chegada.md) · Horário local automático em formato ISO e relógio injetável
- [ADR-010](decisoes/ADR-010-nucleo-sem-colecoes-prontas.md) · Núcleo sem coleções prontas e escopo da camada Django
- [ADR-011](decisoes/ADR-011-django-e-testes.md) · Django 5.2 e testes sem `pytest-django`
- [ADR-012](decisoes/ADR-012-cancelamento-de-atendimento.md) · Cancelamento de atendimento uma vez por médico

## 7. Resultados dos testes

A suíte executada com `pytest -v` (evidência completa em [docs/evidencias/pytest.txt](evidencias/pytest.txt)) obteve **175 testes aprovados, 0 falhas e 0 xfails**:

- **Unitários (`tests/unit/`):** `ListaEncadeada`, `HashTable` (colisões 101/108, redimensionamento, remoções), `MinHeap` (incluindo 500 operações aleatórias), `MinHeap` de médicos, entidades/relógio, `RBTree` (inserções/remoções aleatórias) e guarda AST `test_sem_estruturas_prontas.py` em todos os arquivos de `core/`.
- **Integração (`tests/integracao/`):** operações de pacientes, médicos, cancelamento, rollback em falhas de gravação e de estrutura (12 cenários), rehidratação e transação parcial no SQLite, consistência estruturas × SQLite em 200 operações pseudoaleatórias, smoke tests web (7 rotas + fluxos POST) e teste estático de arquitetura web.
- **Aceitação (`tests/aceitacao/`):** cenários A, A2, B, C, C2, C3, C4, P1, M1–M5 e K1–K5, todos encerrando com `validar_indices().ok`.

## 8. Limitações conhecidas

- **Processo único obrigatório:** o estado das estruturas vive na memória do processo Django sincronizado com o SQLite; por isso o servidor deve ser executado com `runserver --noreload --nothreading`.
- **Escopo acadêmico:** não há autenticação/autorização de usuários, múltiplos prontos-socorros ou API REST; todos os dados de demonstração são fictícios.
