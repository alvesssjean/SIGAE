# T50_cancelamento_atendimento

- **Responsável sugerido:** I2
- **Descrição:** Suporte de rollback em ListaEncadeada (remover_valor) e testes de cancelamento
- **Validação:** `pytest tests/unit/test_lista_encadeada.py tests/integracao/test_cancelamento.py -v`

## Como aplicar
1. Extraia este ZIP na **raiz do repositório SIGAE**.
2. Remova `INSTRUCOES.md` antes de fazer `git add`.

## Arquivos desta task (3)
- `core/lista_encadeada.py`
- `tests/unit/test_lista_encadeada.py`
- `tests/integracao/test_cancelamento.py`
