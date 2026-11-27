"""T36 / H25: smoke tests da interface web com django.test.Client."""

from django.test import Client


ROTAS_TELAS = (
    "/",
    "/pacientes/",
    "/triagem/",
    "/medicos/",
    "/atendimentos/",
    "/historico/",
    "/diagnostico/",
)


def test_todas_as_telas_respondem_200(banco):
    client = Client()
    for rota in ROTAS_TELAS:
        resposta = client.get(rota)
        assert resposta.status_code == 200, f"falha na rota {rota}"


def test_post_cadastro_paciente_aparece_na_lista(banco):
    from web.atendimento.servico import obter_sistema

    client = Client()
    resp = client.post(
        "/pacientes/",
        {"nome": "Paciente Web Ficticio", "prioridade": "2"},
        follow=True,
    )
    assert resp.status_code == 200
    assert "Paciente Web Ficticio" in resp.content.decode("utf-8")
    assert len(obter_sistema().listar_pacientes()) == 1


def test_chamada_sem_medico_mostra_mensagem_e_nao_altera_estado(banco):
    from web.atendimento.servico import obter_sistema

    client = Client()
    client.post("/pacientes/", {"nome": "Paciente Sem Medico", "prioridade": "2"})
    resp = client.post("/chamar/", {"origem": "painel"}, follow=True)
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    assert "não há médicos disponíveis" in html.lower()
    s = obter_sistema()
    assert s.proximo_paciente().nome == "Paciente Sem Medico"
    assert len(s.listar_atendimentos_ativos()) == 0
    assert s.validar_indices().ok


def test_dado_invalido_nao_altera_estado_nem_da_500(banco):
    from web.atendimento.servico import obter_sistema

    client = Client()
    resp_nome = client.post("/pacientes/", {"nome": "   ", "prioridade": "3"}, follow=True)
    assert resp_nome.status_code == 200

    resp_prio = client.post("/pacientes/", {"nome": "Teste", "prioridade": "9"}, follow=True)
    assert resp_prio.status_code == 200

    resp_busca = client.get("/pacientes/?buscar_id=999")
    assert resp_busca.status_code == 200

    s = obter_sistema()
    assert len(s.listar_pacientes()) == 0
    assert s.validar_indices().ok


def test_cancelar_atendimento_via_web_e_repetir_pelo_mesmo_medico_mostra_erro(banco):
    from web.atendimento.servico import obter_sistema

    client = Client()
    client.post("/medicos/", {"nome": "Dra. Web A", "registro": "CRM-WEB-A"})
    client.post("/pacientes/", {"nome": "Paciente Pouco Urgente", "prioridade": "4"})

    # Chama o paciente
    client.post("/chamar/", {"origem": "painel"})
    # Cadastra Muito urgente e Emergência enquanto o 1º está em atendimento
    client.post("/pacientes/", {"nome": "Paciente Muito Urgente", "prioridade": "2"})
    client.post("/pacientes/", {"nome": "Paciente Emergencia", "prioridade": "1"})

    s = obter_sistema()
    ativos = list(s.listar_atendimentos_ativos())
    assert len(ativos) == 1
    atend_id = ativos[0].id

    # Cancela atendimento via POST
    resp_cancel = client.post(f"/atendimentos/{atend_id}/cancelar/", follow=True)
    assert resp_cancel.status_code == 200
    assert [p.nome for p in s.listar_fila_prioridade()] == [
        "Paciente Emergencia",
        "Paciente Pouco Urgente",
        "Paciente Muito Urgente",
    ]
    assert s.consultar_medico(1).situacao == "Disponível"
    assert s.consultar_medico(1).concluidos == 0

    # Atende Emergência e conclui para que o devolvido vá novamente para a mesma médica
    client.post("/chamar/", {"origem": "triagem"})
    atend_emerg = list(s.listar_atendimentos_ativos())[0].id
    client.post(f"/atendimentos/{atend_emerg}/concluir/")

    # Agora o devolvido vai para a mesma médica (Dra. Web A)
    client.post("/chamar/", {"origem": "triagem"})
    atend_repetido = list(s.listar_atendimentos_ativos())[0].id

    # Na tela de Atendimentos, o botão cancelar fica escondido para este par
    resp_tela = client.get("/atendimentos/")
    assert resp_tela.status_code == 200
    assert "Cancelamento já usado por este médico" in resp_tela.content.decode("utf-8")

    # Mesmo enviando POST direto, o núcleo rejeita com mensagem de erro e sem 500
    resp_erro = client.post(f"/atendimentos/{atend_repetido}/cancelar/", follow=True)
    assert resp_erro.status_code == 200
    assert "já cancelou o atendimento deste paciente" in resp_erro.content.decode("utf-8").lower()
    assert len(s.listar_atendimentos_ativos()) == 1
    assert s.validar_indices().ok


def test_cancelar_paciente_em_atendimento_pede_confirmacao(banco):
    from web.atendimento.servico import obter_sistema

    client = Client()
    client.post("/medicos/", {"nome": "Dra. Web A", "registro": "CRM-WEB-A"})
    client.post("/pacientes/", {"nome": "Paciente Confirmacao", "prioridade": "3"})
    client.post("/chamar/", {"origem": "painel"})
    s = obter_sistema()

    lista = client.get("/pacientes/").content.decode("utf-8")
    assert 'href="/pacientes/1/cancelar/"' in lista

    # GET só mostra a confirmação e não altera nada
    resp = client.get("/pacientes/1/cancelar/")
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    assert "Confirmar cancelamento" in html
    assert "volta para a fila" in html
    assert s.consultar_paciente(1).situacao == "Em atendimento"

    # POST confirma: o paciente volta para a fila
    client.post("/pacientes/1/cancelar/", follow=True)
    assert s.consultar_paciente(1).situacao == "Aguardando"
    assert s.consultar_paciente(1).retorno is True
    assert s.validar_indices().ok


def test_tela_pacientes_esconde_cancelamento_ja_usado_pelo_medico(banco):
    from web.atendimento.servico import obter_sistema

    client = Client()
    client.post("/medicos/", {"nome": "Dra. Web A", "registro": "CRM-WEB-A"})
    client.post("/pacientes/", {"nome": "Paciente Devolvido", "prioridade": "3"})
    client.post("/chamar/", {"origem": "painel"})
    s = obter_sistema()
    client.post(f"/atendimentos/{s.listar_atendimentos_ativos().cabeca.valor.id}/cancelar/")
    # A mesma médica recebe o paciente de novo
    client.post("/chamar/", {"origem": "painel"})

    lista = client.get("/pacientes/").content.decode("utf-8")
    assert 'href="/pacientes/1/cancelar/"' not in lista
    assert "Cancelamento já usado por este médico" in lista

    confirmacao = client.get("/pacientes/1/cancelar/").content.decode("utf-8")
    assert "o cancelamento não está disponível" in confirmacao
    assert 'action="/pacientes/1/cancelar/"' not in confirmacao


def test_confirmacao_de_paciente_inexistente_ou_encerrado_redireciona(banco):
    client = Client()
    resp = client.get("/pacientes/999/cancelar/", follow=True)
    assert resp.status_code == 200
    assert "não encontrado" in resp.content.decode("utf-8")

    client.post("/pacientes/", {"nome": "Paciente Encerrado", "prioridade": "3"})
    client.post("/pacientes/1/cancelar/")
    resp = client.get("/pacientes/1/cancelar/", follow=True)
    assert resp.status_code == 200
    assert "já concluído ou cancelado" in resp.content.decode("utf-8")
