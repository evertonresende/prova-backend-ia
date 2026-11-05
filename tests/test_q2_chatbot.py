import time

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from apoio_q2 import ModeloGravador, modelo_com
from q2_chatbot.chatbot import PROMPT_SISTEMA, ChaveAusenteError, criar_chatbot, criar_modelo, perguntar


def tipos(mensagens):
    return [type(m) for m in mensagens]


class ChatbotQueGuardaConfig:
    """Chatbot de mentira: guarda o `config` recebido por `invoke` e responde "ok"."""

    def invoke(self, entrada, config):
        self.config = config
        return {"messages": [AIMessage("ok")]}


def test_primeira_chamada_envia_prompt_de_sistema_e_pergunta():
    modelo = modelo_com("r1")
    resposta = perguntar(criar_chatbot(modelo), "Como criar uma lista em Python?", "c1", "teste")
    assert resposta == "r1"
    enviadas = modelo.recebidas[0]
    assert tipos(enviadas) == [SystemMessage, HumanMessage]
    assert enviadas[0].content == PROMPT_SISTEMA
    assert enviadas[1].content == "Como criar uma lista em Python?"


def test_mesma_conversa_envia_o_historico():
    modelo = modelo_com("r1", "r2")
    chatbot = criar_chatbot(modelo)
    perguntar(chatbot, "q1", "c1", "teste")
    perguntar(chatbot, "q2", "c1", "teste")
    assert tipos(modelo.recebidas[1]) == [SystemMessage, HumanMessage, AIMessage, HumanMessage]
    assert [m.content for m in modelo.recebidas[1][1:]] == ["q1", "r1", "q2"]


def test_conversas_diferentes_nao_misturam_historico():
    modelo = modelo_com("r1", "r2")
    chatbot = criar_chatbot(modelo)
    perguntar(chatbot, "q1", "c1", "teste")
    perguntar(chatbot, "qX", "c2", "teste")
    assert tipos(modelo.recebidas[1]) == [SystemMessage, HumanMessage]
    assert modelo.recebidas[1][1].content == "qX"


def test_perguntar_devolve_so_o_texto_quando_a_resposta_vem_em_blocos():
    # Modelos de raciocínio podem responder em blocos: raciocínio + texto.
    blocos = [
        {"type": "reasoning", "reasoning": "pensando..."},
        {"type": "text", "text": "Use []."},
    ]
    modelo = ModeloGravador(messages=iter([AIMessage(content=blocos)]))
    assert perguntar(criar_chatbot(modelo), "Como criar uma lista?", "c1", "teste") == "Use []."


def test_perguntar_marca_o_run_com_a_origem():
    chatbot = ChatbotQueGuardaConfig()
    perguntar(chatbot, "Olá", "abc", "cli")
    assert chatbot.config["tags"] == ["cli"]
    assert chatbot.config["metadata"] == {"origem": "cli"}
    assert chatbot.config["configurable"] == {"thread_id": "abc"}


# Chave vazia é o primeiro caso real: o .env.example vem com `OPENAI_API_KEY=`.
@pytest.mark.parametrize("chave", [None, ""])
def test_criar_modelo_sem_chave_da_erro_claro(monkeypatch, chave):
    if chave is None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    else:
        monkeypatch.setenv("OPENAI_API_KEY", chave)
    with pytest.raises(ChaveAusenteError, match="OPENAI_API_KEY"):
        criar_modelo()


@pytest.mark.parametrize("valor_env", [None, ""])
def test_criar_modelo_configuracao_padrao(monkeypatch, valor_env):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    if valor_env is None:
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
    else:
        monkeypatch.setenv("OPENAI_MODEL", valor_env)
    modelo = criar_modelo()
    assert modelo.model_name == "gpt-6-luna"
    assert modelo.request_timeout == 60
    assert modelo.max_retries == 2
    assert modelo.reasoning_effort == "medium"
    assert modelo.temperature is None


def test_criar_modelo_respeita_openai_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6.1-terra")
    assert criar_modelo().model_name == "gpt-6.1-terra"


@pytest.mark.live
def test_live_pergunta_do_enunciado(chave_openai_real):
    inicio = time.monotonic()
    resposta = perguntar(criar_chatbot(criar_modelo()), "Como criar uma lista em Python?", "live", "teste")
    duracao = time.monotonic() - inicio
    print(f"\nlatência: {duracao:.1f}s")
    assert "[" in resposta
    assert duracao < 60
