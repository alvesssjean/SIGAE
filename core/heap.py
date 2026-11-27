"""Min-Heap binário como árvore completa explícita sem vetor (ADR-008, ADR-010)."""

from __future__ import annotations

from typing import Any, Callable, Iterator, Optional

from core.hash_table import HashTable


class HeapInvalidoError(ValueError):
    """Exceção levantada quando alguma invariante do MinHeap é violada."""


class NoHeap:
    __slots__ = ("item", "pai", "esq", "dir")

    def __init__(self, item: Any, pai: Optional[NoHeap] = None) -> None:
        self.item = item
        self.pai = pai
        self.esq: Optional[NoHeap] = None
        self.dir: Optional[NoHeap] = None


class MinHeap:
    """Min-Heap genérico com árvore binária completa ligada e mapa id->nó em HashTable."""

    def __init__(
        self,
        chave: Callable[..., Any],
        id_de: Callable[..., int],
    ) -> None:
        self._chave = chave
        self._id_de = id_de
        self._raiz: Optional[NoHeap] = None
        self._tamanho: int = 0
        self._mapa: HashTable = HashTable()

    def tamanho(self) -> int:
        return self._tamanho

    def __len__(self) -> int:
        return self._tamanho

    def contem(self, item_id: int) -> bool:
        return self._mapa.contem(item_id)

    def __contains__(self, item_id: int) -> bool:
        return self._mapa.contem(item_id)

    def raiz(self) -> Any:
        return None if self._raiz is None else self._raiz.item

    def _no_na_posicao(self, k: int) -> NoHeap:
        no = self._raiz
        if no is None:
            raise HeapInvalidoError("acesso a posição em heap vazio")
        for bit in range(k.bit_length() - 2, -1, -1):
            proximo = no.dir if (k >> bit) & 1 else no.esq
            if proximo is None:
                raise HeapInvalidoError(f"posição {k} inalcançável na árvore")
            no = proximo
        return no

    def _trocar_itens(self, no_a: NoHeap, no_b: NoHeap) -> None:
        no_a.item, no_b.item = no_b.item, no_a.item
        self._mapa.atualizar(self._id_de(no_a.item), no_a)
        self._mapa.atualizar(self._id_de(no_b.item), no_b)

    def _subir(self, no: NoHeap) -> None:
        while no.pai is not None:
            if self._chave(no.item) < self._chave(no.pai.item):
                self._trocar_itens(no, no.pai)
                no = no.pai
            else:
                break

    def _descer(self, no: NoHeap) -> None:
        while True:
            menor = no
            if no.esq is not None and self._chave(no.esq.item) < self._chave(menor.item):
                menor = no.esq
            if no.dir is not None and self._chave(no.dir.item) < self._chave(menor.item):
                menor = no.dir
            if menor is no:
                break
            self._trocar_itens(no, menor)
            no = menor

    def inserir(self, item: Any) -> None:
        item_id = self._id_de(item)
        if self._mapa.contem(item_id):
            raise ValueError(f"id duplicado no heap: {item_id}")

        novo = NoHeap(item)
        if self._tamanho == 0:
            self._raiz = novo
        else:
            pos = self._tamanho + 1
            pai = self._no_na_posicao(pos // 2)
            novo.pai = pai
            if pos % 2 == 0:
                pai.esq = novo
            else:
                pai.dir = novo

        self._tamanho += 1
        self._mapa.inserir(item_id, novo)
        self._subir(novo)

    def extrair_minimo(self) -> Any:
        if self._raiz is None:
            return None
        return self.remover(self._id_de(self._raiz.item))

    def alterar_prioridade(self, item_id: int) -> None:
        no = self._mapa.buscar(item_id)
        if no is None:
            raise KeyError(f"id não encontrado no heap: {item_id}")
        self._subir(no)
        self._descer(no)

    def remover(self, item_id: int) -> Any:
        no = self._mapa.buscar(item_id)
        if no is None:
            raise KeyError(f"id não encontrado no heap: {item_id}")

        removido = no.item
        ultimo = self._no_na_posicao(self._tamanho)

        if ultimo.pai is None:
            self._raiz = None
        elif ultimo is ultimo.pai.esq:
            ultimo.pai.esq = None
        else:
            ultimo.pai.dir = None
        ultimo.pai = None

        self._tamanho -= 1
        self._mapa.remover(item_id)

        if no is not ultimo:
            no.item = ultimo.item
            self._mapa.atualizar(self._id_de(no.item), no)
            self._subir(no)
            self._descer(no)

        return removido

    def itens(self) -> Iterator[Any]:
        def percorrer(no: Optional[NoHeap]) -> Iterator[Any]:
            if no is not None:
                yield no.item
                yield from percorrer(no.esq)
                yield from percorrer(no.dir)

        return percorrer(self._raiz)

    def validar(self) -> None:
        self._mapa.validar()
        if self._tamanho == 0:
            if self._raiz is not None:
                raise HeapInvalidoError("heap vazio possui raiz")
            if self._mapa.tamanho() != 0:
                raise HeapInvalidoError("heap vazio possui mapa não vazio")
            return

        if self._raiz is None:
            raise HeapInvalidoError("heap não vazio sem raiz")
        if self._raiz.pai is not None:
            raise HeapInvalidoError("raiz do heap não pode ter pai")
        if self._mapa.tamanho() != self._tamanho:
            raise HeapInvalidoError(
                f"tamanho do mapa ({self._mapa.tamanho()}) difere do heap ({self._tamanho})"
            )

        for k in range(1, self._tamanho + 1):
            no = self._no_na_posicao(k)
            if k == 1:
                if no.pai is not None:
                    raise HeapInvalidoError("raiz possui pai")
            else:
                pai_esperado = self._no_na_posicao(k // 2)
                if no.pai is not pai_esperado:
                    raise HeapInvalidoError(f"ponteiro de pai inconsistente na posição {k}")

            espera_esq = 2 * k <= self._tamanho
            espera_dir = 2 * k + 1 <= self._tamanho
            if (no.esq is not None) != espera_esq:
                raise HeapInvalidoError(f"filho esquerdo inconsistente na posição {k}")
            if (no.dir is not None) != espera_dir:
                raise HeapInvalidoError(f"filho direito inconsistente na posição {k}")

            item_id = self._id_de(no.item)
            if self._mapa.buscar(item_id) is not no:
                raise HeapInvalidoError(f"mapa inconsistente para id {item_id}")

            chave_atual = self._chave(no.item)
            if no.esq is not None and chave_atual > self._chave(no.esq.item):
                raise HeapInvalidoError(
                    f"propriedade min-heap violada entre posição {k} e filho esquerdo"
                )
            if no.dir is not None and chave_atual > self._chave(no.dir.item):
                raise HeapInvalidoError(
                    f"propriedade min-heap violada entre posição {k} e filho direito"
                )
