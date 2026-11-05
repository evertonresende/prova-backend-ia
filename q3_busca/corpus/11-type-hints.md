# Type hints: anotações de tipo em Python

Python tem tipagem dinâmica: uma variável pode guardar um número agora e um texto depois. As type hints não mudam isso. Elas são anotações que documentam o que cada função espera receber e o que devolve:

```python
def media(notas: list[float]) -> float:
    return sum(notas) / len(notas)

def buscar_usuario(email: str) -> dict[str, str] | None:
    ...
```

O ponto que mais confunde quem está começando: o interpretador não verifica nada disso. Chamar `media("abc")` roda normalmente até quebrar lá dentro, com um `TypeError`. Quem confere os tipos são ferramentas externas, como o mypy e o Pyright, que analisam o código sem executá-lo e apontam o erro antes de ele chegar à produção. Os editores usam as mesmas anotações para autocompletar e sinalizar problemas enquanto você digita.

A sintaxe ficou bem mais simples nas versões recentes. Desde o Python 3.9 dá para escrever `list[int]` e `dict[str, int]` sem importar nada do módulo `typing`, e desde o 3.10 a barra vertical substitui `Optional` e `Union`: `int | None` quer dizer "um inteiro ou nada".

Alguns frameworks leem as anotações em tempo de execução, e aí elas viram comportamento. O FastAPI e o Pydantic usam os tipos para validar os dados de entrada e gerar a documentação da API automaticamente.

Não é preciso anotar tudo de uma vez. Comece pelas funções públicas, que formam o contrato do seu código com quem o usa.
