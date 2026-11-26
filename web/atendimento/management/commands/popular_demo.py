"""Comando Django para popular dados 100% fictícios passando pelo core/sistema.py (T39)."""

from django.core.management.base import BaseCommand

from web.atendimento.servico import obter_sistema

MEDICOS_FICTICIOS = (
    ("Dra. Ana Fictícia (A)", "CRM-FIC-001"),
    ("Dr. Bruno Fictício (B)", "CRM-FIC-002"),
    ("Dra. Carla Fictícia (C)", "CRM-FIC-003"),
)

PACIENTES_FICTICIOS = (
    ("Paciente Fictício 1", 3),
    ("Paciente Fictício 2", 1),
    ("Paciente Fictício 3", 5),
    ("Paciente Fictício 4", 2),
    ("Paciente Fictício 5", 4),
    ("Paciente Fictício 6", 2),
    ("Paciente Fictício 7", 1),
    ("Paciente Fictício 8", 3),
)


class Command(BaseCommand):
    help = "Popula médicos e pacientes fictícios passando exclusivamente por core/sistema.py."

    def handle(self, *args, **options) -> None:
        sistema = obter_sistema()
        for nome, registro in MEDICOS_FICTICIOS:
            sistema.cadastrar_medico(nome, registro)
        for nome, prioridade in PACIENTES_FICTICIOS:
            sistema.cadastrar_paciente(nome, prioridade)
        self.stdout.write(
            self.style.SUCCESS(
                f"Dados fictícios cadastrados: {len(MEDICOS_FICTICIOS)} médicos e "
                f"{len(PACIENTES_FICTICIOS)} pacientes."
            )
        )
