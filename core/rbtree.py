from __future__ import annotations

from typing import Any, Iterator, Optional

from core.lista_encadeada import ListaEncadeada

Chave = tuple[str, int]

VERMELHO = "V"
NEGRO = "N"


class RBInvalidaError(Exception):
    pass


class No:
    __slots__ = ("chave", "valor", "cor", "esq", "dir", "pai")

    def __init__(
        self,
        chave: Chave,
        valor: Any = None,
        cor: str = VERMELHO,
        pai: "Optional[No]" = None,
    ):
        self.chave = chave
        self.valor = valor
        self.cor = cor
        self.esq: Optional[No] = None
        self.dir: Optional[No] = None
        self.pai = pai


def nome_cor(cor: str) -> str:
    if cor == VERMELHO:
        return "vermelho"
    return "negro"


def rotulo(chave: Chave) -> str:
    return f"{chave[0]}#{chave[1]}"


def cor_de(no: Optional[No]) -> str:
    return NEGRO if no is None else no.cor


def exigir(no: Optional[No]) -> No:
    if no is None:
        raise RBInvalidaError("estrutura inconsistente durante a operação")
    return no


class RBTree:
    def __init__(self, rastrear: bool = False) -> None:
        self._raiz: Optional[No] = None
        self._tamanho = 0
        self._rastrear = rastrear
        self.eventos = ListaEncadeada()
        self.ao_registrar: Any = None

    def __len__(self) -> int:
        return self._tamanho

    def raiz(self) -> Optional[No]:
        return self._raiz

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

    def em_ordem(self) -> Iterator[tuple[Chave, Any]]:
        no = None if self._raiz is None else self._minimo(self._raiz)
        while no is not None:
            yield (no.chave, no.valor)
            no = self._sucessor(no)

    def _minimo(self, no: No) -> No:
        while no.esq is not None:
            no = no.esq
        return no

    def _sucessor(self, no: No) -> Optional[No]:
        if no.dir is not None:
            return self._minimo(no.dir)
        pai = no.pai
        while pai is not None and no is pai.dir:
            no = pai
            pai = pai.pai
        return pai

    def desenhar(self, cores: bool = False) -> str:
        if self._raiz is None:
            return "(árvore vazia)"

        def texto(no: No) -> str:
            base = f"{rotulo(no.chave)} [{no.cor}]"
            if not cores:
                return base
            codigo = "\033[91m" if no.cor == VERMELHO else "\033[7m"
            return f"{codigo}{base}\033[0m"

        def descer(no: No, prefixo: str) -> str:
            resultado = ""
            if no.esq is not None:
                ultimo = no.dir is None
                ramo = "`-- " if ultimo else "|-- "
                resultado += f"\n{prefixo}{ramo}E: {texto(no.esq)}"
                resultado += descer(no.esq, prefixo + ("    " if ultimo else "|   "))
            if no.dir is not None:
                resultado += f"\n{prefixo}`-- D: {texto(no.dir)}"
                resultado += descer(no.dir, prefixo + "    ")
            return resultado

        return texto(self._raiz) + descer(self._raiz, "")

    def _registrar(self, texto: str) -> None:
        if self._rastrear:
            self.eventos.anexar(texto)
            if self.ao_registrar is not None:
                self.ao_registrar(texto)

    def _pintar(self, no: No, cor: str) -> None:
        if no.cor != cor:
            self._registrar(
                f"recolorir {rotulo(no.chave)}: {nome_cor(no.cor)} -> {nome_cor(cor)}"
            )
            no.cor = cor

    def inserir(self, chave: Chave, valor: Any = None) -> None:
        self.eventos = ListaEncadeada()
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
        self._registrar(f"inserir {rotulo(chave)} (nasce vermelho)")
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
                    self._registrar("caso 1: tio vermelho, recolore pai, tio e avô")
                    self._pintar(pai, NEGRO)
                    self._pintar(tio, NEGRO)
                    self._pintar(avo, VERMELHO)
                    no = avo
                else:
                    if no is pai.dir:
                        self._registrar("caso 2: tio negro, nó em zigue-zague")
                        no = pai
                        self._rotacionar_esquerda(no)
                        pai = exigir(no.pai)
                    self._registrar("caso 3: tio negro, nó em linha")
                    self._pintar(pai, NEGRO)
                    self._pintar(avo, VERMELHO)
                    self._rotacionar_direita(avo)
            else:
                tio = avo.esq
                if tio is not None and tio.cor == VERMELHO:
                    self._registrar("caso 1: tio vermelho, recolore pai, tio e avô")
                    self._pintar(pai, NEGRO)
                    self._pintar(tio, NEGRO)
                    self._pintar(avo, VERMELHO)
                    no = avo
                else:
                    if no is pai.esq:
                        self._registrar("caso 2: tio negro, nó em zigue-zague")
                        no = pai
                        self._rotacionar_direita(no)
                        pai = exigir(no.pai)
                    self._registrar("caso 3: tio negro, nó em linha")
                    self._pintar(pai, NEGRO)
                    self._pintar(avo, VERMELHO)
                    self._rotacionar_esquerda(avo)
        if self._raiz is not None:
            self._pintar(self._raiz, NEGRO)

    def remover(self, chave: Chave) -> bool:
        self.eventos = ListaEncadeada()
        z = self._achar(chave)
        if z is None:
            return False
        self._registrar(f"remover {rotulo(chave)}")
        y = z
        cor_original = y.cor
        x: Optional[No]
        x_pai: Optional[No]
        if z.esq is None:
            x = z.dir
            x_pai = z.pai
            self._transplantar(z, z.dir)
        elif z.dir is None:
            x = z.esq
            x_pai = z.pai
            self._transplantar(z, z.esq)
        else:
            y = self._minimo(z.dir)
            self._registrar(
                f"nó com dois filhos: sucessor {rotulo(y.chave)} assume o lugar"
            )
            cor_original = y.cor
            x = y.dir
            if y.pai is z:
                x_pai = y
            else:
                x_pai = y.pai
                self._transplantar(y, y.dir)
                y.dir = z.dir
                exigir(y.dir).pai = y
            self._transplantar(z, y)
            y.esq = z.esq
            exigir(y.esq).pai = y
            self._pintar(y, z.cor)
        self._tamanho -= 1
        if cor_original == NEGRO:
            self._registrar("o nó removido era negro: corrigir o duplo negro")
            self._corrigir_remocao(x, x_pai)
        elif x is not None:
            self._pintar(x, NEGRO)
        return True

    def _transplantar(self, u: No, v: Optional[No]) -> None:
        if u.pai is None:
            self._raiz = v
        elif u is u.pai.esq:
            u.pai.esq = v
        else:
            u.pai.dir = v
        if v is not None:
            v.pai = u.pai

    def _corrigir_remocao(self, x: Optional[No], x_pai: Optional[No]) -> None:
        while x is not self._raiz and cor_de(x) == NEGRO:
            if x_pai is None:
                break
            if x is x_pai.esq:
                w = exigir(x_pai.dir)
                if w.cor == VERMELHO:
                    self._registrar("caso 1: irmão vermelho, troca cores e rotaciona")
                    self._pintar(w, NEGRO)
                    self._pintar(x_pai, VERMELHO)
                    self._rotacionar_esquerda(x_pai)
                    w = exigir(x_pai.dir)
                if cor_de(w.esq) == NEGRO and cor_de(w.dir) == NEGRO:
                    self._registrar("caso 2: irmão negro e sobrinhos negros, sobe")
                    self._pintar(w, VERMELHO)
                    x = x_pai
                    x_pai = x.pai
                else:
                    if cor_de(w.dir) == NEGRO:
                        self._registrar("caso 3: sobrinho distante negro, rotaciona")
                        self._pintar(exigir(w.esq), NEGRO)
                        self._pintar(w, VERMELHO)
                        self._rotacionar_direita(w)
                        w = exigir(x_pai.dir)
                    self._registrar("caso 4: sobrinho distante vermelho, finaliza")
                    self._pintar(w, x_pai.cor)
                    self._pintar(x_pai, NEGRO)
                    self._pintar(exigir(w.dir), NEGRO)
                    self._rotacionar_esquerda(x_pai)
                    x = self._raiz
                    x_pai = None
            else:
                w = exigir(x_pai.esq)
                if w.cor == VERMELHO:
                    self._registrar("caso 1: irmão vermelho, troca cores e rotaciona")
                    self._pintar(w, NEGRO)
                    self._pintar(x_pai, VERMELHO)
                    self._rotacionar_direita(x_pai)
                    w = exigir(x_pai.esq)
                if cor_de(w.esq) == NEGRO and cor_de(w.dir) == NEGRO:
                    self._registrar("caso 2: irmão negro e sobrinhos negros, sobe")
                    self._pintar(w, VERMELHO)
                    x = x_pai
                    x_pai = x.pai
                else:
                    if cor_de(w.esq) == NEGRO:
                        self._registrar("caso 3: sobrinho distante negro, rotaciona")
                        self._pintar(exigir(w.dir), NEGRO)
                        self._pintar(w, VERMELHO)
                        self._rotacionar_esquerda(w)
                        w = exigir(x_pai.esq)
                    self._registrar("caso 4: sobrinho distante vermelho, finaliza")
                    self._pintar(w, x_pai.cor)
                    self._pintar(x_pai, NEGRO)
                    self._pintar(exigir(w.esq), NEGRO)
                    self._rotacionar_direita(x_pai)
                    x = self._raiz
                    x_pai = None
        if x is not None:
            self._pintar(x, NEGRO)

    def _rotacionar_esquerda(self, x: No) -> None:
        y = x.dir
        if y is None:
            raise ValueError("rotação à esquerda exige filho direito")
        self._registrar(f"rotação à esquerda em {rotulo(x.chave)}")
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
        self._registrar(f"rotação à direita em {rotulo(x.chave)}")
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
            raise RBInvalidaError(
                f"a raiz deve ser negra (raiz {self._raiz.chave} é vermelha)"
            )

        contados = 0

        def visitar(
            no: Optional[No], minimo: Optional[Chave], maximo: Optional[Chave]
        ) -> int:
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
                    raise RBInvalidaError(
                        f"ponteiro de pai inconsistente em {filho.chave}"
                    )
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
                f"tamanho registrado ({self._tamanho}) difere dos nós "
                f"alcançáveis ({contados})"
            )

    def esta_valida(self) -> bool:
        try:
            self.validar()
        except RBInvalidaError:
            return False
        return True
