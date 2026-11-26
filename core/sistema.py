"""Núcleo integrador do SIGAE WEB com rollback por compensações (ADR-003 a ADR-012)."""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional

from core.atendimento import (
    CANCELADO as ATENDIMENTO_CANCELADO,
    CONCLUIDO as ATENDIMENTO_CONCLUIDO,
    EM_ANDAMENTO,
    Atendimento,
)
from core.erros import (
    ErroValidacao,
    EstadoInvalido,
    FilaVazia,
    NaoEncontrado,
    SemMedicoDisponivel,
)
from core.hash_table import EstatisticasHash, HashTable
from core.heap import MinHeap
from core.lista_encadeada import ListaEncadeada
from core.medico import (
    DISPONIVEL as MEDICO_DISPONIVEL,
    EM_ATENDIMENTO as MEDICO_EM_ATENDIMENTO,
    Medico,
)
from core.paciente import (
    AGUARDANDO,
    CANCELADO as PACIENTE_CANCELADO,
    CONCLUIDO as PACIENTE_CONCLUIDO,
    EM_ATENDIMENTO as PACIENTE_EM_ATENDIMENTO,
    Paciente,
    validar_prioridade,
)
from core.rbtree import RBTree
from core.relogio import agora_local
from core.repositorio import Repositorio, RepositorioMemoria


class Indicadores:
    """Resumo quantitativo de pacientes, médicos e atendimentos."""

    def __init__(
        self,
        aguardando: int,
        em_atendimento: int,
        concluidos: int,
        cancelados: int,
        medicos_disponiveis: int,
        medicos_em_atendimento: int,
        atendimentos_ativos: int,
        atendimentos_concluidos: int,
        atendimentos_cancelados: int,
        medicos: ListaEncadeada,
    ) -> None:
        self.aguardando = aguardando
        self.em_atendimento = em_atendimento
        self.concluidos = concluidos
        self.cancelados = cancelados
        self.total_pacientes = aguardando + em_atendimento + concluidos + cancelados
        self.medicos_disponiveis = medicos_disponiveis
        self.medicos_em_atendimento = medicos_em_atendimento
        self.total_medicos = medicos_disponiveis + medicos_em_atendimento
        self.atendimentos_ativos = atendimentos_ativos
        self.atendimentos_concluidos = atendimentos_concluidos
        self.atendimentos_cancelados = atendimentos_cancelados
        self.medicos = medicos


class RelatorioConsistencia:
    """Resultado da validação cruzada de todos os índices do núcleo."""

    def __init__(
        self,
        ok: bool,
        erros: ListaEncadeada,
        total_aguardando: int,
        total_medicos_disponiveis: int,
        total_atendimentos_ativos: int,
    ) -> None:
        self.ok = ok
        self.erros = erros
        self.total_aguardando = total_aguardando
        self.total_medicos_disponiveis = total_medicos_disponiveis
        self.total_atendimentos_ativos = total_atendimentos_ativos
        if ok:
            self.resumo = (
                f"Índices consistentes: {total_aguardando} aguardando, "
                f"{total_medicos_disponiveis} médicos disponíveis, "
                f"{total_atendimentos_ativos} atendimentos ativos."
            )
        else:
            self.resumo = f"Inconsistências encontradas ({len(erros)})."


class DiagnosticoSistema:
    """Estado interno das estruturas para a tela de diagnóstico e defesa."""

    def __init__(
        self,
        hash_pacientes: EstatisticasHash,
        hash_medicos: EstatisticasHash,
        hash_atendimentos: EstatisticasHash,
        rb_espera_valida: bool,
        rb_espera_altura: int,
        rb_espera_tamanho: int,
        rb_historico_valida: bool,
        rb_historico_altura: int,
        rb_historico_tamanho: int,
        heap_pacientes_tamanho: int,
        heap_pacientes_raiz: Optional[Paciente],
        heap_medicos_tamanho: int,
        heap_medicos_raiz: Optional[Medico],
        consistencia: RelatorioConsistencia,
        ultimo_paciente_id: int,
        ultimo_medico_id: int,
        ultimo_atendimento_id: int,
        relogio_logico: int,
    ) -> None:
        self.hash_pacientes = hash_pacientes
        self.hash_medicos = hash_medicos
        self.hash_atendimentos = hash_atendimentos
        self.rb_espera_valida = rb_espera_valida
        self.rb_espera_altura = rb_espera_altura
        self.rb_espera_tamanho = rb_espera_tamanho
        self.rb_historico_valida = rb_historico_valida
        self.rb_historico_altura = rb_historico_altura
        self.rb_historico_tamanho = rb_historico_tamanho
        self.heap_pacientes_tamanho = heap_pacientes_tamanho
        self.heap_pacientes_raiz = heap_pacientes_raiz
        self.heap_medicos_tamanho = heap_medicos_tamanho
        self.heap_medicos_raiz = heap_medicos_raiz
        self.consistencia = consistencia
        self.ultimo_paciente_id = ultimo_paciente_id
        self.ultimo_medico_id = ultimo_medico_id
        self.ultimo_atendimento_id = ultimo_atendimento_id
        self.relogio_logico = relogio_logico


def _chave_paciente(paciente: Paciente) -> tuple[int, int, str, int]:
    return paciente.chave_heap()


def _id_entidade(entidade: Any) -> int:
    return entidade.id


def _chave_medico(medico: Medico) -> tuple[int, int, int]:
    return medico.chave_heap()


def _executar_compensacoes(pilha: ListaEncadeada) -> None:
    while pilha:
        compensacao = pilha.remover_inicio()
        compensacao()


class Sistema:
    """Fachada única do domínio SIGAE integrando Hash, RB-Tree, Heaps e Repositório."""

    def __init__(
        self,
        repositorio: Optional[Repositorio] = None,
        relogio: Callable[..., str] = agora_local,
    ) -> None:
        self._repositorio: Repositorio = repositorio or RepositorioMemoria()
        self._relogio: Callable[..., str] = relogio
        self._lock: threading.Lock = threading.Lock()

        self._ultimo_paciente_id: int = 0
        self._ultimo_medico_id: int = 0
        self._ultimo_atendimento_id: int = 0
        self._relogio_logico: int = 0

        self._hash_pacientes: HashTable = HashTable()
        self._hash_medicos: HashTable = HashTable()
        self._hash_atendimentos: HashTable = HashTable()

        self._rb_espera: RBTree = RBTree()
        self._rb_historico: RBTree = RBTree()

        self._heap_pacientes: MinHeap = MinHeap(_chave_paciente, _id_entidade)
        self._heap_medicos: MinHeap = MinHeap(_chave_medico, _id_entidade)

        self._cont_aguardando: int = 0
        self._cont_em_atendimento: int = 0
        self._cont_concluidos: int = 0
        self._cont_cancelados: int = 0

    @classmethod
    def carregar(
        cls,
        repositorio: Repositorio,
        relogio: Callable[..., str] = agora_local,
    ) -> Sistema:
        sistema = cls(repositorio=repositorio, relogio=relogio)
        dados = repositorio.carregar_tudo()

        sistema._ultimo_paciente_id = dados.ultimo_paciente_id
        sistema._ultimo_medico_id = dados.ultimo_medico_id
        sistema._ultimo_atendimento_id = dados.ultimo_atendimento_id
        sistema._relogio_logico = dados.relogio_logico

        for paciente in dados.pacientes:
            if paciente.id > sistema._ultimo_paciente_id:
                sistema._ultimo_paciente_id = paciente.id
            sistema._hash_pacientes.inserir(paciente.id, paciente)
            sistema._rb_historico.inserir(paciente.chave_rb(), paciente)
            if paciente.situacao == AGUARDANDO:
                sistema._cont_aguardando += 1
                sistema._rb_espera.inserir(paciente.chave_rb(), paciente)
                sistema._heap_pacientes.inserir(paciente)
            elif paciente.situacao == PACIENTE_EM_ATENDIMENTO:
                sistema._cont_em_atendimento += 1
            elif paciente.situacao == PACIENTE_CONCLUIDO:
                sistema._cont_concluidos += 1
            elif paciente.situacao == PACIENTE_CANCELADO:
                sistema._cont_cancelados += 1

        for medico in dados.medicos:
            if medico.id > sistema._ultimo_medico_id:
                sistema._ultimo_medico_id = medico.id
            if medico.seq_ultima_atribuicao > sistema._relogio_logico:
                sistema._relogio_logico = medico.seq_ultima_atribuicao
            sistema._hash_medicos.inserir(medico.id, medico)
            if medico.situacao == MEDICO_DISPONIVEL:
                sistema._heap_medicos.inserir(medico)

        for atendimento in dados.atendimentos:
            if atendimento.id > sistema._ultimo_atendimento_id:
                sistema._ultimo_atendimento_id = atendimento.id
            sistema._hash_atendimentos.inserir(atendimento.id, atendimento)
            if atendimento.status == ATENDIMENTO_CANCELADO:
                paciente = sistema._hash_pacientes.buscar(atendimento.paciente_id)
                if paciente is not None and not paciente.medicos_que_cancelaram.contem(
                    atendimento.medico_id
                ):
                    paciente.medicos_que_cancelaram.anexar(atendimento.medico_id)

        return sistema

    def _salvar_contadores(self) -> None:
        self._repositorio.salvar_contadores(
            self._ultimo_paciente_id,
            self._ultimo_medico_id,
            self._ultimo_atendimento_id,
            self._relogio_logico,
        )

    def cadastrar_paciente(self, nome: str, prioridade: int) -> Paciente:
        with self._lock:
            if not isinstance(nome, str) or not nome.strip():
                raise ErroValidacao("nome do paciente é obrigatório")
            validar_prioridade(prioridade)

            id_anterior = self._ultimo_paciente_id
            novo_id = id_anterior + 1
            horario = self._relogio()
            paciente = Paciente(novo_id, nome, horario, prioridade)

            desfazer = ListaEncadeada()
            try:
                self._ultimo_paciente_id = novo_id
                desfazer.inserir_inicio(
                    lambda: setattr(self, "_ultimo_paciente_id", id_anterior)
                )

                self._hash_pacientes.inserir(paciente.id, paciente)
                desfazer.inserir_inicio(
                    lambda: self._hash_pacientes.remover(paciente.id)
                )

                self._rb_espera.inserir(paciente.chave_rb(), paciente)
                desfazer.inserir_inicio(
                    lambda: self._rb_espera.remover(paciente.chave_rb())
                )

                self._rb_historico.inserir(paciente.chave_rb(), paciente)
                desfazer.inserir_inicio(
                    lambda: self._rb_historico.remover(paciente.chave_rb())
                )

                self._heap_pacientes.inserir(paciente)
                desfazer.inserir_inicio(
                    lambda: self._heap_pacientes.remover(paciente.id)
                )

                self._cont_aguardando += 1
                desfazer.inserir_inicio(
                    lambda: setattr(
                        self, "_cont_aguardando", self._cont_aguardando - 1
                    )
                )

                with self._repositorio.transacao():
                    self._repositorio.salvar_paciente(paciente)
                    self._salvar_contadores()
            except Exception:
                _executar_compensacoes(desfazer)
                raise

            return paciente

    def consultar_paciente(self, paciente_id: int) -> Paciente:
        with self._lock:
            paciente = self._hash_pacientes.buscar(paciente_id)
            if paciente is None:
                raise NaoEncontrado(f"paciente {paciente_id} não encontrado")
            return paciente

    def listar_pacientes(self) -> ListaEncadeada:
        with self._lock:
            resultado = ListaEncadeada()
            for paciente_id in range(1, self._ultimo_paciente_id + 1):
                paciente = self._hash_pacientes.buscar(paciente_id)
                if paciente is not None:
                    resultado.anexar(paciente)
            return resultado

    def reclassificar(self, paciente_id: int, nova_prioridade: int) -> Paciente:
        with self._lock:
            validar_prioridade(nova_prioridade)
            paciente = self._hash_pacientes.buscar(paciente_id)
            if paciente is None:
                raise NaoEncontrado(f"paciente {paciente_id} não encontrado")
            if paciente.situacao != AGUARDANDO:
                raise EstadoInvalido(
                    "só é permitido reclassificar paciente com situação Aguardando"
                )
            if paciente.prioridade == nova_prioridade:
                return paciente

            prioridade_anterior = paciente.prioridade
            desfazer = ListaEncadeada()
            try:
                paciente.prioridade = nova_prioridade
                desfazer.inserir_inicio(
                    lambda: setattr(paciente, "prioridade", prioridade_anterior)
                )

                self._heap_pacientes.alterar_prioridade(paciente.id)
                desfazer.inserir_inicio(
                    lambda: self._reverter_prioridade_heap(
                        paciente, prioridade_anterior
                    )
                )

                with self._repositorio.transacao():
                    self._repositorio.salvar_paciente(paciente)
            except Exception:
                _executar_compensacoes(desfazer)
                raise

            return paciente

    def _reverter_prioridade_heap(
        self, paciente: Paciente, prioridade_anterior: int
    ) -> None:
        paciente.prioridade = prioridade_anterior
        self._heap_pacientes.alterar_prioridade(paciente.id)

    def _buscar_atendimento_ativo_do_paciente(
        self, paciente_id: int
    ) -> Optional[Atendimento]:
        for atendimento_id in range(1, self._ultimo_atendimento_id + 1):
            atendimento = self._hash_atendimentos.buscar(atendimento_id)
            if (
                atendimento is not None
                and atendimento.paciente_id == paciente_id
                and atendimento.status == EM_ANDAMENTO
            ):
                return atendimento
        return None

    def cancelar_paciente(self, paciente_id: int) -> Paciente:
        with self._lock:
            paciente = self._hash_pacientes.buscar(paciente_id)
            if paciente is None:
                raise NaoEncontrado(f"paciente {paciente_id} não encontrado")

            if paciente.situacao == PACIENTE_EM_ATENDIMENTO:
                atendimento = self._buscar_atendimento_ativo_do_paciente(paciente_id)
                if atendimento is None:
                    raise EstadoInvalido(
                        "paciente em atendimento sem registro de atendimento ativo"
                    )
                self._cancelar_atendimento_interno(atendimento.id)
                return paciente

            if paciente.situacao != AGUARDANDO:
                raise EstadoInvalido(
                    "não é possível cancelar paciente já concluído ou cancelado"
                )

            situacao_anterior = paciente.situacao
            retorno_anterior = paciente.retorno
            desfazer = ListaEncadeada()
            try:
                self._heap_pacientes.remover(paciente.id)
                desfazer.inserir_inicio(
                    lambda: self._heap_pacientes.inserir(paciente)
                )

                self._rb_espera.remover(paciente.chave_rb())
                desfazer.inserir_inicio(
                    lambda: self._rb_espera.inserir(paciente.chave_rb(), paciente)
                )

                paciente.situacao = PACIENTE_CANCELADO
                paciente.retorno = False
                desfazer.inserir_inicio(
                    lambda: self._restaurar_estado_paciente(
                        paciente, situacao_anterior, retorno_anterior
                    )
                )

                self._cont_aguardando -= 1
                self._cont_cancelados += 1
                desfazer.inserir_inicio(self._desfazer_cont_cancelamento_espera)

                with self._repositorio.transacao():
                    self._repositorio.salvar_paciente(paciente)
            except Exception:
                _executar_compensacoes(desfazer)
                raise

            return paciente

    def _restaurar_estado_paciente(
        self, paciente: Paciente, situacao: str, retorno: bool
    ) -> None:
        paciente.situacao = situacao
        paciente.retorno = retorno

    def _restaurar_estado_medico(
        self, medico: Medico, situacao: str, concluidos: int, seq: int
    ) -> None:
        medico.situacao = situacao
        medico.concluidos = concluidos
        medico.seq_ultima_atribuicao = seq

    def _restaurar_atendimento(
        self, atendimento: Atendimento, status: str, fim: Optional[str]
    ) -> None:
        atendimento.status = status
        atendimento.fim = fim

    def _desfazer_cont_cancelamento_espera(self) -> None:
        self._cont_aguardando += 1
        self._cont_cancelados -= 1

    def _desfazer_cont_chamada(self) -> None:
        self._cont_aguardando += 1
        self._cont_em_atendimento -= 1

    def _desfazer_cont_conclusao(self) -> None:
        self._cont_em_atendimento += 1
        self._cont_concluidos -= 1

    def _desfazer_cont_cancelamento_atendimento(self) -> None:
        self._cont_em_atendimento += 1
        self._cont_aguardando -= 1

    def listar_fila_chegada(self) -> ListaEncadeada:
        with self._lock:
            resultado = ListaEncadeada()
            for _, paciente in self._rb_espera.em_ordem():
                resultado.anexar(paciente)
            return resultado

    def listar_fila_prioridade(self) -> ListaEncadeada:
        with self._lock:
            auxiliar = MinHeap(_chave_paciente, _id_entidade)
            for paciente in self._heap_pacientes.itens():
                auxiliar.inserir(paciente)
            resultado = ListaEncadeada()
            while auxiliar.tamanho() > 0:
                resultado.anexar(auxiliar.extrair_minimo())
            return resultado

    def proximo_paciente(self) -> Optional[Paciente]:
        with self._lock:
            return self._heap_pacientes.raiz()

    def cadastrar_medico(self, nome: str, registro: str) -> Medico:
        with self._lock:
            id_anterior = self._ultimo_medico_id
            novo_id = id_anterior + 1
            medico = Medico(novo_id, nome, registro)

            desfazer = ListaEncadeada()
            try:
                self._ultimo_medico_id = novo_id
                desfazer.inserir_inicio(
                    lambda: setattr(self, "_ultimo_medico_id", id_anterior)
                )

                self._hash_medicos.inserir(medico.id, medico)
                desfazer.inserir_inicio(
                    lambda: self._hash_medicos.remover(medico.id)
                )

                self._heap_medicos.inserir(medico)
                desfazer.inserir_inicio(
                    lambda: self._heap_medicos.remover(medico.id)
                )

                with self._repositorio.transacao():
                    self._repositorio.salvar_medico(medico)
                    self._salvar_contadores()
            except Exception:
                _executar_compensacoes(desfazer)
                raise

            return medico

    def consultar_medico(self, medico_id: int) -> Medico:
        with self._lock:
            medico = self._hash_medicos.buscar(medico_id)
            if medico is None:
                raise NaoEncontrado(f"médico {medico_id} não encontrado")
            return medico

    def listar_medicos(self) -> ListaEncadeada:
        with self._lock:
            resultado = ListaEncadeada()
            for medico_id in range(1, self._ultimo_medico_id + 1):
                medico = self._hash_medicos.buscar(medico_id)
                if medico is not None:
                    resultado.anexar(medico)
            return resultado

    def chamar_proximo(self) -> Atendimento:
        with self._lock:
            if self._heap_pacientes.tamanho() == 0:
                raise FilaVazia("não há pacientes aguardando na fila")
            if self._heap_medicos.tamanho() == 0:
                raise SemMedicoDisponivel("não há médicos disponíveis para chamada")

            desfazer = ListaEncadeada()
            try:
                paciente: Paciente = self._heap_pacientes.extrair_minimo()
                desfazer.inserir_inicio(
                    lambda: self._heap_pacientes.inserir(paciente)
                )

                self._rb_espera.remover(paciente.chave_rb())
                desfazer.inserir_inicio(
                    lambda: self._rb_espera.inserir(paciente.chave_rb(), paciente)
                )

                medico: Medico = self._heap_medicos.extrair_minimo()
                desfazer.inserir_inicio(
                    lambda: self._heap_medicos.inserir(medico)
                )

                relogio_anterior = self._relogio_logico
                self._relogio_logico = relogio_anterior + 1
                desfazer.inserir_inicio(
                    lambda: setattr(self, "_relogio_logico", relogio_anterior)
                )

                med_sit_ant = medico.situacao
                med_conc_ant = medico.concluidos
                med_seq_ant = medico.seq_ultima_atribuicao
                medico.seq_ultima_atribuicao = self._relogio_logico
                medico.situacao = MEDICO_EM_ATENDIMENTO
                desfazer.inserir_inicio(
                    lambda: self._restaurar_estado_medico(
                        medico, med_sit_ant, med_conc_ant, med_seq_ant
                    )
                )

                pac_sit_ant = paciente.situacao
                pac_ret_ant = paciente.retorno
                paciente.situacao = PACIENTE_EM_ATENDIMENTO
                paciente.retorno = False
                desfazer.inserir_inicio(
                    lambda: self._restaurar_estado_paciente(
                        paciente, pac_sit_ant, pac_ret_ant
                    )
                )

                self._cont_aguardando -= 1
                self._cont_em_atendimento += 1
                desfazer.inserir_inicio(self._desfazer_cont_chamada)

                atend_id_ant = self._ultimo_atendimento_id
                novo_atend_id = atend_id_ant + 1
                atendimento = Atendimento(
                    novo_atend_id, paciente.id, medico.id, self._relogio()
                )
                self._ultimo_atendimento_id = novo_atend_id
                desfazer.inserir_inicio(
                    lambda: setattr(self, "_ultimo_atendimento_id", atend_id_ant)
                )

                self._hash_atendimentos.inserir(atendimento.id, atendimento)
                desfazer.inserir_inicio(
                    lambda: self._hash_atendimentos.remover(atendimento.id)
                )

                with self._repositorio.transacao():
                    self._repositorio.salvar_paciente(paciente)
                    self._repositorio.salvar_medico(medico)
                    self._repositorio.salvar_atendimento(atendimento)
                    self._salvar_contadores()
            except Exception:
                _executar_compensacoes(desfazer)
                raise

            return atendimento

    def concluir_atendimento(self, atendimento_id: int) -> Atendimento:
        with self._lock:
            atendimento = self._hash_atendimentos.buscar(atendimento_id)
            if atendimento is None:
                raise NaoEncontrado(f"atendimento {atendimento_id} não encontrado")
            if atendimento.status != EM_ANDAMENTO:
                raise EstadoInvalido(
                    "só é possível concluir atendimento com status Em andamento"
                )

            paciente = self._hash_pacientes.buscar(atendimento.paciente_id)
            medico = self._hash_medicos.buscar(atendimento.medico_id)
            if paciente is None or medico is None:
                raise EstadoInvalido("atendimento referencia registro inexistente")

            status_ant = atendimento.status
            fim_ant = atendimento.fim
            pac_sit_ant = paciente.situacao
            pac_ret_ant = paciente.retorno
            med_sit_ant = medico.situacao
            med_conc_ant = medico.concluidos
            med_seq_ant = medico.seq_ultima_atribuicao

            desfazer = ListaEncadeada()
            try:
                atendimento.status = ATENDIMENTO_CONCLUIDO
                atendimento.fim = self._relogio()
                desfazer.inserir_inicio(
                    lambda: self._restaurar_atendimento(
                        atendimento, status_ant, fim_ant
                    )
                )

                paciente.situacao = PACIENTE_CONCLUIDO
                desfazer.inserir_inicio(
                    lambda: self._restaurar_estado_paciente(
                        paciente, pac_sit_ant, pac_ret_ant
                    )
                )

                self._cont_em_atendimento -= 1
                self._cont_concluidos += 1
                desfazer.inserir_inicio(self._desfazer_cont_conclusao)

                medico.concluidos += 1
                medico.situacao = MEDICO_DISPONIVEL
                desfazer.inserir_inicio(
                    lambda: self._restaurar_estado_medico(
                        medico, med_sit_ant, med_conc_ant, med_seq_ant
                    )
                )

                self._heap_medicos.inserir(medico)
                desfazer.inserir_inicio(
                    lambda: self._heap_medicos.remover(medico.id)
                )

                with self._repositorio.transacao():
                    self._repositorio.salvar_atendimento(atendimento)
                    self._repositorio.salvar_paciente(paciente)
                    self._repositorio.salvar_medico(medico)
            except Exception:
                _executar_compensacoes(desfazer)
                raise

            return atendimento

    def cancelar_atendimento(self, atendimento_id: int) -> Atendimento:
        with self._lock:
            return self._cancelar_atendimento_interno(atendimento_id)

    def _cancelar_atendimento_interno(self, atendimento_id: int) -> Atendimento:
        atendimento = self._hash_atendimentos.buscar(atendimento_id)
        if atendimento is None:
            raise NaoEncontrado(f"atendimento {atendimento_id} não encontrado")
        if atendimento.status != EM_ANDAMENTO:
            raise EstadoInvalido(
                "só é possível cancelar atendimento com status Em andamento"
            )

        paciente = self._hash_pacientes.buscar(atendimento.paciente_id)
        medico = self._hash_medicos.buscar(atendimento.medico_id)
        if paciente is None or medico is None:
            raise EstadoInvalido("atendimento referencia registro inexistente")

        if paciente.medicos_que_cancelaram.contem(medico.id):
            raise EstadoInvalido(
                "este médico já cancelou o atendimento deste paciente"
            )

        status_ant = atendimento.status
        fim_ant = atendimento.fim
        pac_sit_ant = paciente.situacao
        pac_ret_ant = paciente.retorno
        med_sit_ant = medico.situacao
        med_conc_ant = medico.concluidos
        med_seq_ant = medico.seq_ultima_atribuicao

        desfazer = ListaEncadeada()
        try:
            atendimento.status = ATENDIMENTO_CANCELADO
            atendimento.fim = self._relogio()
            desfazer.inserir_inicio(
                lambda: self._restaurar_atendimento(atendimento, status_ant, fim_ant)
            )

            paciente.situacao = AGUARDANDO
            paciente.retorno = True
            desfazer.inserir_inicio(
                lambda: self._restaurar_estado_paciente(
                    paciente, pac_sit_ant, pac_ret_ant
                )
            )

            paciente.medicos_que_cancelaram.anexar(medico.id)
            desfazer.inserir_inicio(
                lambda: paciente.medicos_que_cancelaram.remover_valor(medico.id)
            )

            self._cont_em_atendimento -= 1
            self._cont_aguardando += 1
            desfazer.inserir_inicio(self._desfazer_cont_cancelamento_atendimento)

            self._rb_espera.inserir(paciente.chave_rb(), paciente)
            desfazer.inserir_inicio(
                lambda: self._rb_espera.remover(paciente.chave_rb())
            )

            self._heap_pacientes.inserir(paciente)
            desfazer.inserir_inicio(
                lambda: self._heap_pacientes.remover(paciente.id)
            )

            medico.situacao = MEDICO_DISPONIVEL
            desfazer.inserir_inicio(
                lambda: self._restaurar_estado_medico(
                    medico, med_sit_ant, med_conc_ant, med_seq_ant
                )
            )

            self._heap_medicos.inserir(medico)
            desfazer.inserir_inicio(
                lambda: self._heap_medicos.remover(medico.id)
            )

            with self._repositorio.transacao():
                self._repositorio.salvar_atendimento(atendimento)
                self._repositorio.salvar_paciente(paciente)
                self._repositorio.salvar_medico(medico)
        except Exception:
            _executar_compensacoes(desfazer)
            raise

        return atendimento

    def listar_atendimentos_ativos(self) -> ListaEncadeada:
        with self._lock:
            resultado = ListaEncadeada()
            for atendimento_id in range(1, self._ultimo_atendimento_id + 1):
                atendimento = self._hash_atendimentos.buscar(atendimento_id)
                if atendimento is not None and atendimento.status == EM_ANDAMENTO:
                    resultado.anexar(atendimento)
            return resultado

    def historico_atendimentos(self) -> ListaEncadeada:
        with self._lock:
            resultado = ListaEncadeada()
            for atendimento_id in range(1, self._ultimo_atendimento_id + 1):
                atendimento = self._hash_atendimentos.buscar(atendimento_id)
                if atendimento is not None and atendimento.status != EM_ANDAMENTO:
                    resultado.anexar(atendimento)
            return resultado

    def listar_historico_chegadas(self) -> ListaEncadeada:
        with self._lock:
            resultado = ListaEncadeada()
            for _, paciente in self._rb_historico.em_ordem():
                resultado.anexar(paciente)
            return resultado

    def indicadores(self) -> Indicadores:
        with self._lock:
            medicos = ListaEncadeada()
            medicos_disponiveis = 0
            medicos_em_atendimento = 0
            for medico_id in range(1, self._ultimo_medico_id + 1):
                medico = self._hash_medicos.buscar(medico_id)
                if medico is not None:
                    medicos.anexar(medico)
                    if medico.situacao == MEDICO_DISPONIVEL:
                        medicos_disponiveis += 1
                    else:
                        medicos_em_atendimento += 1

            atend_ativos = 0
            atend_concluidos = 0
            atend_cancelados = 0
            for atendimento_id in range(1, self._ultimo_atendimento_id + 1):
                atendimento = self._hash_atendimentos.buscar(atendimento_id)
                if atendimento is not None:
                    if atendimento.status == EM_ANDAMENTO:
                        atend_ativos += 1
                    elif atendimento.status == ATENDIMENTO_CONCLUIDO:
                        atend_concluidos += 1
                    else:
                        atend_cancelados += 1

            return Indicadores(
                aguardando=self._cont_aguardando,
                em_atendimento=self._cont_em_atendimento,
                concluidos=self._cont_concluidos,
                cancelados=self._cont_cancelados,
                medicos_disponiveis=medicos_disponiveis,
                medicos_em_atendimento=medicos_em_atendimento,
                atendimentos_ativos=atend_ativos,
                atendimentos_concluidos=atend_concluidos,
                atendimentos_cancelados=atend_cancelados,
                medicos=medicos,
            )

    def _validar_indices_interno(self) -> RelatorioConsistencia:
        erros = ListaEncadeada()

        for nome, estrutura in (
            ("hash_pacientes", self._hash_pacientes),
            ("hash_medicos", self._hash_medicos),
            ("hash_atendimentos", self._hash_atendimentos),
            ("rb_espera", self._rb_espera),
            ("rb_historico", self._rb_historico),
            ("heap_pacientes", self._heap_pacientes),
            ("heap_medicos", self._heap_medicos),
        ):
            try:
                estrutura.validar()
            except Exception as exc:
                erros.anexar(f"{nome} inválida: {exc}")

        cont_aguardando = 0
        cont_em_atendimento = 0
        cont_concluidos = 0
        cont_cancelados = 0

        for paciente in self._hash_pacientes.valores():
            if not (paciente.chave_rb() in self._rb_historico):
                erros.anexar(f"paciente {paciente.id} ausente na RB histórico")
            if paciente.situacao == AGUARDANDO:
                cont_aguardando += 1
                if not (paciente.chave_rb() in self._rb_espera):
                    erros.anexar(f"paciente {paciente.id} Aguardando ausente na RB espera")
                if not self._heap_pacientes.contem(paciente.id):
                    erros.anexar(f"paciente {paciente.id} Aguardando ausente no Heap")
            else:
                if paciente.retorno:
                    erros.anexar(
                        f"paciente {paciente.id} tem retorno=True mas está {paciente.situacao}"
                    )
                if paciente.chave_rb() in self._rb_espera:
                    erros.anexar(
                        f"paciente {paciente.id} ({paciente.situacao}) ainda está na RB espera"
                    )
                if self._heap_pacientes.contem(paciente.id):
                    erros.anexar(
                        f"paciente {paciente.id} ({paciente.situacao}) ainda está no Heap"
                    )
                if paciente.situacao == PACIENTE_EM_ATENDIMENTO:
                    cont_em_atendimento += 1
                elif paciente.situacao == PACIENTE_CONCLUIDO:
                    cont_concluidos += 1
                elif paciente.situacao == PACIENTE_CANCELADO:
                    cont_cancelados += 1

        if cont_aguardando != self._cont_aguardando:
            erros.anexar("contador aguardando diverge da Hash")
        if cont_em_atendimento != self._cont_em_atendimento:
            erros.anexar("contador em_atendimento diverge da Hash")
        if cont_concluidos != self._cont_concluidos:
            erros.anexar("contador concluidos diverge da Hash")
        if cont_cancelados != self._cont_cancelados:
            erros.anexar("contador cancelados diverge da Hash")

        if len(self._rb_espera) != cont_aguardando:
            erros.anexar("tamanho da RB espera diverge de pacientes Aguardando")
        if self._heap_pacientes.tamanho() != cont_aguardando:
            erros.anexar("tamanho do Heap de pacientes diverge de pacientes Aguardando")
        if len(self._rb_historico) != self._hash_pacientes.tamanho():
            erros.anexar("tamanho da RB histórico diverge da Hash de pacientes")

        for _, paciente in self._rb_espera.em_ordem():
            if not self._heap_pacientes.contem(paciente.id):
                erros.anexar(f"paciente {paciente.id} na RB espera mas ausente no Heap")
            encontrado = self._hash_pacientes.buscar(paciente.id)
            if encontrado is not paciente or encontrado.situacao != AGUARDANDO:
                erros.anexar(f"paciente {paciente.id} inconsistente entre RB espera e Hash")

        cont_med_disp = 0
        cont_med_atend = 0
        for medico in self._hash_medicos.valores():
            if medico.situacao == MEDICO_DISPONIVEL:
                cont_med_disp += 1
                if not self._heap_medicos.contem(medico.id):
                    erros.anexar(f"médico {medico.id} Disponível ausente no Heap")
            else:
                cont_med_atend += 1
                if self._heap_medicos.contem(medico.id):
                    erros.anexar(f"médico {medico.id} Em atendimento ainda está no Heap")

        if self._heap_medicos.tamanho() != cont_med_disp:
            erros.anexar("tamanho do Heap de médicos diverge dos médicos Disponível")

        ativos_por_paciente = HashTable()
        ativos_por_medico = HashTable()
        total_ativos = 0

        for atendimento in self._hash_atendimentos.valores():
            paciente = self._hash_pacientes.buscar(atendimento.paciente_id)
            medico = self._hash_medicos.buscar(atendimento.medico_id)
            if paciente is None:
                erros.anexar(f"atendimento {atendimento.id} com paciente inexistente")
                continue
            if medico is None:
                erros.anexar(f"atendimento {atendimento.id} com médico inexistente")
                continue

            if atendimento.status == EM_ANDAMENTO:
                total_ativos += 1
                if paciente.situacao != PACIENTE_EM_ATENDIMENTO:
                    erros.anexar(
                        f"atendimento ativo {atendimento.id} com paciente {paciente.id} em {paciente.situacao}"
                    )
                if medico.situacao != MEDICO_EM_ATENDIMENTO:
                    erros.anexar(
                        f"atendimento ativo {atendimento.id} com médico {medico.id} em {medico.situacao}"
                    )
                if ativos_por_paciente.contem(paciente.id):
                    erros.anexar(f"paciente {paciente.id} com mais de um atendimento ativo")
                else:
                    ativos_por_paciente.inserir(paciente.id, atendimento.id)
                if ativos_por_medico.contem(medico.id):
                    erros.anexar(f"médico {medico.id} com mais de um atendimento ativo")
                else:
                    ativos_por_medico.inserir(medico.id, atendimento.id)
            elif atendimento.status == ATENDIMENTO_CANCELADO:
                if not paciente.medicos_que_cancelaram.contem(medico.id):
                    erros.anexar(
                        f"atendimento cancelado {atendimento.id} ausente em medicos_que_cancelaram do paciente {paciente.id}"
                    )

        if total_ativos != cont_em_atendimento:
            erros.anexar("quantidade de atendimentos ativos diverge de pacientes Em atendimento")
        if total_ativos != cont_med_atend:
            erros.anexar("quantidade de atendimentos ativos diverge de médicos Em atendimento")

        for paciente in self._hash_pacientes.valores():
            for medico_id in paciente.medicos_que_cancelaram:
                achou = False
                for atendimento in self._hash_atendimentos.valores():
                    if (
                        atendimento.status == ATENDIMENTO_CANCELADO
                        and atendimento.paciente_id == paciente.id
                        and atendimento.medico_id == medico_id
                    ):
                        achou = True
                        break
                if not achou:
                    erros.anexar(
                        f"médico {medico_id} listado em medicos_que_cancelaram do paciente {paciente.id} sem atendimento cancelado"
                    )

        return RelatorioConsistencia(
            ok=len(erros) == 0,
            erros=erros,
            total_aguardando=cont_aguardando,
            total_medicos_disponiveis=cont_med_disp,
            total_atendimentos_ativos=total_ativos,
        )

    def validar_indices(self) -> RelatorioConsistencia:
        with self._lock:
            return self._validar_indices_interno()

    def diagnostico(self) -> DiagnosticoSistema:
        with self._lock:
            consistencia = self._validar_indices_interno()
            return DiagnosticoSistema(
                hash_pacientes=self._hash_pacientes.estatisticas(),
                hash_medicos=self._hash_medicos.estatisticas(),
                hash_atendimentos=self._hash_atendimentos.estatisticas(),
                rb_espera_valida=self._rb_espera.esta_valida(),
                rb_espera_altura=self._rb_espera.altura(),
                rb_espera_tamanho=len(self._rb_espera),
                rb_historico_valida=self._rb_historico.esta_valida(),
                rb_historico_altura=self._rb_historico.altura(),
                rb_historico_tamanho=len(self._rb_historico),
                heap_pacientes_tamanho=self._heap_pacientes.tamanho(),
                heap_pacientes_raiz=self._heap_pacientes.raiz(),
                heap_medicos_tamanho=self._heap_medicos.tamanho(),
                heap_medicos_raiz=self._heap_medicos.raiz(),
                consistencia=consistencia,
                ultimo_paciente_id=self._ultimo_paciente_id,
                ultimo_medico_id=self._ultimo_medico_id,
                ultimo_atendimento_id=self._ultimo_atendimento_id,
                relogio_logico=self._relogio_logico,
            )
