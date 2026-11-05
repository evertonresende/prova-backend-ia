import re
import unicodedata

import pytest

from q3_busca.demo import CONSULTA_SEM_PALAVRAS_EM_COMUM, CONSULTAS_DEMO
from q3_busca.indice import LIMITE_TOKENS, MODELO_EMBEDDINGS, Buscador, carregar_corpus, embedder_real, texto_documento

PALAVRAS_VAZIAS = {"para", "como", "cada", "mais", "entre", "sobre", "quando", "mesmo", "isso", "essa",
                   "esse", "pelo", "pela", "seus", "suas", "onde", "qual", "quais", "muito", "também", "fazer"}


def palavras_de_conteudo(texto):
    simples = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).casefold()
    return {p for p in re.findall(r"\w+", simples) if len(p) >= 4 and p not in PALAVRAS_VAZIAS}


def test_corpus_tem_15_a_20_posts_com_titulos_unicos():
    docs = carregar_corpus()
    assert 15 <= len(docs) <= 20
    assert len({d.titulo for d in docs}) == len(docs)


def test_cada_post_tem_150_a_250_palavras():
    for doc in carregar_corpus():
        assert 150 <= len(doc.corpo.split()) <= 250, doc.arquivo


def test_consultas_demo_apontam_para_posts_existentes():
    arquivos = {d.arquivo for d in carregar_corpus()}
    assert 4 <= len(CONSULTAS_DEMO) <= 6
    assert all(esperado in arquivos for _, esperado in CONSULTAS_DEMO)
    assert CONSULTA_SEM_PALAVRAS_EM_COMUM in CONSULTAS_DEMO


def test_consulta_sem_palavras_em_comum_e_verdade():
    consulta, esperado = CONSULTA_SEM_PALAVRAS_EM_COMUM
    doc = next(d for d in carregar_corpus() if d.arquivo == esperado)
    assert palavras_de_conteudo(consulta) & palavras_de_conteudo(f"{doc.titulo} {doc.corpo}") == set()


@pytest.mark.slow
def test_todo_post_cabe_em_512_tokens():
    from transformers import AutoTokenizer

    tokenizador = AutoTokenizer.from_pretrained(MODELO_EMBEDDINGS)
    for doc in carregar_corpus():
        total = len(tokenizador(texto_documento(doc))["input_ids"])
        assert total <= LIMITE_TOKENS, f"{doc.arquivo}: {total} tokens"


@pytest.mark.slow
def test_consultas_demo_trazem_o_post_esperado_em_primeiro(tmp_path):
    buscador = Buscador(embedder_real(), carregar_corpus(), pasta_indice=tmp_path)
    for consulta, esperado in CONSULTAS_DEMO:
        assert buscador.buscar(consulta, k=1)[0].arquivo == esperado, consulta
