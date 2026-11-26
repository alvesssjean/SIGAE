"""Rotas do app atendimento (6 telas obrigatórias + Diagnóstico)."""

from django.urls import path

from web.atendimento import views

urlpatterns = [
    path("", views.painel, name="painel"),
    path("chamar/", views.chamar_proximo, name="chamar_proximo"),
    path("pacientes/", views.pacientes, name="pacientes"),
    path(
        "pacientes/<int:paciente_id>/cancelar/",
        views.cancelar_paciente,
        name="cancelar_paciente",
    ),
    path("triagem/", views.triagem, name="triagem"),
    path("medicos/", views.medicos, name="medicos"),
    path("atendimentos/", views.atendimentos, name="atendimentos"),
    path(
        "atendimentos/<int:atendimento_id>/concluir/",
        views.concluir_atendimento,
        name="concluir_atendimento",
    ),
    path(
        "atendimentos/<int:atendimento_id>/cancelar/",
        views.cancelar_atendimento,
        name="cancelar_atendimento",
    ),
    path("historico/", views.historico, name="historico"),
    path("diagnostico/", views.diagnostico, name="diagnostico"),
]
