"""T26: testes Django sem pytest-django. Testes do core não dependem disto.

Uso: def test_x(banco): ...
"""

import os

import pytest


@pytest.fixture(scope="session")
def _banco_de_sessao():
    pytest.importorskip("django")
    pytest.importorskip("web.settings")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")

    import django

    django.setup()

    from django.db import connection
    from django.test.utils import setup_test_environment, teardown_test_environment

    setup_test_environment()
    nome_original = connection.settings_dict["NAME"]
    connection.creation.create_test_db(verbosity=0)
    yield
    connection.creation.destroy_test_db(nome_original, verbosity=0)
    teardown_test_environment()


@pytest.fixture
def banco(_banco_de_sessao):
    from django.core.management import call_command

    call_command("flush", interactive=False, verbosity=0)
    yield
