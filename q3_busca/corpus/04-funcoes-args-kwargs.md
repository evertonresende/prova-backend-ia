# Funções, valores padrão, *args e **kwargs

Funções organizam o código em pedaços com nome, que recebem entradas e devolvem um resultado com `return`. Sem `return`, a função devolve `None`.

Parâmetros podem ter valor padrão, e na chamada os argumentos podem ir por posição ou por nome:

```python
def saudacao(nome, cumprimento="Olá"):
    return f"{cumprimento}, {nome}!"

saudacao("Ana")                    # 'Olá, Ana!'
saudacao("Rui", cumprimento="Oi")  # 'Oi, Rui!'
```

Cuidado com valor padrão mutável. Ele é avaliado uma única vez, quando a função é definida, então `def adicionar(item, lista=[])` reaproveita a mesma lista em todas as chamadas. O jeito certo é usar `lista=None` e criar a lista dentro da função.

Quando a quantidade de argumentos varia, entram `*args` e `**kwargs`:

```python
def registrar(mensagem, *args, **kwargs):
    print(mensagem, args, kwargs)

registrar("pedido", 1, 2, urgente=True)
# pedido (1, 2) {'urgente': True}
```

`*args` junta os argumentos posicionais extras numa tupla, e `**kwargs` junta os nomeados num dicionário. Os nomes são só convenção; o que importa são os asteriscos. Na chamada, eles fazem o inverso: `print(*[1, 2, 3])` espalha a lista como argumentos separados e imprime `1 2 3`.

Um asterisco sozinho na assinatura, como em `def conectar(host, *, timeout)`, obriga quem chama a passar `timeout` pelo nome. A chamada fica mais legível, e ninguém troca a ordem dos argumentos sem querer.
