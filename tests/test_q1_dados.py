from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import func, text
from sqlalchemy.pool import NullPool, StaticPool
from sqlmodel import Session, select

from q1_livros.db import criar_engine, criar_tabelas, normalizar, url_padrao
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


def test_banco_em_arquivo_abre_uma_conexao_por_sessao(tmp_path):
    assert isinstance(criar_engine(f"sqlite:///{tmp_path / 'livros.db'}").pool, NullPool)


def test_banco_em_memoria_mantem_uma_conexao_so():
    assert isinstance(criar_engine("sqlite://").pool, StaticPool)


def test_busca_sem_acento_vale_em_toda_sessao_do_arquivo(tmp_path):
    # Cada sessão abre uma conexão nova: `normalizar` tem que existir em todas.
    engine = criar_engine(f"sqlite:///{tmp_path / 'livros.db'}")
    criar_tabelas(engine)
    with Session(engine) as sessao:
        sessao.add(Livro.model_validate(LivroCriar(**VALIDO | {"autor": "Érico Veríssimo"})))
        sessao.commit()
    for _ in range(2):
        with Session(engine) as sessao:
            consulta = select(Livro).where(func.normalizar(Livro.autor).contains("erico"))
            assert [livro.autor for livro in sessao.exec(consulta).all()] == ["Érico Veríssimo"]


def test_url_padrao_usa_o_padrao_quando_a_variavel_esta_vazia(monkeypatch):
    monkeypatch.setenv("LIVROS_DB_PATH", "")
    assert url_padrao() == "sqlite:///livros.db"


def test_url_padrao_respeita_a_variavel(monkeypatch):
    monkeypatch.setenv("LIVROS_DB_PATH", "outro.db")
    assert url_padrao() == "sqlite:///outro.db"
    monkeypatch.delenv("LIVROS_DB_PATH")
    assert url_padrao() == "sqlite:///livros.db"


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
