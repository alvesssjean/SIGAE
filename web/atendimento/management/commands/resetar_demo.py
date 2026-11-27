"""Comando Django para zerar banco SQLite e estado em memória (T39)."""

from django.core.management.base import BaseCommand

from web.atendimento.repositorio_django import RepositorioDjango
from web.atendimento.servico import obter_sistema, resetar_sistema


class Command(BaseCommand):
    help = "Zera as tabelas do SIGAE e recria o estado em memória."

    def handle(self, *args, **options) -> None:
        RepositorioDjango().limpar_tudo()
        resetar_sistema()
        obter_sistema()
        self.stdout.write(
            self.style.SUCCESS("Banco e estado em memória do SIGAE zerados com sucesso.")
        )
