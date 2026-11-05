"""Apoio aos testes da Q2: modelos fake, um que grava tudo o que recebe e outro que sempre falha."""

from typing import Any

import openai
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult
from pydantic import Field


class ModeloGravador(GenericFakeChatModel):
    """Modelo fake que guarda as mensagens recebidas em cada chamada.

    O agente soma o prompt de sistema na hora da chamada, sem guardá-lo no
    estado do grafo. Por isso os testes conferem o que o modelo recebeu, e não
    o estado.
    """

    recebidas: list[list[BaseMessage]] = Field(default_factory=list)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        # O `_stream` do pai também passa por aqui: invoke e stream ficam gravados.
        self.recebidas.append(list(messages))
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


def modelo_com(*respostas: str) -> ModeloGravador:
    """Cria um modelo que devolve as respostas na ordem dada.

    Use um novo por teste: o iterador de respostas se esgota.
    """
    return ModeloGravador(messages=iter([AIMessage(r) for r in respostas]))


class ModeloQueFalha(GenericFakeChatModel):
    """Modelo fake que sempre levanta `openai.OpenAIError`, como numa falha da OpenAI (rede, chave, limite)."""

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        raise openai.OpenAIError("falha simulada")


def modelo_que_falha() -> GenericFakeChatModel:
    return ModeloQueFalha(messages=iter([]))  # "messages" é obrigatório no GenericFakeChatModel
