# Roteiro da defesa (rascunho)

O professor opera o sistema. Cada integrante fala de 2 a 3 minutos.

| Quem | Assunto | Mostrar |
|---|---|---|
| I1 (nome) | Rubro-Negra | rotações, recoloração, remoção, `validar()`, `demo_rbtree.py` |
| I2 (nome) | Heaps | nós ligados, posição pelos bits, chaves, desempate, mapa id→nó |
| I3 (nome) | Hash e integração | colisão 101/108, redimensionamento, rollback |
| Jean | Arquitetura e testes | ADRs, `pytest -v`, consistência |

## Perguntas prováveis
- **Por que não usar `list`?** Decisão do grupo para que nenhuma coleção pronta substitua as estruturas (ADR-010).
- **Por que o devolvido fica atrás das Emergências?** A prioridade clínica máxima nunca é ultrapassada; ele já tinha sido chamado (ADR-012).
- **E ele passar à frente de prioridades 2 a 5?** É uma exceção decidida pelo grupo; para mudar basta alterar `chave_heap()`.
- **Por que o banco não responde consultas?** Ele só persiste; buscas e ordens vêm das estruturas (ADR-004).
- **Complexidades?** Hash O(1) médio, O(n) pior caso; Heap e Rubro-Negra O(log n); percurso em ordem O(n).
