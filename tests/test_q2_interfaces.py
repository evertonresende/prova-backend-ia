import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import q2_chatbot.router as modulo_router
from apoio_q2 import modelo_com, modelo_que_falha
from q2_chatbot.__main__ import PERGUNTAS_DEMO, main
from q2_chatbot.chatbot import MENSAGEM_FALHA_OPENAI, MENSAGEM_SEM_CHAVE, criar_chatbot, perguntar
from q2_chatbot.router import obter_chatbot, resetar_chatbot, router


@pytest.fixture
def app():
    resetar_chatbot()
    aplicacao = FastAPI()
    aplicacao.include_router(router)
    yield aplicacao
    resetar_chatbot()


def com_modelo(app, monkeypatch, modelo):
    chatbot = criar_chatbot(modelo)
    monkeypatch.setattr("q2_chatbot.router.obter_chatbot", lambda: chatbot)
    return TestClient(app)


def test_chat_responde_e_cria_conversa_id(app, monkeypatch):
    cliente = com_modelo(app, monkeypatch, modelo_com("r1"))
    resposta = cliente.post("/chat", json={"pergunta": "Olá"})
    assert resposta.status_code == 200
    assert resposta.json()["resposta"] == "r1"
    uuid.UUID(resposta.json()["conversa_id"])


def test_chat_mesma_conversa_mantem_contexto(app, monkeypatch):
    modelo = modelo_com("r1", "r2")
    cliente = com_modelo(app, monkeypatch, modelo)
    conversa_id = cliente.post("/chat", json={"pergunta": "q1"}).json()["conversa_id"]
    cliente.post("/chat", json={"pergunta": "q2", "conversa_id": conversa_id})
    assert len(modelo.recebidas[1]) == 4


CORPOS_INVALIDOS = [
    {"pergunta": "   "}, {"pergunta": ""}, {}, {"pergunta": "ok", "conversa_id": "x" * 101},
]


@pytest.mark.parametrize("corpo", CORPOS_INVALIDOS)
def test_chat_valida_entrada(app, monkeypatch, corpo):
    assert com_modelo(app, monkeypatch, modelo_com()).post("/chat", json=corpo).status_code == 422


@pytest.mark.parametrize("corpo", CORPOS_INVALIDOS)
def test_chat_sem_chave_valida_o_corpo_antes(app, monkeypatch, corpo):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert TestClient(app).post("/chat", json=corpo).status_code == 422


def test_chat_sem_chave_devolve_503(app, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    resposta = TestClient(app).post("/chat", json={"pergunta": "Olá"})
    assert resposta.status_code == 503
    assert resposta.json() == {"detail": MENSAGEM_SEM_CHAVE}


def test_chat_falha_da_openai_devolve_502(app, monkeypatch):
    cliente = com_modelo(app, monkeypatch, modelo_que_falha())
    resposta = cliente.post("/chat", json={"pergunta": "Olá"})
    assert resposta.status_code == 502
    assert resposta.json() == {"detail": MENSAGEM_FALHA_OPENAI}


def test_obter_chatbot_cria_uma_vez_com_concorrencia(monkeypatch):
    resetar_chatbot()
    criacoes = []

    def criar_modelo_lento():
        criacoes.append(threading.get_ident())
        time.sleep(0.05)
        return modelo_com()

    monkeypatch.setattr(modulo_router, "criar_modelo", criar_modelo_lento)
    with ThreadPoolExecutor(8) as executor:
        chatbots = list(executor.map(lambda _: obter_chatbot(), range(8)))
    assert len(criacoes) == 1
    assert all(c is chatbots[0] for c in chatbots)
    resetar_chatbot()


def test_obter_chatbot_nao_guarda_a_falha_sem_chave(monkeypatch):
    resetar_chatbot()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(HTTPException) as erro:
        obter_chatbot()
    assert erro.value.status_code == 503
    monkeypatch.setattr("q2_chatbot.router.criar_modelo", lambda: modelo_com("oi"))
    assert perguntar(obter_chatbot(), "Olá", "c1", "teste") == "oi"
    resetar_chatbot()


def test_cli_sem_chave_sai_com_1_sem_traceback(capsys, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(["--demo"]) == 1
    erro = capsys.readouterr().err
    assert "OPENAI_API_KEY" in erro
    assert "Traceback" not in erro


def test_cli_demo_mostra_perguntas_e_usa_historico(capsys, monkeypatch):
    modelo = modelo_com("r1", "r2", "r3")
    monkeypatch.setattr("q2_chatbot.__main__.criar_modelo", lambda: modelo)
    assert main(["--demo"]) == 0
    saida = capsys.readouterr().out
    assert all(p in saida for p in PERGUNTAS_DEMO)
    assert all(r in saida for r in ("r1", "r2", "r3"))
    assert len(modelo.recebidas[1]) == 4


def test_cli_demo_conta_falhas(capsys, monkeypatch):
    monkeypatch.setattr("q2_chatbot.__main__.criar_modelo", modelo_que_falha)
    assert main(["--demo"]) == 1
    assert MENSAGEM_FALHA_OPENAI in capsys.readouterr().err


def test_cli_interativo_ignora_vazio_e_sai(monkeypatch):
    modelo = modelo_com("r1")
    entradas = iter(["", "Olá", "sair"])
    monkeypatch.setattr("q2_chatbot.__main__.criar_modelo", lambda: modelo)
    monkeypatch.setattr("builtins.input", lambda _="": next(entradas))
    assert main([]) == 0
    assert len(modelo.recebidas) == 1


@pytest.mark.parametrize("interrupcao", [EOFError, KeyboardInterrupt])
def test_cli_ctrl_d_e_ctrl_c_saem_sem_traceback(capsys, monkeypatch, interrupcao):
    def entrada(_=""):
        raise interrupcao

    monkeypatch.setattr("q2_chatbot.__main__.criar_modelo", lambda: modelo_com())
    monkeypatch.setattr("builtins.input", entrada)
    assert main([]) == 0
    assert "Traceback" not in capsys.readouterr().err
