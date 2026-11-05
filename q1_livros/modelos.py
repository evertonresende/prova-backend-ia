"""Modelos da Q1: o corpo do POST (com validação) e a tabela `livro`."""

from datetime import date

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class LivroBase(SQLModel):
    """Campos e regras comuns ao cadastro, à tabela e à resposta."""

    # Espaços das pontas saem antes de checar os limites: "   " vira "" e é rejeitado.
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=1, max_length=200)
    autor: str = Field(min_length=1, max_length=200)
    # Data de calendário válida em ISO 8601 (AAAA-MM-DD); "2026-02-30" dá 422.
    data_publicacao: date
    resumo: str = Field(min_length=1, max_length=5000)


# Corpo do `POST /livros`. Sem tabela, para que as regras valham de verdade.
# A docstring abaixo vira o texto público do schema no Swagger.
class LivroCriar(LivroBase):
    """Dados para cadastrar um livro."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "titulo": "Dom Casmurro",
                    "autor": "Machado de Assis",
                    "data_publicacao": "1899-01-01",
                    "resumo": "Bentinho narra o amor por Capitu e o ciúme que o consome.",
                }
            ]
        }
    )


class Livro(LivroBase, table=True):
    """Tabela `livro`.

    Modelos com `table=True` não validam no construtor: `Livro(titulo="")` passa
    sem erro. Por isso as linhas nascem de `Livro.model_validate(LivroCriar(...))`,
    que aplica as regras da entrada (o seed segue o mesmo caminho).
    """

    id: int | None = Field(default=None, primary_key=True)


class LivroLer(LivroBase):
    """Resposta da API: o livro com o `id` já definido."""

    id: int
