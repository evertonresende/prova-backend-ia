"""Rotas da Q1: cadastrar, buscar e consultar livros."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy import func
from sqlmodel import Session, select

from q1_livros.db import normalizar, obter_sessao
from q1_livros.modelos import Livro, LivroCriar, LivroLer

router = APIRouter(prefix="/livros", tags=["Q1 · Livros"])

Sessao = Annotated[Session, Depends(obter_sessao)]


@router.post(
    "",
    status_code=201,
    response_model=LivroLer,
    summary="Cadastrar um livro",
    description=(
        "Cria um livro a partir de título, autor, data de publicação (AAAA-MM-DD) e resumo. "
        "Devolve o livro com o `id` gerado e o endereço dele no header `Location`."
    ),
)
def cadastrar_livro(dados: LivroCriar, sessao: Sessao, response: Response) -> Livro:
    # A linha nasce de `model_validate` porque o construtor de `Livro` (table=True)
    # não valida nada; as regras de entrada estão em `LivroCriar`.
    livro = Livro.model_validate(dados)
    sessao.add(livro)
    sessao.commit()
    sessao.refresh(livro)
    response.headers["Location"] = f"/livros/{livro.id}"
    return livro


@router.get(
    "",
    response_model=list[LivroLer],
    summary="Buscar livros por título e/ou autor",
    description=(
        "Devolve os livros cujo título e/ou autor contêm o trecho informado, sem diferenciar "
        "maiúsculas de minúsculas nem acentos. Com os dois filtros, o livro precisa atender aos "
        "dois. Sem filtros, devolve todos, ordenados por `id`. Sem resultado, devolve `[]`."
    ),
)
def buscar_livros(
    sessao: Sessao,
    # O limite de 200 é o tamanho máximo dos campos. Sem ele, um termo longo passava do
    # limite de 50.000 bytes do padrão do LIKE no SQLite e a busca respondia 500.
    titulo: Annotated[
        str | None,
        Query(
            max_length=200,
            description="Trecho do título, até 200 caracteres. Ignora maiúsculas e acentos; "
            "vazio = sem filtro.",
        ),
    ] = None,
    autor: Annotated[
        str | None,
        Query(
            max_length=200,
            description="Trecho do autor, até 200 caracteres. Ignora maiúsculas e acentos; "
            "vazio = sem filtro.",
        ),
    ] = None,
) -> list[Livro]:
    consulta = select(Livro).order_by(Livro.id)
    for coluna, valor in ((Livro.titulo, titulo), (Livro.autor, autor)):
        # Normaliza primeiro e escapa por último: o NFKD transforma `％` e `＿` de
        # largura total em `%` e `_`; se o escape viesse antes, eles virariam
        # curingas do LIKE. O `autoescape` roda depois, então ficam literais.
        termo = normalizar((valor or "").strip())
        if termo:
            # Limitação: o filtro roda `normalizar` em toda linha (varredura completa
            # da tabela). Em escala, usar coluna normalizada com índice ou FTS5.
            consulta = consulta.where(func.normalizar(coluna).contains(termo, autoescape=True))
    return list(sessao.exec(consulta).all())


@router.get(
    "/{livro_id}",
    response_model=LivroLer,
    summary="Consultar um livro pelo id",
    description=(
        "Devolve o livro com o `id` informado, ou 404 se ele não existir. "
        "O `id` precisa ser um inteiro entre 1 e 2**63 - 1 (o limite do INTEGER do SQLite); "
        "fora disso a resposta é 422."
    ),
    responses={404: {"description": "Livro não encontrado"}},
)
def obter_livro(livro_id: Annotated[int, Path(ge=1, le=2**63 - 1)], sessao: Sessao) -> Livro:
    livro = sessao.get(Livro, livro_id)
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    return livro
