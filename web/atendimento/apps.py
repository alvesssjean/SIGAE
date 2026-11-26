"""Configuração do app Django atendimento."""

from django.apps import AppConfig


class AtendimentoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "web.atendimento"
    verbose_name = "Atendimento SIGAE"
