"""Motor da busca semântica: posts → embeddings → índice FAISS → consulta.

O processo, em ordem:

1. `carregar_corpus` lê os posts Markdown de `corpus/` (título na primeira linha).
2. O embedder (multilingual-e5-small, via sentence-transformers) transforma cada post num
   vetor de norma 1; textos de assunto parecido ficam com vetores próximos.
3. `Buscador` guarda esses vetores num índice FAISS em disco e só o refaz quando o corpus
   ou o modelo mudam.
4. `Buscador.buscar` transforma a consulta em vetor e devolve os posts mais próximos.
"""

import hashlib
import json
import logging
import os
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np

logger = logging.getLogger(__name__)

MODELO_EMBEDDINGS = "intfloat/multilingual-e5-small"
PASTA_CORPUS = Path(__file__).parent / "corpus"
PASTA_INDICE = Path(__file__).parent / ".indice"
# O e5 lê no máximo 512 tokens por texto; o sentence-transformers corta o resto em silêncio.
LIMITE_TOKENS = 512

# Recebe n textos e devolve uma matriz (n, d) float32, uma linha por texto, cada linha com
# norma 1. A aplicação usa o modelo real (`embedder_real`); os testes, um embedder falso.
Embedder = Callable[[list[str]], np.ndarray]


@dataclass(frozen=True)
class Documento:
    """Um post do corpus: nome do arquivo, título (a linha `# ...`) e o texto depois dela."""

    arquivo: str
    titulo: str
    corpo: str


@dataclass(frozen=True)
class Resultado:
    """Um post encontrado pela busca, com o score de cosseno e o começo do texto."""

    titulo: str
    arquivo: str
    score: float
    trecho: str


def carregar_corpus(pasta: Path = PASTA_CORPUS) -> list[Documento]:
    """Lê os posts `*.md` da pasta, em ordem de nome (essa ordem é a posição de cada post no índice).

    A primeira linha de cada post tem que ser o título (`# título`). Sem ela, o erro diz qual
    arquivo está errado, em vez de seguir com um título vazio.
    """
    docs = []
    for caminho in sorted(pasta.glob("*.md")):
        primeira_linha, _, resto = caminho.read_text(encoding="utf-8").partition("\n")
        titulo = primeira_linha.removeprefix("# ").strip()
        if not primeira_linha.startswith("# ") or not titulo:
            raise ValueError(f"{caminho.name}: a primeira linha precisa ser '# título'")
        docs.append(Documento(arquivo=caminho.name, titulo=titulo, corpo=resto.strip()))
    return docs


# O e5 foi treinado com um prefixo que diz o papel de cada texto: "passage: " no que vai ser
# buscado e "query: " na pergunta. Sem os prefixos os vetores pioram, e nada avisa.
def texto_documento(doc: Documento) -> str:
    """Texto que vira o vetor de um post: prefixo do e5 + título + corpo."""
    return f"passage: {doc.titulo}\n{doc.corpo}"


def texto_consulta(consulta: str) -> str:
    """Texto que vira o vetor da consulta: prefixo do e5 + o que a pessoa digitou."""
    return f"query: {consulta}"


class Buscador:
    """Índice FAISS dos posts + o embedder que transforma as consultas em vetores."""

    def __init__(
        self,
        embed: Embedder,
        docs: list[Documento],
        nome_modelo: str = MODELO_EMBEDDINGS,
        pasta_indice: Path = PASTA_INDICE,
    ) -> None:
        self.embed = embed
        self.docs = docs
        impressao_digital = _impressao_digital(nome_modelo, docs)
        caminho_indice = pasta_indice / "indice.faiss"
        caminho_metadados = pasta_indice / "metadados.json"
        if (
            caminho_indice.exists()
            and caminho_metadados.exists()
            and json.loads(caminho_metadados.read_text(encoding="utf-8")).get("impressao_digital")
            == impressao_digital
        ):
            self.indice = faiss.deserialize_index(np.frombuffer(caminho_indice.read_bytes(), dtype=np.uint8))
            return

        logger.info(
            "Índice ausente ou desatualizado: gerando os embeddings de %d posts (o índice fica salvo em %s).",
            len(docs),
            pasta_indice,
        )
        vetores = embed([texto_documento(d) for d in docs])
        # Os vetores têm norma 1, então o produto interno (IP) entre dois deles é exatamente o
        # cosseno do ângulo entre eles: quanto maior, mais parecidos (1 = mesma direção).
        # Limitação: IndexFlatIP é busca exata (compara a consulta com todos os vetores), certa
        # para ~20 posts. Com milhões de vetores, um índice aproximado (IVF ou HNSW) troca um
        # pouco de precisão por velocidade.
        self.indice = faiss.IndexFlatIP(vetores.shape[1])
        self.indice.add(vetores)

        # Nunca faiss.write_index/read_index: eles abrem o arquivo com o fopen do C, não aceitam
        # Path e quebram em caminho com acento no Windows. serialize_index devolve os bytes do
        # índice, e quem grava e lê o arquivo é o Python.
        pasta_indice.mkdir(parents=True, exist_ok=True)
        _gravar_atomico(caminho_indice, faiss.serialize_index(self.indice).tobytes())
        # Os metadados vão por último porque são eles que dizem "este índice vale para este
        # corpus": se o processo cair entre as duas gravações, a impressão digital salva não
        # bate e o índice é refeito na próxima vez.
        metadados = {
            "impressao_digital": impressao_digital,
            "documentos": [{"arquivo": d.arquivo, "titulo": d.titulo} for d in docs],
        }
        _gravar_atomico(caminho_metadados, json.dumps(metadados, ensure_ascii=False, indent=2).encode("utf-8"))

    def buscar(self, consulta: str, k: int = 3) -> list[Resultado]:
        """Devolve os `k` posts mais parecidos com a consulta, do maior score para o menor."""
        if not consulta.strip():
            raise ValueError("A consulta não pode ser vazia.")
        if k < 1:
            raise ValueError("k precisa ser pelo menos 1.")
        k = min(k, self.indice.ntotal)
        # A consulta vai como matriz 2-D com uma linha: é o formato que o FAISS espera.
        scores, ids = self.indice.search(self.embed([texto_consulta(consulta)]), k)
        resultados = []
        for score, i in zip(scores[0], ids[0]):
            # O FAISS completa com id -1 as posições sem vizinho, com um score sentinela: a doc
            # dele fala em -Inf (que nem é JSON válido); no IndexFlatIP do faiss 1.15.1 vem o
            # menor float32 (≈ -3,4e38). Não é um post, então sai. O min() acima já evita isso;
            # este filtro é a segunda guarda.
            if i == -1:
                continue
            doc = self.docs[i]
            resultados.append(
                Resultado(titulo=doc.titulo, arquivo=doc.arquivo, score=float(score), trecho=_trecho(doc.corpo))
            )
        return resultados


def _impressao_digital(nome_modelo: str, docs: list[Documento]) -> str:
    """Hash do modelo + conteúdo do corpus: se qualquer um mudar, o índice salvo não serve mais."""
    # O json.dumps separa as partes sem ambiguidade ("ab" + "c" e "a" + "bc" dariam o mesmo hash).
    partes = [nome_modelo] + [[d.arquivo, d.titulo, d.corpo] for d in docs]
    return hashlib.sha256(json.dumps(partes).encode("utf-8")).hexdigest()


def _gravar_atomico(destino: Path, dados: bytes) -> None:
    """Grava num arquivo temporário e troca pelo destino de uma vez só (`os.replace`).

    Se o processo cair no meio, o arquivo antigo continua inteiro: ninguém lê um índice pela
    metade. O PID no nome evita que dois processos (CLI e API, por exemplo) dividam o temporário.
    """
    tmp = destino.with_name(f"{destino.name}.{os.getpid()}.tmp")
    tmp.write_bytes(dados)
    os.replace(tmp, destino)


def _trecho(corpo: str) -> str:
    """Começo do post para mostrar no resultado, sem blocos de código e com espaços colapsados."""
    # O trecho é para leitura: um bloco de código cru no começo do resultado polui a saída.
    sem_codigo = re.sub(r"```.*?```", " ", corpo, flags=re.S)
    texto = " ".join(sem_codigo.split())
    return texto if len(texto) <= 200 else texto[:200] + "…"


def embedder_real() -> Embedder:
    """Carrega o multilingual-e5-small na CPU e devolve a função que gera os embeddings.

    Na primeira vez, o sentence-transformers baixa o modelo (~0,49 GB) para o cache do Hugging Face.
    """
    # O import fica aqui dentro de propósito: o sentence-transformers puxa o torch, que é pesado
    # de importar. Assim, subir a API (ou só importar este módulo) não paga esse custo.
    from sentence_transformers import SentenceTransformer

    modelo = SentenceTransformer(MODELO_EMBEDDINGS, device="cpu")

    def embed(textos: list[str]) -> np.ndarray:
        # O que o encode faz por baixo: tokeniza cada texto, passa os tokens pelo modelo do
        # `transformers` (um encoder tipo BERT, que devolve um vetor por token), tira a média
        # desses vetores (mean pooling) e, com normalize_embeddings=True, divide o resultado pela
        # norma, para cada vetor ter comprimento 1.
        # Os prefixos do e5 já vêm de texto_documento/texto_consulta, aplicados à mão: no
        # sentence-transformers 6.2, encode_query/encode_document não os põem para este modelo
        # (ele não traz prompts configurados), e confiar neles pioraria a busca sem erro nenhum.
        return modelo.encode(
            textos, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True
        ).astype(np.float32)

    return embed


_buscador: Buscador | None = None
_trava = threading.Lock()


def obter_buscador() -> Buscador:
    """Devolve o buscador do processo, criado na primeira chamada.

    Carregamento lazy: subir a API não baixa nem carrega o modelo; isso só acontece na primeira
    busca. A trava faz duas primeiras buscas simultâneas esperarem uma única carga do modelo,
    em vez de carregá-lo duas vezes.
    """
    global _buscador
    with _trava:
        if _buscador is None:
            # PASTA_CORPUS, PASTA_INDICE e embedder_real são lidos aqui, na hora da chamada (e não
            # em argumento padrão), para os testes poderem trocá-los com monkeypatch. O corpus vem
            # antes do modelo: um post sem título falha na hora, sem esperar o download.
            docs = carregar_corpus(PASTA_CORPUS)
            _buscador = Buscador(embedder_real(), docs, pasta_indice=PASTA_INDICE)
        return _buscador


def resetar_buscador() -> None:
    """Descarta o buscador criado; a próxima chamada a `obter_buscador` cria outro."""
    global _buscador
    with _trava:
        _buscador = None
