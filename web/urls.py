"""Rotas principais do projeto Django SIGAE WEB."""

from django.urls import include, path

urlpatterns = [
    path("", include("web.atendimento.urls")),
]
