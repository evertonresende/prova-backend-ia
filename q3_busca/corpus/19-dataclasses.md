# Dataclasses: classes de dados sem código repetitivo

Uma classe que só guarda dados costuma vir com muito código repetitivo: o `__init__` atribuindo cada campo, o `__repr__` para mostrar o objeto de forma legível e o `__eq__` para comparar dois objetos. O decorator `@dataclass` gera tudo isso a partir das anotações de tipo:

```python
from dataclasses import dataclass, field

@dataclass
class Produto:
    nome: str
    preco: float
    tags: list[str] = field(default_factory=list)

caneta = Produto("Caneta", 2.5)
print(caneta)  # Produto(nome='Caneta', preco=2.5, tags=[])
print(caneta == Produto("Caneta", 2.5))  # True
```

Repare no `field(default_factory=list)`. Escrever `tags: list[str] = []` daria erro, justamente para impedir que todos os objetos compartilhem a mesma lista. A fábrica cria uma lista nova para cada instância.

Algumas opções do decorator valem a pena. Com `@dataclass(frozen=True)`, os campos não podem ser reatribuídos depois da criação, e o Python gera o `__hash__`: o objeto pode virar chave de dicionário, desde que os campos também sejam hashable. Com `order=True`, o Python gera os operadores de comparação, e uma lista de objetos pode ser ordenada com `sorted`. E `slots=True`, disponível desde o 3.10, economiza memória quando há milhares de instâncias.

Um detalhe importante: as anotações de tipo não são verificadas. `Produto("Caneta", "barato")` é aceito sem reclamar. Quando os dados vêm de fora, como o corpo de uma requisição ou um arquivo JSON, e precisam de validação, o Pydantic é a ferramenta indicada. Para dados internos, a dataclass é leve e já vem com o Python.
