"""App FastAPI único: uma API, um Swagger, as três questões."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from q1_livros.db import criar_tabelas, engine
from q1_livros.router import router as router_livros

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Cria as tabelas da Q1 ao subir. A Q2 e a Q3 carregam seus modelos só no primeiro uso."""
    criar_tabelas(engine)
    yield


app = FastAPI(
    title="Prova Backend IA",
    description=(
        "Três questões de back-end com IA numa API só:\n\n"
        "- **Q1 · Livros**: cadastro, busca e consulta de livros (SQLite).\n"
        "- **Q2 · Chatbot**: assistente de Python com memória por `conversa_id`.\n"
        "- **Q3 · Busca semântica**: posts parecidos por significado, via embeddings.\n\n"
        "Use esta página para testar: abra uma rota, clique em **Try it out**, preencha e **Execute**."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# A Q1 é sempre montada. A Q2 e a Q3 dependem da pilha de IA (LangChain, FAISS, PyTorch):
# se ela não estiver instalada, o app sobe só com a Q1 e avisa no log.
# A guarda pega só `ModuleNotFoundError`, nunca `Exception`: um bug real na Q2 ou na Q3
# precisa derrubar o app, não fazer um terço dele sumir em silêncio.
app.include_router(router_livros)

try:
    from q2_chatbot.router import router as router_chat

    app.include_router(router_chat)
except ModuleNotFoundError as erro:
    logger.warning("Q2 (chatbot) indisponível: falta o pacote %s. Instale o requirements.txt.", erro.name)

try:
    from q3_busca.router import router as router_busca

    app.include_router(router_busca)
except ModuleNotFoundError as erro:
    logger.warning("Q3 (busca) indisponível: falta o pacote %s. Instale o requirements.txt.", erro.name)


@app.get("/", include_in_schema=False)
def raiz() -> RedirectResponse:
    """Abre o Swagger quando alguém acessa a raiz."""
    return RedirectResponse("/docs")
