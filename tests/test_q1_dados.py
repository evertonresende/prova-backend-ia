from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlmodel import Session, select

from q1_livros.db import criar_engine, criar_tabelas, normalizar
from q1_livros.modelos import Livro, LivroCriar
from q1_livros.seed import LIVROS_EXEMPLO, popular

VALIDO = {"titulo": "T", "autor": "A", "data_publicacao": "2000-01-01", "resumo": "R"}


@pytest.mark.parametrize("entrada, esperado", [
    ("Érico Veríssimo", "erico verissimo"),
    ("JOSÉ DE ALENCAR", "jose de alencar"),
    ("Coração", "coracao"),
    ("", ""),
    (None, None),
])
def test_normalizar(entrada, esperado):
    assert normalizar(entrada) == esperado


def test_engine_registra_normalizar_no_sqlite():
    with criar_engine("sqlite://").connect() as conexao:
        assert conexao.execute(text("select normalizar('Érico')")).scalar() == "erico"


def test_dados_persistem_no_arquivo(tmp_path):
    url = f"sqlite:///{tmp_path / 'livros.db'}"
    engine = criar_engine(url)
    criar_tabelas(engine)
    with Session(engine) as sessao:
        sessao.add(Livro.model_validate(LivroCriar(**VALIDO)))
        sessao.commit()
    engine.dispose()
    with Session(criar_engine(url)) as sessao:
        assert len(sessao.exec(select(Livro)).all()) == 1


def test_livro_criar_remove_espacos_e_converte_data():
    livro = LivroCriar(**VALIDO | {"titulo": "  Dom Casmurro  ", "data_publicacao": "1899-01-01"})
    assert livro.titulo == "Dom Casmurro"
    assert livro.data_publicacao == date(1899, 1, 1)


@pytest.mark.parametrize("campo, valor", [
    ("titulo", "   "), ("autor", ""), ("titulo", "x" * 201),
    ("autor", "x" * 201), ("resumo", "x" * 5001), ("data_publicacao", "2026-02-30"),
])
def test_livro_criar_rejeita_invalido(campo, valor):
    with pytest.raises(ValidationError):
        LivroCriar(**VALIDO | {campo: valor})


def test_seed_popula_10_livros_e_e_idempotente():
    engine = criar_engine("sqlite://")
    criar_tabelas(engine)
    with Session(engine) as sessao:
        assert popular(sessao) == len(LIVROS_EXEMPLO) == 10
        assert popular(sessao) == 0
        assert len(sessao.exec(select(Livro)).all()) == 10
