from __future__ import annotations

from typing import Any, Optional

Chave = tuple[str, int]

VERMELHO = "V"
NEGRO = "N"


class RBInvalidaError(Exception):
    pass


class No:
    __slots__ = ("chave", "valor", "cor", "esq", "dir", "pai")

    def __init__(self, chave: Chave, valor: Any = None, cor: str = VERMELHO, pai: "Optional[No]" = None):
        self.chave = chave
        self.valor = valor
        self.cor = cor
        self.esq: Optional[No] = None
        self.dir: Optional[No] = None
        self.pai = pai


class RBTree:
    def __init__(self) -> None:
        self._raiz: Optional[No] = None
        self._tamanho = 0

    def __len__(self) -> int:
        return self._tamanho

    def __contains__(self, chave: Chave) -> bool:
        return self._achar(chave) is not None

    def _achar(self, chave: Chave) -> Optional[No]:
        no = self._raiz
        while no is not None:
            if chave == no.chave:
                return no
            no = no.esq if chave < no.chave else no.dir
        return None

    def buscar(self, chave: Chave) -> Any:
        no = self._achar(chave)
        return None if no is None else no.valor

    def altura(self) -> int:
        def h(no: Optional[No]) -> int:
            return 0 if no is None else 1 + max(h(no.esq), h(no.dir))

        return h(self._raiz)

    def em_ordem(self) -> list[tuple[Chave, Any]]:
        resultado: list[tuple[Chave, Any]] = []
        pilha: list[No] = []
        no = self._raiz
        while pilha or no is not None:
            while no is not None:
                pilha.append(no)
                no = no.esq
            no = pilha.pop()
            resultado.append((no.chave, no.valor))
            no = no.dir
        return resultado

    def inserir(self, chave: Chave, valor: Any = None) -> None:
        pai: Optional[No] = None
        atual = self._raiz
        while atual is not None:
            if chave == atual.chave:
                raise ValueError(f"chave duplicada: {chave}")
            pai = atual
            atual = atual.esq if chave < atual.chave else atual.dir

        novo = No(chave, valor, VERMELHO, pai)
        if pai is None:
            self._raiz = novo
        elif chave < pai.chave:
            pai.esq = novo
        else:
            pai.dir = novo
        self._tamanho += 1
        self._corrigir_insercao(novo)

    def _corrigir_insercao(self, no: No) -> None:
        while no.pai is not None and no.pai.cor == VERMELHO:
            pai = no.pai
            avo = pai.pai
            if avo is None:
                break
            if pai is avo.esq:
                tio = avo.dir
                if tio is not None and tio.cor == VERMELHO:
                    pai.cor = NEGRO
                    tio.cor = NEGRO
                    avo.cor = VERMELHO
                    no = avo
                else:
                    if no is pai.dir:
                        no = pai
                        self._rotacionar_esquerda(no)
                        pai = no.pai
                    pai.cor = NEGRO
                    avo.cor = VERMELHO
                    self._rotacionar_direita(avo)
            else:
                tio = avo.esq
                if tio is not None and tio.cor == VERMELHO:
                    pai.cor = NEGRO
                    tio.cor = NEGRO
                    avo.cor = VERMELHO
                    no = avo
                else:
                    if no is pai.esq:
                        no = pai
                        self._rotacionar_direita(no)
                        pai = no.pai
                    pai.cor = NEGRO
                    avo.cor = VERMELHO
                    self._rotacionar_esquerda(avo)
        if self._raiz is not None:
            self._raiz.cor = NEGRO

    def remover(self, chave: Chave) -> bool:
        raise NotImplementedError

    def _rotacionar_esquerda(self, x: No) -> None:
        y = x.dir
        if y is None:
            raise ValueError("rotação à esquerda exige filho direito")
        x.dir = y.esq
        if y.esq is not None:
            y.esq.pai = x
        y.pai = x.pai
        if x.pai is None:
            self._raiz = y
        elif x is x.pai.esq:
            x.pai.esq = y
        else:
            x.pai.dir = y
        y.esq = x
        x.pai = y

    def _rotacionar_direita(self, x: No) -> None:
        y = x.esq
        if y is None:
            raise ValueError("rotação à direita exige filho esquerdo")
        x.esq = y.dir
        if y.dir is not None:
            y.dir.pai = x
        y.pai = x.pai
        if x.pai is None:
            self._raiz = y
        elif x is x.pai.dir:
            x.pai.dir = y
        else:
            x.pai.esq = y
        y.dir = x
        x.pai = y

    def validar(self) -> None:
        if self._raiz is None:
            if self._tamanho != 0:
                raise RBInvalidaError("árvore vazia, mas o tamanho registrado não é 0")
            return
        if self._raiz.pai is not None:
            raise RBInvalidaError("a raiz não deve ter pai")
        if self._raiz.cor != NEGRO:
            raise RBInvalidaError(f"a raiz deve ser negra (raiz {self._raiz.chave} é vermelha)")

        contados = 0

        def visitar(no: Optional[No], minimo: Optional[Chave], maximo: Optional[Chave]) -> int:
            nonlocal contados
            if no is None:
                return 1
            contados += 1
            if no.cor not in (VERMELHO, NEGRO):
                raise RBInvalidaError(f"cor inválida no nó {no.chave}: {no.cor!r}")
            if (minimo is not None and not no.chave > minimo) or (
                maximo is not None and not no.chave < maximo
            ):
                raise RBInvalidaError(f"ordem das chaves violada no nó {no.chave}")
            for filho in (no.esq, no.dir):
                if filho is not None and filho.pai is not no:
                    raise RBInvalidaError(f"ponteiro de pai inconsistente em {filho.chave}")
                if no.cor == VERMELHO and filho is not None and filho.cor == VERMELHO:
                    raise RBInvalidaError(
                        f"dois nós vermelhos seguidos: {no.chave} e {filho.chave}"
                    )
            he = visitar(no.esq, minimo, no.chave)
            hd = visitar(no.dir, no.chave, maximo)
            if he != hd:
                raise RBInvalidaError(f"altura negra diferente abaixo do nó {no.chave}")
            return he + (1 if no.cor == NEGRO else 0)

        visitar(self._raiz, None, None)
        if contados != self._tamanho:
            raise RBInvalidaError(
                f"tamanho registrado ({self._tamanho}) difere dos nós alcançáveis ({contados})"
            )

    def esta_valida(self) -> bool:
        try:
            self.validar()
        except RBInvalidaError:
            return False
        return True