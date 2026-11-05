# Listas: a coleção mais usada do Python

A lista é a estrutura de dados que você mais vai encontrar em código Python. Ela guarda uma sequência de itens em ordem, aceita elementos de tipos diferentes e pode crescer ou encolher enquanto o programa roda.

```python
frutas = ["maçã", "banana"]
frutas.append("uva")          # adiciona no fim
frutas.insert(0, "kiwi")      # adiciona na posição 0
frutas.extend(["pera", "manga"])
print(frutas[0], frutas[-1])  # kiwi manga
print(frutas[1:3])            # ['maçã', 'banana']
```

O primeiro índice é zero, e índices negativos contam a partir do fim. O fatiamento `[início:fim]` devolve uma lista nova, sem incluir a posição final.

Listas são mutáveis: `append`, `remove` e `sort` alteram a própria lista e devolvem `None`. Por isso `frutas = frutas.sort()` é um erro clássico: a variável passa a valer `None` e a lista se perde. Quando quiser uma cópia ordenada sem mexer na original, use `sorted(frutas)`.

Outra pegadinha é a atribuição. `b = a` não copia nada: as duas variáveis apontam para a mesma lista, e mudar uma muda a outra. Para copiar, use `a.copy()` ou `list(a)`. Essas cópias são rasas: se a lista tiver outras listas dentro, as internas continuam compartilhadas.

Se a sequência não deve mudar depois de criada, prefira uma tupla. E se o código vive testando `item in lista` numa lista grande, um `set` faz essa verificação muito mais rápido.
