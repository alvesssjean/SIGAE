"""Models Django para persistência em SQLite (T23 / H20 / ADR-004).

Os IDs são gerados pelo core (sem autoincremento do banco).
"""

from django.db import models


class PacienteModel(models.Model):
    id = models.IntegerField(primary_key=True)
    nome = models.CharField(max_length=200)
    horario = models.CharField(max_length=19)
    prioridade = models.IntegerField()
    situacao = models.CharField(max_length=30)
    retorno = models.BooleanField(default=False)

    class Meta:
        db_table = "sigae_paciente"


class MedicoModel(models.Model):
    id = models.IntegerField(primary_key=True)
    nome = models.CharField(max_length=200)
    registro = models.CharField(max_length=60)
    situacao = models.CharField(max_length=30)
    concluidos = models.IntegerField(default=0)
    seq_ultima_atribuicao = models.IntegerField(default=0)

    class Meta:
        db_table = "sigae_medico"


class AtendimentoModel(models.Model):
    id = models.IntegerField(primary_key=True)
    paciente_id = models.IntegerField()
    medico_id = models.IntegerField()
    inicio = models.CharField(max_length=19)
    fim = models.CharField(max_length=19, null=True, blank=True)
    status = models.CharField(max_length=30)

    class Meta:
        db_table = "sigae_atendimento"


class Contador(models.Model):
    nome = models.CharField(max_length=50, primary_key=True)
    valor = models.IntegerField(default=0)

    class Meta:
        db_table = "sigae_contador"
