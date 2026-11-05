"""Banco SQLite da Q1: engine, busca sem acento e sessão por requisição."""

import os
import unicodedata
from collections.abc import Iterator

from sqlalchemy import Engine, event
from sqlalchemy.pool import NullPool, StaticPool
from sqlmodel import Session, SQLModel, create_engine


def normalizar(texto: str | None) -> str | None:
    """Tira acentos e maiúsculas, para que `erico` ache `Érico`.

    O `LIKE` do SQLite só ignora maiúsculas em letras ASCII e nunca ignora
    acento. Por isso a busca compara `normalizar(coluna)` com o termo também
    normalizado.

    O NFKD separa a letra da marca de acento (`é` vira `e` + acento); depois
    descartamos as marcas e aplicamos `casefold()`, que é mais completo que
    `lower()` (`ß` vira `ss`).

    `None` volta `None`: uma exceção dentro de função SQL vira
    `OperationalError`, e a coluna pode ser nula.
    """
    if texto is None:
        return None
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).casefold()


def criar_engine(url: str) -> Engine:
    """Cria o engine e registra `normalizar` no SQLite em toda conexão.

    App e testes usam esta mesma função, então a busca se comporta igual nos dois.
    """
    argumentos: dict = {"connect_args": {"check_same_thread": False}}
    if url == "sqlite://":
        # Banco em memória some quando a conexão fecha. O StaticPool mantém uma
        # única conexão viva, compartilhada entre as threads do TestClient.
        argumentos["poolclass"] = StaticPool
    else:
        # Arquivo: uma conexão nova por sessão, sem pool. Conexão de SQLite é barata
        # (abrir um arquivo local), e assim nenhuma requisição espera numa fila do
        # pool. Com o pool limitado do SQLAlchemy 2.x (5 + 10 conexões) e o threadpool
        # do FastAPI, acima de ~55 requisições simultâneas tudo travava por 30 s e as
        # requisições respondiam 500. Era o padrão do SQLAlchemy 1.x para arquivo.
        argumentos["poolclass"] = NullPool
    engine = create_engine(url, **argumentos)

    # O listener tem que ser ligado logo depois de criar o engine, antes de
    # qualquer conexão abrir: com StaticPool a primeira conexão vive para sempre
    # e, se já existisse, nunca receberia a função.
    @event.listens_for(engine, "connect")
    def _registrar_normalizar(dbapi_connection, _registro) -> None:
        dbapi_connection.create_function("normalizar", 1, normalizar, deterministic=True)

    return engine


def url_padrao() -> str:
    """URL do banco: `LIVROS_DB_PATH` se definida e não vazia, senão `livros.db` na pasta atual."""
    # `or` em vez do padrão do getenv para que `LIVROS_DB_PATH=` vazio no .env
    # também caia no padrão (vazio viraria `sqlite:///`, um banco em memória).
    return f"sqlite:///{os.getenv('LIVROS_DB_PATH') or 'livros.db'}"


# Criar o engine não abre conexão nem cria o arquivo, então é seguro no import.
engine = criar_engine(url_padrao())


def criar_tabelas(engine: Engine) -> None:
    """Cria as tabelas que ainda não existem."""
    SQLModel.metadata.create_all(engine)


def obter_sessao() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição, fechada ao final."""
    with Session(engine) as sessao:
        yield sessao
