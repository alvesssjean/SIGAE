"""Tabela Hash com encadeamento separado e tupla de sentinelas (ADR-001, ADR-002, ADR-010)."""

from __future__ import annotations

from typing import Any, Iterator, Optional

from core.lista_encadeada import ListaEncadeada


class HashInvalidaError(ValueError):
    """Exceção levantada quando alguma invariante da HashTable é violada."""


class NoHash:
    __slots__ = ("id", "valor", "proximo")

    def __init__(
        self,
        chave_id: int,
        valor: Any,
        proximo: Optional[NoHash] = None,
    ) -> None:
        self.id = chave_id
        self.valor = valor
        self.proximo = proximo


class Sentinela:
    __slots__ = ("proximo",)

    def __init__(self) -> None:
        self.proximo: Optional[NoHash] = None


class EstatisticasHash:
    __slots__ = (
        "capacidade",
        "tamanho",
        "fator_carga",
        "buckets_ocupados",
        "maior_cadeia",
        "total_colisoes",
        "buckets_com_colisao",
    )

    def __init__(
        self,
        capacidade: int,
        tamanho: int,
        fator_carga: float,
        buckets_ocupados: int,
        maior_cadeia: int,
        total_colisoes: int,
        buckets_com_colisao: ListaEncadeada,
    ) -> None:
        self.capacidade = capacidade
        self.tamanho = tamanho
        self.fator_carga = fator_carga
        self.buckets_ocupados = buckets_ocupados
        self.maior_cadeia = maior_cadeia
        self.total_colisoes = total_colisoes
        self.buckets_com_colisao = buckets_com_colisao


def _eh_primo(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def _proximo_primo(minimo: int) -> int:
    candidato = minimo if minimo >= 2 else 2
    if candidato > 2 and candidato % 2 == 0:
        candidato += 1
    while not _eh_primo(candidato):
        candidato += 2 if candidato > 2 else 1
    return candidato


class HashTable:
    """Tabela Hash indexada por ID inteiro usando tupla imutável de sentinelas."""

    def __init__(self, capacidade: int = 7, fator_maximo: float = 0.75) -> None:
        if capacidade < 1:
            raise ValueError("capacidade deve ser >= 1")
        self._capacidade: int = capacidade
        self._fator_maximo: float = fator_maximo
        self._buckets: tuple[Sentinela, ...] = tuple(
            Sentinela() for _ in range(capacidade)
        )
        self._tamanho: int = 0

    def _indice(self, chave_id: int) -> int:
        return chave_id % self._capacidade

    def _bucket(self, indice: int) -> Sentinela:
        return self._buckets[indice]

    def capacidade(self) -> int:
        return self._capacidade

    def tamanho(self) -> int:
        return self._tamanho

    def __len__(self) -> int:
        return self._tamanho

    def fator_carga(self) -> float:
        return self._tamanho / self._capacidade

    def inserir(self, chave_id: int, valor: Any) -> None:
        sentinela = self._bucket(self._indice(chave_id))
        atual = sentinela.proximo
        while atual is not None:
            if atual.id == chave_id:
                raise ValueError(f"chave duplicada: {chave_id}")
            atual = atual.proximo

        novo = NoHash(chave_id, valor, sentinela.proximo)
        sentinela.proximo = novo
        self._tamanho += 1

        if self.fator_carga() > self._fator_maximo:
            self.redimensionar()

    def atualizar(self, chave_id: int, valor: Any) -> None:
        sentinela = self._bucket(self._indice(chave_id))
        atual = sentinela.proximo
        while atual is not None:
            if atual.id == chave_id:
                atual.valor = valor
                return
            atual = atual.proximo
        raise KeyError(f"chave não encontrada: {chave_id}")

    def buscar(self, chave_id: int) -> Any:
        sentinela = self._bucket(self._indice(chave_id))
        atual = sentinela.proximo
        while atual is not None:
            if atual.id == chave_id:
                return atual.valor
            atual = atual.proximo
        return None

    def contem(self, chave_id: int) -> bool:
        sentinela = self._bucket(self._indice(chave_id))
        atual = sentinela.proximo
        while atual is not None:
            if atual.id == chave_id:
                return True
            atual = atual.proximo
        return False

    def __contains__(self, chave_id: int) -> bool:
        return self.contem(chave_id)

    def remover(self, chave_id: int) -> bool:
        sentinela = self._bucket(self._indice(chave_id))
        anterior: Any = sentinela
        atual = sentinela.proximo
        while atual is not None:
            if atual.id == chave_id:
                anterior.proximo = atual.proximo
                atual.proximo = None
                self._tamanho -= 1
                return True
            anterior = atual
            atual = atual.proximo
        return False

    def redimensionar(self, nova_capacidade: Optional[int] = None) -> None:
        if nova_capacidade is None:
            nova_capacidade = _proximo_primo(self._capacidade * 2)
        if nova_capacidade < 1:
            raise ValueError("nova capacidade deve ser >= 1")

        novos_buckets = tuple(Sentinela() for _ in range(nova_capacidade))
        for indice in range(self._capacidade):
            sentinela_antiga = self._bucket(indice)
            atual = sentinela_antiga.proximo
            sentinela_antiga.proximo = None
            while atual is not None:
                proximo = atual.proximo
                novo_indice = atual.id % nova_capacidade
                destino = novos_buckets[novo_indice]
                atual.proximo = destino.proximo
                destino.proximo = atual
                atual = proximo

        self._buckets = novos_buckets
        self._capacidade = nova_capacidade

    def ids(self) -> Iterator[int]:
        for indice in range(self._capacidade):
            atual = self._bucket(indice).proximo
            while atual is not None:
                yield atual.id
                atual = atual.proximo

    def valores(self) -> Iterator[Any]:
        for indice in range(self._capacidade):
            atual = self._bucket(indice).proximo
            while atual is not None:
                yield atual.valor
                atual = atual.proximo

    def itens(self) -> Iterator[tuple[int, Any]]:
        for indice in range(self._capacidade):
            atual = self._bucket(indice).proximo
            while atual is not None:
                yield (atual.id, atual.valor)
                atual = atual.proximo

    def estatisticas(self) -> EstatisticasHash:
        buckets_ocupados = 0
        maior_cadeia = 0
        total_colisoes = 0
        buckets_com_colisao = ListaEncadeada()

        for indice in range(self._capacidade):
            comprimento = 0
            atual = self._bucket(indice).proximo
            while atual is not None:
                comprimento += 1
                atual = atual.proximo
            if comprimento > 0:
                buckets_ocupados += 1
                if comprimento > maior_cadeia:
                    maior_cadeia = comprimento
                if comprimento > 1:
                    total_colisoes += comprimento - 1
                    buckets_com_colisao.anexar((indice, comprimento))

        return EstatisticasHash(
            capacidade=self._capacidade,
            tamanho=self._tamanho,
            fator_carga=self.fator_carga(),
            buckets_ocupados=buckets_ocupados,
            maior_cadeia=maior_cadeia,
            total_colisoes=total_colisoes,
            buckets_com_colisao=buckets_com_colisao,
        )

    def validar(self) -> None:
        contados = 0
        for indice in range(self._capacidade):
            atual = self._bucket(indice).proximo
            while atual is not None:
                contados += 1
                esperado = atual.id % self._capacidade
                if esperado != indice:
                    raise HashInvalidaError(
                        f"id {atual.id} no bucket {indice}, esperado {esperado}"
                    )
                outro = atual.proximo
                while outro is not None:
                    if outro.id == atual.id:
                        raise HashInvalidaError(
                            f"id duplicado {atual.id} no bucket {indice}"
                        )
                    outro = outro.proximo
                atual = atual.proximo

        if contados != self._tamanho:
            raise HashInvalidaError(
                f"tamanho registrado ({self._tamanho}) difere dos nós ({contados})"
            )
