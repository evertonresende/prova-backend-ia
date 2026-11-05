"""Rota `GET /busca`: a busca semântica pela API."""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, StringConstraints

from q3_busca.indice import obter_buscador

router = APIRouter(prefix="/busca", tags=["Q3 · Busca semântica"])


class ResultadoBusca(BaseModel):
    """Um post encontrado pela busca."""

    titulo: str = Field(description="Título do post.")
    arquivo: str = Field(description="Nome do arquivo Markdown do post no corpus.")
    score: float = Field(description="Similaridade de cosseno entre a consulta e o post (maior = mais parecido).")
    trecho: str = Field(description="Começo do texto do post.")


# Rota com `def` (e não `async def`): a busca é trabalho bloqueante (gera o embedding da
# consulta no PyTorch), então o FastAPI a roda numa thread à parte, sem travar o servidor.
@router.get(
    "",
    summary="Busca posts por significado",
    description=(
        "Devolve os `k` posts do corpus mais parecidos com a consulta, do maior score para o menor. "
        "A busca é por significado (embeddings), não por palavras: a consulta pode não ter nenhuma "
        "palavra em comum com o post. **A primeira chamada carrega o modelo de embeddings (e, na "
        "primeira vez na máquina, baixa ~0,49 GB), então demora; as seguintes são rápidas.**"
    ),
)
def buscar_documentos(
    # Espaços das pontas saem antes de checar o tamanho: "   " vira "" e dá 422.
    q: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
        Query(description="Texto da consulta, em linguagem natural."),
    ],
    k: Annotated[int, Query(ge=1, le=10, description="Quantos posts devolver (de 1 a 10).")] = 3,
) -> list[ResultadoBusca]:
    # O buscador vem daqui, e não de `Depends`: o FastAPI resolve as dependências antes de
    # validar `q` e `k`, e uma consulta inválida esperaria o modelo carregar (e, na primeira
    # vez, baixar) só para receber o 422. Chamado aqui, depois da validação, o 422 sai na hora.
    buscador = obter_buscador()
    return [ResultadoBusca(**asdict(r)) for r in buscador.buscar(q, k)]
