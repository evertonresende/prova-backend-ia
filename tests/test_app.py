import importlib
import logging
import sys

from fastapi.testclient import TestClient

import q1_livros.db
from app.main import app

TAGS = {"Q1 · Livros", "Q2 · Chatbot", "Q3 · Busca semântica"}
PILHA_DE_IA = ("langchain", "langchain_core", "langchain_openai", "langgraph", "numpy", "faiss", "sentence_transformers")


def tags_do_esquema(esquema):
    return {tag for rota in esquema["paths"].values() for operacao in rota.values() for tag in operacao.get("tags", [])}


def test_swagger_mostra_as_tres_questoes():
    esquema = TestClient(app).get("/openapi.json").json()
    assert {"/livros", "/livros/{livro_id}", "/chat", "/busca"} <= set(esquema["paths"])
    assert tags_do_esquema(esquema) == TAGS


def test_raiz_redireciona_para_docs():
    resposta = TestClient(app).get("/", follow_redirects=False)
    assert resposta.status_code == 307
    assert resposta.headers["location"] == "/docs"


def test_lifespan_cria_as_tabelas(monkeypatch):
    chamadas = []
    monkeypatch.setattr("app.main.criar_tabelas", chamadas.append)
    with TestClient(app):
        pass
    assert chamadas == [q1_livros.db.engine]


def test_app_sobe_so_com_a_q1_sem_a_pilha_de_ia(monkeypatch, caplog):
    # Bloqueia também os submódulos já importados: o CPython devolve "pkg.sub" do cache sem olhar o pai.
    for nome in [m for m in list(sys.modules) if m.split(".")[0] in PILHA_DE_IA] + list(PILHA_DE_IA):
        monkeypatch.setitem(sys.modules, nome, None)
    for nome in [m for m in sys.modules if m.startswith(("q2_chatbot", "q3_busca", "app.main"))]:
        monkeypatch.delitem(sys.modules, nome)
    # O reimport troca o atributo `main` do pacote `app` pelo módulo novo, e restaurar o
    # `sys.modules` não o devolve. Sem isto, um patch por texto ("app.main.criar_tabelas")
    # num teste seguinte cairia no módulo novo, e o `app` dos outros testes criaria o
    # `livros.db` de verdade.
    monkeypatch.delattr(sys.modules["app"], "main")
    with caplog.at_level(logging.WARNING):
        caminhos = importlib.import_module("app.main").app.openapi()["paths"]
    assert "/livros" in caminhos
    assert "/chat" not in caminhos and "/busca" not in caminhos
    assert "Q2 (chatbot) indisponível" in caplog.text
    assert "Q3 (busca) indisponível" in caplog.text
