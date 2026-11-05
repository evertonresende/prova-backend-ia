import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

import q3_busca.indice as modulo
from apoio_q3 import POSTS, EmbedderFalso, escrever_corpus
from q3_busca.indice import Buscador, carregar_corpus, obter_buscador, resetar_buscador


@pytest.fixture
def docs(tmp_path):
    escrever_corpus(tmp_path / "corpus", POSTS)
    return carregar_corpus(tmp_path / "corpus")


def buscador(docs, tmp_path, embed=None):
    return Buscador(embed or EmbedderFalso(), docs, pasta_indice=tmp_path / "idx")


def test_carregar_corpus_le_titulo_e_corpo(docs):
    assert [d.arquivo for d in docs] == ["01-listas.md", "02-dicionarios.md", "03-arquivos.md"]
    assert docs[1].titulo == "Dicionários"
    assert docs[1].corpo == "dicionarios mapeiam chaves para valores"


def test_carregar_corpus_sem_titulo_da_erro_claro(tmp_path):
    escrever_corpus(tmp_path, {"sem-titulo.md": "texto sem linha de título"})
    with pytest.raises(ValueError, match="sem-titulo.md"):
        carregar_corpus(tmp_path)


def test_carregar_corpus_titulo_vazio_da_erro_claro(tmp_path):
    escrever_corpus(tmp_path, {"titulo-vazio.md": "# \n\ncorpo sem título"})
    with pytest.raises(ValueError, match="titulo-vazio.md"):
        carregar_corpus(tmp_path)


def test_prefixos_do_e5(docs, tmp_path):
    embed = EmbedderFalso()
    buscador(docs, tmp_path, embed).buscar("chaves e valores")
    assert all(t.startswith("passage: ") for t in embed.chamadas[0])
    assert embed.chamadas[-1] == ["query: chaves e valores"]


def test_mais_parecido_vem_primeiro(docs, tmp_path):
    resultados = buscador(docs, tmp_path).buscar("dicionarios chaves valores", k=3)
    assert resultados[0].arquivo == "02-dicionarios.md"
    assert [r.score for r in resultados] == sorted((r.score for r in resultados), reverse=True)


def test_k_maior_que_o_corpus_sem_linhas_vazias(docs, tmp_path):
    resultados = buscador(docs, tmp_path).buscar("listas", k=10)
    assert len(resultados) == 3
    assert all(math.isfinite(r.score) for r in resultados)


@pytest.mark.parametrize("consulta, k", [("   ", 3), ("listas", 0)])
def test_entrada_invalida(docs, tmp_path, consulta, k):
    with pytest.raises(ValueError):
        buscador(docs, tmp_path).buscar(consulta, k=k)


def test_trecho_do_resultado(docs, tmp_path):
    assert buscador(docs, tmp_path).buscar("listas append", k=1)[0].trecho == "listas guardam itens em ordem e aceitam append"


def test_trecho_longo_colapsa_espacos_e_corta_em_200(tmp_path):
    escrever_corpus(tmp_path / "c", {"longo.md": "# Longo\n\nlinha um\n\n" + "x" * 300})
    resultado = buscador(carregar_corpus(tmp_path / "c"), tmp_path).buscar("linha", k=1)[0]
    assert resultado.trecho == "linha um " + "x" * 191 + "…"


def test_indice_salvo_e_reaproveitado(docs, tmp_path):
    buscador(docs, tmp_path)
    assert (tmp_path / "idx" / "indice.faiss").exists()
    assert (tmp_path / "idx" / "metadados.json").exists()
    embed = EmbedderFalso()
    buscador(docs, tmp_path, embed)
    assert embed.chamadas == []


def test_indice_em_pasta_com_acento(docs, tmp_path):
    Buscador(EmbedderFalso(), docs, pasta_indice=tmp_path / "índice")
    embed = EmbedderFalso()
    Buscador(embed, docs, pasta_indice=tmp_path / "índice")
    assert embed.chamadas == []


def test_reconstroi_quando_o_corpus_muda(tmp_path):
    escrever_corpus(tmp_path / "c", POSTS)
    Buscador(EmbedderFalso(), carregar_corpus(tmp_path / "c"), pasta_indice=tmp_path / "idx")
    escrever_corpus(tmp_path / "c", {"01-listas.md": "# Listas\n\ntexto novo"})
    embed = EmbedderFalso()
    Buscador(embed, carregar_corpus(tmp_path / "c"), pasta_indice=tmp_path / "idx")
    assert len(embed.chamadas) == 1


def test_obter_buscador_cria_uma_vez_com_concorrencia(monkeypatch, tmp_path):
    escrever_corpus(tmp_path / "corpus", POSTS)
    monkeypatch.setattr(modulo, "PASTA_CORPUS", tmp_path / "corpus")
    monkeypatch.setattr(modulo, "PASTA_INDICE", tmp_path / "idx")
    criacoes = []

    def embedder_lento():
        criacoes.append(threading.get_ident())
        time.sleep(0.05)
        return EmbedderFalso()

    monkeypatch.setattr(modulo, "embedder_real", embedder_lento)
    resetar_buscador()
    with ThreadPoolExecutor(8) as executor:
        buscadores = list(executor.map(lambda _: obter_buscador(), range(8)))
    assert len(criacoes) == 1
    assert all(b is buscadores[0] for b in buscadores)
    resetar_buscador()
