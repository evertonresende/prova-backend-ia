# Compreensões de lista, dicionário e conjunto

Compreensão é a forma enxuta de criar uma coleção a partir de outra. Em vez de começar com uma lista vazia e chamar `append` dentro de um `for`, você escreve tudo numa expressão só:

```python
quadrados = [n * n for n in range(10)]
pares = [n for n in range(10) if n % 2 == 0]
```

A leitura é quase em português: "n vezes n, para cada n de 0 a 9". O `if` no final funciona como filtro e deixa passar só os itens que satisfazem a condição.

A mesma ideia vale para dicionários e conjuntos:

```python
precos = {"café": 4.5, "pão": 0.8}
com_desconto = {item: valor * 0.9 for item, valor in precos.items()}
iniciais = {nome[0] for nome in ["Ana", "Bia", "Alice"]}  # {'A', 'B'}
```

Com parênteses no lugar dos colchetes, o resultado é uma expressão geradora, que produz os valores sob demanda em vez de montar a coleção inteira na memória. Ela é a escolha certa quando o resultado vai direto para uma função como `sum` ou `max`: `sum(n * n for n in range(1_000_000))`.

Compreensões costumam ser um pouco mais rápidas que o laço equivalente, mas o principal ganho é a clareza. O limite é o bom senso: com dois `for` aninhados e várias condições, a linha vira um quebra-cabeça. Nesse ponto, um laço comum, com nomes bons, é mais fácil de ler e de depurar.
