"""Isolamento do ambiente de teste.

Este arquivo roda antes de qualquer teste e garante que a suíte nunca chame a
OpenAI nem mande traces ao LangSmith por acidente, mesmo que o shell do
desenvolvedor tenha uma chave ou o tracing ligado.

Ele não importa nenhuma biblioteca de IA (o `dotenv` só entra dentro da
fixture): o atalho "só Q1" precisa rodar sem elas instaladas.
"""

import os
from pathlib import Path

import pytest

# As variáveis *_V2 são lidas primeiro e o LangSmith guarda o valor em cache na
# primeira leitura, então tudo isso tem que ser definido antes de qualquer
# import de biblioteca de IA.
for _nome in ("LANGSMITH_TRACING", "LANGSMITH_TRACING_V2", "LANGCHAIN_TRACING", "LANGCHAIN_TRACING_V2"):
    os.environ[_nome] = "false"

# Remove a chave para que um teste esquecido de usar mock falhe, em vez de
# gastar dinheiro. Os testes `live` pegam a chave de volta pela fixture abaixo.
CHAVE_OPENAI_ORIGINAL: str | None = os.environ.pop("OPENAI_API_KEY", None)


@pytest.fixture
def chave_openai_real(monkeypatch: pytest.MonkeyPatch) -> str:
    """Devolve a chave real da OpenAI e a recoloca no ambiente só neste teste.

    Procura primeiro no ambiente original, depois no `.env` da raiz; sem chave
    em nenhum dos dois, o teste é pulado.
    """
    chave = CHAVE_OPENAI_ORIGINAL
    if not chave:
        from dotenv import dotenv_values

        chave = dotenv_values(Path(__file__).resolve().parent.parent / ".env").get("OPENAI_API_KEY")
    if not chave:
        pytest.skip("sem OPENAI_API_KEY no ambiente nem no .env")
    monkeypatch.setenv("OPENAI_API_KEY", chave)
    return chave
