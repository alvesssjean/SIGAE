"""Comando Django para popular dados 100% fictícios passando pelo core/sistema.py (T39)."""

from django.core.management.base import BaseCommand

from web.atendimento.servico import obter_sistema

MEDICOS_FICTICIOS = (
    ("Ana Fictícia", "100001"),
    ("Bruno Fictício", "100002"),
    ("Carla Fictícia", "100003"),
)

PACIENTES_FICTICIOS = (
    ("Paciente Fictício Um", 3),
    ("Paciente Fictício Dois", 1),
    ("Paciente Fictício Três", 5),
    ("Paciente Fictício Quatro", 2),
    ("Paciente Fictício Cinco", 4),
    ("Paciente Fictício Seis", 2),
    ("Paciente Fictício Sete", 1),
    ("Paciente Fictício Oito", 3),
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
