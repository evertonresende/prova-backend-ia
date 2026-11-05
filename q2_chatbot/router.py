"""Rota da Q2: `POST /chat`, o chatbot de Python pela API.

O chatbot (modelo + memória) é um só por processo e nasce na primeira
requisição; cada `conversa_id` é uma conversa separada dentro dele.
"""

import logging
import threading
from typing import Annotated
from uuid import uuid4

import openai
from fastapi import APIRouter, HTTPException
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from q2_chatbot.chatbot import (
    MENSAGEM_FALHA_OPENAI,
    MENSAGEM_SEM_CHAVE,
    ChaveAusenteError,
    criar_chatbot,
    criar_modelo,
    perguntar,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Q2 · Chatbot"])


class PerguntaChat(BaseModel):
    """Corpo do `POST /chat`."""

    # Exemplo do Swagger sem `conversa_id`: cada "Try it out" abre uma conversa nova.
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"pergunta": "Como criar uma lista em Python?"}]}
    )

    # Espaços das pontas saem antes de checar o tamanho: "   " vira "" e dá 422.
    pergunta: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
    # O id vira a chave da conversa na memória do processo; o limite impede que um
    # cliente crie conversas com ids gigantes. Sem id, o servidor cria um.
    conversa_id: str | None = Field(default=None, max_length=100)


class RespostaChat(BaseModel):
    """Resposta do `POST /chat`: o texto do modelo e o id para continuar a conversa."""

    resposta: str
    conversa_id: str


_chatbot: CompiledStateGraph | None = None
_trava = threading.Lock()


def obter_chatbot() -> CompiledStateGraph:
    """Devolve o chatbot do processo, criado na primeira requisição.

    Carregamento lazy: subir a API não exige `OPENAI_API_KEY`; sem ela, só o
    `/chat` responde 503 e o resto do app segue de pé. Um chatbot só por
    processo: a memória das conversas mora no checkpointer dele, e um chatbot
    por requisição esqueceria o histórico. A trava faz duas primeiras
    requisições simultâneas esperarem uma única criação.
    """
    global _chatbot
    with _trava:
        if _chatbot is None:
            try:
                _chatbot = criar_chatbot(criar_modelo())
            except ChaveAusenteError:
                # A falha não fica guardada: a checagem é barata e cada
                # requisição confere a chave de novo.
                raise HTTPException(status_code=503, detail=MENSAGEM_SEM_CHAVE) from None
        return _chatbot


def resetar_chatbot() -> None:
    """Descarta o chatbot criado (e a memória dele); a próxima chamada cria outro."""
    global _chatbot
    with _trava:
        _chatbot = None


@router.post(
    "",
    summary="Perguntar ao chatbot de Python",
    description=(
        "Envia uma pergunta e devolve a resposta do modelo. Sem `conversa_id`, abre uma conversa "
        "nova e devolve o id dela; reenviar o mesmo `conversa_id` continua a conversa com o "
        "histórico. Precisa de `OPENAI_API_KEY` no servidor."
    ),
    responses={
        502: {"description": "Falha ao consultar a OpenAI (o detalhe fica só no log do servidor)"},
        503: {"description": "`OPENAI_API_KEY` não definida no servidor"},
    },
)
def conversar(dados: PerguntaChat) -> RespostaChat:
    # O FastAPI resolve os `Depends` antes de validar o corpo. Chamando aqui, um
    # corpo inválido responde 422 mesmo sem chave, e só uma pergunta válida
    # chega à checagem da chave (503).
    chatbot = obter_chatbot()
    conversa_id = dados.conversa_id or str(uuid4())
    try:
        resposta = perguntar(chatbot, dados.pergunta, conversa_id, "api")
    except openai.OpenAIError:
        # O cliente recebe só a mensagem genérica; o detalhe (status da OpenAI,
        # timeout, limite) vai para o log, onde quem opera o servidor o vê.
        # Limitação: a pergunta que falhou continua no histórico da conversa (o
        # checkpointer a salva antes de chamar o modelo) e vai de novo para o
        # modelo junto com a próxima pergunta.
        logger.exception("Falha ao consultar a OpenAI (conversa_id=%s)", conversa_id)
        raise HTTPException(status_code=502, detail=MENSAGEM_FALHA_OPENAI) from None
    return RespostaChat(resposta=resposta, conversa_id=conversa_id)
