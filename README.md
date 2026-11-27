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

A interface web (`web/`) utiliza **Django** com **Bootstrap 5** apenas para exibição e formulários: as views chamam exclusivamente `obter_sistema()`, e o banco de dados (SQLite localmente ou PostgreSQL no Docker) atua apenas como camada de persistência e rehidratação na inicialização (sem `order_by`, `filter` ou `objects.get` para regras de negócio).

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

> **Aviso de processo único:** execute sempre com `--noreload --nothreading`. O estado das estruturas de dados permanece em memória sincronizado com o banco; múltiplos processos ou threads concorrentes poderiam duplicar o estado em memória.

## Resetar e repopular dados fictícios

```bash
python manage.py resetar_demo
python manage.py popular_demo
```

## Execução com Docker Compose (PostgreSQL + Gunicorn + WhiteNoise)

```bash
docker compose up --build
```

Acesse no navegador: `http://127.0.0.1:8000/` (e as árvores/estruturas ao vivo em `http://127.0.0.1:8000/diagnostico/`).

- O serviço `db` sobe um **PostgreSQL 16** (`postgres:16-alpine`) com volume persistente `postgres_data` e healthcheck antes de iniciar o container `web`.
- O Gunicorn roda com `--workers 1 --threads 1` para preservar a consistência do estado em memória das estruturas (ADR-004).
- Os arquivos estáticos são servidos pelo **WhiteNoise** (`CompressedStaticFilesStorage`).
- Na primeira subida com base vazia, os dados fictícios são populados automaticamente (`AUTO_POPULAR_DEMO=1`).
- Sem `POSTGRES_DB` definido (execução local ou `pytest`), o Django usa SQLite automaticamente como fallback.
- Para resetar os dados dentro do container: `docker compose exec web python manage.py resetar_demo && docker compose exec web python manage.py popular_demo`.

## Testes automatizados

```bash
pytest -v
```

Os testes cobrem estruturas unitárias, proibição de coleções prontas via AST, arquitetura web, rollback com falha injetada, rehidratação do banco, consistência em 200 operações aleatórias, smoke tests web e todos os cenários de aceitação (A, A2, B, C, C2–C4, P1, R1, M1–M5, K1–K5, L1, X1, X2).

Para executar a demonstração interativa da Árvore Rubro-Negra no terminal:

```bash
python cli/demo_rbtree.py
```

## Documentação

- [Manual de uso](manual.md)
- [Relatório técnico](docs/RELATORIO.md)
- [Roteiro da defesa](docs/ROTEIRO_DEFESA.md)
- [Estudo do Min-Heap](docs/ESTUDO_HEAP.md)
- [Decisões de arquitetura (ADRs)](docs/decisoes/)
- [Evidências de testes](docs/evidencias/pytest.txt)
- [Documentos de referência](docs/referencia/)
