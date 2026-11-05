# Dicionários: pares de chave e valor

Um dicionário associa chaves a valores. Em vez de procurar um item pela posição, como numa lista, você o encontra pelo nome. E essa busca continua rápida mesmo com milhões de entradas, porque o dicionário usa uma tabela hash por baixo.

```python
estoque = {"caneta": 10, "caderno": 4}
estoque["borracha"] = 7         # cria ou substitui
print(estoque["caneta"])        # 10
print(estoque.get("lápis", 0))  # 0, sem erro
```

Acessar com colchetes uma chave que não existe levanta `KeyError`. O método `get` devolve um valor padrão no lugar, o que é ótimo quando a ausência é normal.

Um uso muito comum é contar ocorrências:

```python
contagem = {}
for palavra in "o rato roeu o queijo".split():
    contagem[palavra] = contagem.get(palavra, 0) + 1
# {'o': 2, 'rato': 1, 'roeu': 1, 'queijo': 1}
```

O módulo `collections` traz o `Counter`, que já faz essa contagem e ainda oferece `most_common()`.

Para percorrer o dicionário, `items()` entrega a chave e o valor juntos:

```python
for produto, quantidade in estoque.items():
    print(produto, quantidade)
```

Desde o Python 3.7, os dicionários preservam a ordem de inserção. As chaves precisam ser hashable: strings, números e tuplas de valores imutáveis servem; listas não. Já os valores podem ser qualquer coisa, inclusive outros dicionários, o que torna essa estrutura perfeita para representar dados vindos de um JSON.
