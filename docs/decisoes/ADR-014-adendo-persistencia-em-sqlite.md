# ADR-013 · Adendo: persistência em SQLite

**Status:** Proposto
**Data:** 26/11/2026
**Decisores:** Equipe SIGAE · Professor (cliente)

## Contexto

O documento base (seção 3) e o ADR-013 previam estado mantido apenas em memória. Posteriormente, o professor passou a exigir persistência em banco de dados.

## Decisão

A persistência será feita em **SQLite**, acessada pelo ORM do Django, dentro de `web/`.

- O banco guarda somente os registros de pacientes (id, nome, horário de chegada e prioridade).
- O `SistemaSigae` continua sendo o único ponto de acesso às estruturas. Ao iniciar, ele reconstrói a RB-Tree, o Heap e a Hash a partir dos registros salvos.
- A interface não consulta o banco para regras de fila. Toda operação passa pelo `SistemaSigae`, que depois sincroniza o banco.
- Os testes de aceitação A, B e C (`tests/aceitacao/`) continuam valendo sem o banco, porque testam o núcleo em memória.

## Consequências

- A seção 3 (fora do escopo) e a seção 9.2 (dependências) do documento base devem ser atualizadas: Django e SQLite passam a ser permitidos, e a persistência sai de "fora do escopo".
- Se `SistemaSigae` não tiver ponto de extensão para carregar e salvar, isso exige ajuste em `core/`. Esse ajuste precisa ser combinado com o integrante 3 antes de ser feito.
- O cronograma não muda, mas a Iteração 3 fica mais apertada. O escopo mínimo continua sendo as sete operações.