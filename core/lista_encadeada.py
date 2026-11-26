from __future__ import annotations

from typing import Any, Iterator, Optional


class NoLista:
    __slots__ = ("valor", "proximo")

    def __init__(self, valor: Any) -> None:
        self.valor = valor
        self.proximo: Optional[NoLista] = None


class ListaEncadeada:
    def __init__(self) -> None:
        self.cabeca: Optional[NoLista] = None
        self.cauda: Optional[NoLista] = None
        self.tamanho = 0

    def anexar(self, valor: Any) -> None:
        no = NoLista(valor)
        if self.cauda is None:
            self.cabeca = no
        else:
            self.cauda.proximo = no
        self.cauda = no
        self.tamanho += 1

    def inserir_inicio(self, valor: Any) -> None:
        no = NoLista(valor)
        no.proximo = self.cabeca
        self.cabeca = no
        if self.cauda is None:
            self.cauda = no
        self.tamanho += 1

    def remover_inicio(self) -> Any:
        no = self.cabeca
        if no is None:
            raise IndexError("lista vazia")
        self.cabeca = no.proximo
        if self.cabeca is None:
            self.cauda = None
        self.tamanho -= 1
        return no.valor

    def contem(self, valor: Any) -> bool:
        for item in self:
            if item == valor:
                return True
        return False

    def __iter__(self) -> Iterator[Any]:
        no = self.cabeca
        while no is not None:
            yield no.valor
            no = no.proximo

    def __len__(self) -> int:
        return self.tamanho

    def __bool__(self) -> bool:
        return self.tamanho > 0
