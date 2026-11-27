# SIGAE WEB

Sistema Inteligente de Gerenciamento de Atendimentos de Emergência.
Simulador acadêmico desenvolvido na disciplina **Estrutura de Dados Avançados** (Universidade de Vassouras). Todos os dados utilizados são 100% fictícios.

## Arquitetura e estruturas implementadas

Todo o núcleo (`core/`) é implementado em Python puro, sem uso de `list`, `dict`, `set`, `frozenset`, `heapq` ou `sorted()` (verificado automaticamente por `tests/unit/test_sem_estruturas_prontas.py`).

| Estrutura | Arquivo | Uso |
|---|---|---|
| Lista Encadeada | `core/lista_encadeada.py` | Retorno de listagens, eventos da RB-Tree e pilha de compensações do rollback |
| Tabela Hash | `core/hash_table.py` | Consulta por ID de pacientes, médicos e atendimentos; mapa `id -> nó` do Min-Heap |
| Min-Heap (árvore binária completa sem vetor) | `core/heap.py` | Fila de prioridade de pacientes e balanceamento de carga entre médicos |
| Árvore Rubro-Negra | `core/rbtree.py` | Fila de espera por ordem de chegada e histórico cronológico de chegadas |
| Núcleo Integrador | `core/sistema.py` | Regras de negócio, validação, rollback atômico e validação cruzada de índices |

A interface web (`web/`) utiliza **Django** apenas para exibição e formulários: as views chamam exclusivamente `obter_sistema()`, e o **SQLite** atua apenas como camada de persistência e rehidratação na inicialização (sem `order_by`, `filter` ou `objects.get` para regras de negócio).

## Requisitos

- Python 3.11 ou superior

## Instalação e execução

```bash
python -m venv .venv
source .venv/bin/activate        # Windows (PowerShell): .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py popular_demo
python manage.py runserver --noreload --nothreading
```

Acesse no navegador: `http://127.0.0.1:8000/`

> **Aviso de processo único:** execute sempre com `--noreload --nothreading`. O estado das estruturas de dados permanece em memória sincronizado com o SQLite; múltiplos processos ou threads concorrentes poderiam duplicar o estado em memória.

## Resetar e repopular dados fictícios

```bash
python manage.py resetar_demo
python manage.py popular_demo
```

## Testes automatizados

```bash
pytest -v
```

Os testes cobrem estruturas unitárias, proibição de coleções prontas via AST, arquitetura web, rollback com falha injetada, rehidratação do SQLite, consistência em 200 operações aleatórias, smoke tests web e todos os cenários de aceitação (A, A2, B, C, C2–C4, P1, R1, M1–M5, K1–K5, L1, X1, X2).

Para executar a demonstração interativa da Árvore Rubro-Negra no terminal:

```bash
python cli/demo_rbtree.py
```

## Documentação

- [Manual de uso](manual.md)
- [Relatório técnico](docs/RELATORIO.md)
- [Roteiro da defesa](docs/ROTEIRO_DEFESA.md)
- [Decisões de arquitetura (ADRs)](docs/decisoes/)
- [Evidências de testes](docs/evidencias/pytest.txt)
- [Documentos de referência](docs/referencia/)
