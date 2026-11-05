# Formatando textos com f-strings

As f-strings, que chegaram no Python 3.6, são a forma mais direta de montar textos com valores dentro. Basta colocar um `f` antes das aspas e escrever qualquer expressão entre chaves:

```python
nome = "Ana"
saldo = 1234.5
print(f"Olá, {nome}! Seu saldo é R$ {saldo:.2f}")
# Olá, Ana! Seu saldo é R$ 1234.50
```

Depois dos dois-pontos vem a especificação de formato, a mesma minilinguagem do `str.format`. Alguns exemplos úteis:

```python
f"{0.256:.1%}"       # '25.6%'
f"{1234567:,}"       # '1,234,567'
f"{42:05d}"          # '00042'
f"{'item':>10}"      # '      item'
f"{agora:%d/%m/%Y}"  # ex.: '05/11/2026'
```

O último mostra que cada tipo pode definir o próprio formato: um `datetime` aceita, direto nas chaves, os mesmos códigos do `strftime`.

Para depurar, existe o atalho `=`, disponível desde o Python 3.8: `f"{saldo=}"` produz `saldo=1234.5`, com o nome e o valor da variável. Poupa tempo quando você quer espiar algumas variáveis no meio do código.

A vírgula como separador de milhar segue o padrão americano. Para o formato brasileiro, uma saída simples é trocar os caracteres depois de formatar, ou usar o módulo `locale`.

Um cuidado importante: f-string não serve para montar consultas SQL com dados do usuário, porque isso abre a porta para SQL injection. Nesse caso, use os parâmetros do driver do banco: `cursor.execute("SELECT * FROM livros WHERE autor = ?", (autor,))`.
