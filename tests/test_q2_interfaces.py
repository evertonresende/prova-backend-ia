import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import q2_chatbot.router as modulo_router
from apoio_q2 import modelo_com, modelo_que_falha
from q2_chatbot.__main__ import PERGUNTAS_DEMO, main
from q2_chatbot.chatbot import MENSAGEM_FALHA_OPENAI, MENSAGEM_SEM_CHAVE, criar_chatbot
from q2_chatbot.router import obter_chatbot, resetar_chatbot, router


@pytest.fixture
def app():
    resetar_chatbot()
    aplicacao = FastAPI()
    aplicacao.include_router(router)
    yield aplicacao
    aplicacao.dependency_overrides.clear()
    resetar_chatbot()


def com_modelo(app, modelo):
    chatbot = criar_chatbot(modelo)
    app.dependency_overrides[obter_chatbot] = lambda: chatbot
    return TestClient(app)


def test_chat_responde_e_cria_conversa_id(app):
    resposta = com_modelo(app, modelo_com("r1")).post("/chat", json={"pergunta": "Olá"})
    assert resposta.status_code == 200
    assert resposta.json()["resposta"] == "r1"
    uuid.UUID(resposta.json()["conversa_id"])


def test_chat_mesma_conversa_mantem_contexto(app):
    modelo = modelo_com("r1", "r2")
    cliente = com_modelo(app, modelo)
    conversa_id = cliente.post("/chat", json={"pergunta": "q1"}).json()["conversa_id"]
    cliente.post("/chat", json={"pergunta": "q2", "conversa_id": conversa_id})
    assert len(modelo.recebidas[1]) == 4


@pytest.mark.parametrize("corpo", [
    {"pergunta": "   "}, {"pergunta": ""}, {}, {"pergunta": "ok", "conversa_id": "x" * 101},
])
def test_chat_valida_entrada(app, corpo):
    assert com_modelo(app, modelo_com()).post("/chat", json=corpo).status_code == 422


def test_chat_sem_chave_devolve_503(app, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    resposta = TestClient(app).post("/chat", json={"pergunta": "Olá"})
    assert resposta.status_code == 503
    assert resposta.json() == {"detail": MENSAGEM_SEM_CHAVE}


def test_chat_falha_da_openai_devolve_502(app):
    resposta = com_modelo(app, modelo_que_falha()).post("/chat", json={"pergunta": "Olá"})
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
