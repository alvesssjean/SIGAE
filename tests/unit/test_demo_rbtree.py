from cli.demo_rbtree import main


def rodar(respostas):
    it = iter(respostas)

    def entrada(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    saida = []
    main(entrada=entrada, saida=saida.append, cores=False)
    return "\n".join(str(s) for s in saida)


def test_demo_inserir_mostra_recoloracao_e_rotacao():
    texto = rodar(
        ["1", "08:00", "1", "Ana", "1", "08:05", "2", "", "1", "08:10", "3", "", "0"]
    )
    assert "rotação à esquerda" in texto
    assert "recolorir" in texto
    assert "Propriedades rubro-negras: OK" in texto
    assert "Antes:" in texto and "Depois:" in texto


def test_demo_aceita_horario_com_segundos():
    texto = rodar(["1", "08:00:30", "1", "", "5", "0"])
    assert "1. 2026-11-26 08:00:30 (ID 1)" in texto


def test_demo_rejeita_horario_e_id_invalidos():
    texto = rodar(["1", "8:5", "1", "08:00", "abc", "0"])
    assert "Horário inválido" in texto
    assert "ID inválido" in texto


def test_demo_rejeita_duplicada():
    texto = rodar(["1", "08:00", "1", "", "1", "08:00", "1", "", "0"])
    assert "Não inserido" in texto


def test_demo_remover_buscar_listar():
    texto = rodar(
        [
            "1", "08:00", "1", "Ana",
            "1", "08:05", "2", "Bruno",
            "3", "08:05", "2",
            "2", "08:05", "2",
            "3", "08:05", "2",
            "2", "09:00", "9",
            "5",
            "0",
        ]
    )
    assert "Encontrado. Valor: 'Bruno'" in texto
    assert "Chave não encontrada." in texto
    assert "1. 2026-11-26 08:00:00 (ID 1) - Ana" in texto


def test_demo_listar_arvore_vazia():
    assert "(nenhum paciente)" in rodar(["5", "0"])


def test_demo_exemplo_validar_e_limpar():
    texto = rodar(["7", "6", "8", "4", "9", "0"])
    assert "Árvore final:" in texto
    assert "Propriedades rubro-negras: OK" in texto
    assert "Árvore limpa." in texto
    assert "(árvore vazia)" in texto
    assert "Opção inválida." in texto


def test_demo_termina_sem_entrada():
    assert "Demonstração" in rodar([])
