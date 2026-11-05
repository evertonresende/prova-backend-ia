"""Apoio aos testes da Q3: corpus de exemplo e um embedder falso que não baixa modelo."""

import re
import zlib
from pathlib import Path

import numpy as np

POSTS = {
    "01-listas.md": "# Listas\n\nlistas guardam itens em ordem e aceitam append",
    "02-dicionarios.md": "# Dicionários\n\ndicionarios mapeiam chaves para valores",
    "03-arquivos.md": "# Arquivos\n\nabrir arquivos com open e fechar com with",
}


def escrever_corpus(pasta: Path, posts: dict[str, str]) -> None:
    pasta.mkdir(parents=True, exist_ok=True)  # alguns testes escrevem 2x na mesma pasta
    for nome, texto in posts.items():
        (pasta / nome).write_text(texto, encoding="utf-8")


class EmbedderFalso:
    """Embedder determinístico: saco de palavras com hash estável (crc32), sem baixar modelo."""

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim
        self.chamadas: list[list[str]] = []

    def __call__(self, textos: list[str]) -> np.ndarray:
        self.chamadas.append(list(textos))
        matriz = np.zeros((len(textos), self.dim), dtype=np.float32)
        for i, texto in enumerate(textos):
            for palavra in re.findall(r"\w+", texto.lower()):
                if palavra not in ("passage", "query"):
                    matriz[i, zlib.crc32(palavra.encode()) % self.dim] += 1
        normas = np.linalg.norm(matriz, axis=1, keepdims=True)
        return matriz / np.where(normas == 0, 1, normas)
