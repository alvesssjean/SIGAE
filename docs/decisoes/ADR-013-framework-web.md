# ADR-013: Framework da interface web

**Status:** Aceito (26/11/2026)

## Contexto
O documento base (§9.2) previa o terminal como interface obrigatória e Flask ou FastAPI como complemento HTML opcional. O enunciado final (PDF "Trabalho Final — SIGAE WEB", fonte que prevalece) exige uma aplicação web com no mínimo seis telas (Painel geral, Pacientes, Triagem/Fila, Médicos, Atendimentos e Histórico) e não exige terminal.

## Decisão
A interface é feita em **Django** (versão fixada no ADR-011), no pacote `web/`, com views e templates HTML/CSS, sem JavaScript e sem DRF.

- As views chamam exclusivamente `obter_sistema()` (`web/atendimento/servico.py`), que entrega a instância única de `Sistema` (`core/sistema.py`). Nunca importam `rbtree`, `heap`, `hash_table` nem `models`.
- Toda mutação segue POST → redirect → GET. Exceções de domínio viram mensagens do Django, sem erro 500.
- A persistência fica na porta `Repositorio` (ADR-004), detalhada no ADR-014.
- O terminal deixa de ser entrega (BACKLOG H24, *Won't*): `cli/menu.py` permanece vazio. `cli/demo_rbtree.py` e `interface_rb/` ficam apenas como apoio visual à defesa da Rubro-Negra.

## Alternativas consideradas
Flask ou FastAPI (documento base): exigiriam mais código manual de template, formulário e mensagens para a mesma entrega. Página com processamento no cliente (JavaScript): duplicaria as estruturas fora do núcleo testado em Python.

## Consequências
Seis telas obrigatórias mais a tela Diagnóstico. A separação é garantida por `tests/integracao/test_arquitetura_web.py` (imports das views e ausência de `order_by`, `filter` e `objects.get` em `web/`), e as telas são cobertas por `tests/integracao/test_web.py`. Os testes de aceitação A, B e C não dependem da web.
