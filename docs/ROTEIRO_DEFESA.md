# Roteiro da Defesa — SIGAE WEB

O professor opera o sistema livremente pela interface web e também pode executar `pytest -v`. Cada integrante apresenta sua parte em **2 a 3 minutos**.

## 1. Preparação antes da apresentação

```bash
python manage.py resetar_demo
python manage.py popular_demo
python manage.py runserver --noreload --nothreading
```

Abrir as abas: **Painel geral** (`/`), **Triagem/Fila** (`/triagem/`), **Atendimentos** (`/atendimentos/`) e **Diagnóstico** (`/diagnostico/`).

## 2. Ordem dos cenários pela interface (BACKLOG §6)

1. **Cadastro e fila por chegada / prioridade (P1, H01, H05):** mostrar os pacientes em **Triagem/Fila** (Min-Heap vs RB-Tree) e consultar um paciente por ID em **Pacientes** (Hash).
2. **Reclassificação (B):** em **Triagem/Fila**, alterar um paciente de prioridade baixa para `1 - Emergência` e mostrar que sobe para o topo sem duplicar e sem alterar a ordem de chegada na RB-Tree.
3. **Distribuição equilibrada entre médicos (M1, M2, M3, M4):** chamar 3 pacientes com A, B e C zerados (um para cada); concluir alguns e mostrar que o próximo vai para o médico de menor carga (e desempate pelo relógio lógico da chamada).
4. **Sem médico disponível (M5):** com todos os médicos ocupados, clicar em **Chamar próximo** e mostrar a mensagem de erro sem perda nem duplicação na fila.
5. **Cancelamento de atendimento (K1–K5, exemplo do BACKLOG §2.3):**
   - Com médicos A e B, chamar X (Muito urgente) → A e Y → B; cadastrar E (Emergência).
   - A cancela X: X volta à fila em **2º lugar** (atrás de E e à frente de prioridades 2 a 5), marcado como *Retorno*; A volta a *Disponível* com contador inalterado e anotado em `X.medicos_que_cancelaram`.
   - Próxima chamada entrega E → A (Emergência prevalece).
   - Demonstrar que se A receber X novamente, o botão de cancelar desaparece (regra de no máximo 1 cancelamento por médico para o mesmo paciente), enquanto outro médico ainda pode cancelar uma vez.
6. **Cancelamento de cadastro e consistência (C, C2, C3):** cancelar um paciente *Aguardando* e abrir **Diagnóstico** (`/diagnostico/`) mostrando `validar_indices()` OK, estatísticas da Hash, alturas das RB-Trees e raízes dos Heaps.
7. **Rehidratação após reinício (X2):** reiniciar o servidor com `runserver --noreload --nothreading` e comprovar que filas, contadores e estados permanecem intactos.

## 3. Divisão das falas (2 a 3 minutos cada)

| Integrante | Tema | Pontos obrigatórios |
|---|---|---|
| **I1** | Árvore Rubro-Negra (`core/rbtree.py`) | Balanceamento (casos 1, 2 e 3 na inserção; transplante, sucessor e duplo negro na remoção), rotações esquerda/direita, recoloração, `validar()`, retirada de `list`/`dict` (`em_ordem()` como gerador por ponteiro `pai`, `eventos` em `ListaEncadeada`) e apoio visual com `cli/demo_rbtree.py` e `interface_rb/`. |
| **I2** | Min-Heaps sem vetor (`core/heap.py`) | Árvore binária completa explícita com ponteiros `item/pai/esq/dir`, localização da posição `k` pelos bits de `k` em O(log n), trocas movendo itens (não nós), mapa `id -> nó` na `HashTable` para `alterar_prioridade(id)` e `remover(id)` em O(log n), chaves de pacientes `(classe, prioridade, horario, id)` e médicos `(concluidos, seq_ultima_atribuicao, id)`, médico fora do heap quando ocupado. |
| **I3** | Tabela Hash (`core/hash_table.py`) e Integração (`core/sistema.py`) | Função `h(id) = id % capacidade`, tupla imutável de sentinelas (O(1) sem `list`), colisão 101 e 108 com capacidade 7, redimensionamento para próximo primo >= 2x (7 → 17 → 37) ao passar de 0,75 religando os nós existentes; fluxo de rollback por pilha de compensações em `ListaEncadeada` + `transaction.atomic()` no SQLite. |
| **Jean** | Arquitetura, Testes e Consistência | ADRs (`docs/decisoes/`), desacoplamento views → `obter_sistema()` → porta `Repositorio`, execução de `pytest -v` (182 testes), garantia automática via AST (`test_sem_estruturas_prontas.py`), teste de arquitetura web (`test_arquitetura_web.py`), teste de rollback e consistência em 200 operações com SQLite. |

## 4. Perguntas prováveis e respostas prontas

- **Por que não usar `list` no núcleo?**
  Decisão do grupo (ADR-010) para garantir que nenhuma coleção pronta da linguagem substitua ou mascare as estruturas implementadas pela equipe. Listagens usam `ListaEncadeada` própria, o Heap usa árvore binária completa ligada e a Hash usa tupla imutável de sentinelas. O teste `test_sem_estruturas_prontas.py` valida isso via AST em todo `core/`.
- **Por que o paciente devolvido fica logo atrás das Emergências (e à frente das prioridades 2 a 5)?**
  As Emergências (prioridade 1) nunca são ultrapassadas, respeitando a prioridade clínica máxima exigida no enunciado. O paciente devolvido já havia sido chamado e perdeu a vez por motivo alheio a ele (cancelamento do atendimento), por isso recebe `classe = 1` na chave `(classe, prioridade, horario, id)` (ADR-012). Alterar essa política exige mudar apenas `Paciente.chave_heap()`.
- **Por que o SQLite não responde buscas ou ordenações?**
  O banco atua exclusivamente como camada de persistência e rehidratação na inicialização (ADR-004). Buscas por ID vêm da Hash, fila de chegada vem da RB-Tree e ordem de chamada vem dos Min-Heaps. O teste `test_arquitetura_web.py` impede o uso de `order_by`, `filter` e `objects.get` em `web/`.
- **Quais são as complexidades das operações?**
  - **Tabela Hash:** inserção, busca e remoção em O(1) médio (O(n) pior caso); redimensionamento O(n) amortizado.
  - **Min-Heap (árvore ligada):** `inserir`, `extrair_minimo`, `alterar_prioridade(id)` e `remover(id)` em O(log n); `raiz` em O(1).
  - **Árvore Rubro-Negra:** `inserir`, `remover` e `buscar` em O(log n); percurso `em_ordem()` por sucessor via `pai` em O(n).
  - **Lista Encadeada:** `anexar`, `inserir_inicio` e `remover_inicio` em O(1); busca linear em O(n).
