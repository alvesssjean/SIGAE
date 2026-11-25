# SIGAE WEB

Sistema Inteligente de Gerenciamento de Atendimentos de Emergência.
Simulador acadêmico (Estrutura de Dados Avançados, Universidade de Vassouras). Todos os dados são fictícios.

## Estado do projeto
Em desenvolvimento. A interface web ainda não está disponível.

## Estruturas implementadas pela equipe
| Estrutura | Uso |
|---|---|
| Árvore Rubro-Negra | ordem de chegada |
| Min-Heap (pacientes e médicos) | prioridade e balanceamento |
| Tabela Hash | consulta por ID |

## Requisitos
Python 3.11 ou superior.

## Instalação e testes
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

## Documentação
- [Decisões de arquitetura](docs/decisoes/)
- [Manual de uso](manual.md)
- [Documentos de referência](docs/referencia/)
