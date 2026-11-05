# Lendo e escrevendo arquivos de texto

Ler e gravar arquivos de texto é uma das tarefas mais comuns em Python, e a receita recomendada é sempre a mesma: `open` dentro de um bloco `with`, que fecha o arquivo no fim, e com o `encoding` explícito.

```python
with open("notas.txt", "w", encoding="utf-8") as arquivo:
    arquivo.write("primeira linha\n")

with open("notas.txt", "a", encoding="utf-8") as arquivo:
    arquivo.write("segunda linha\n")

with open("notas.txt", encoding="utf-8") as arquivo:
    for linha in arquivo:
        print(linha.rstrip("\n"))
```

O modo `"w"` cria o arquivo ou apaga o conteúdo anterior, `"a"` acrescenta no fim, e o padrão, `"r"`, só lê. Para imagens e outros dados binários, acrescente `b` ao modo, como em `"rb"`.

Por que insistir no `encoding`? Sem ele, o Python 3.14 e as versões anteriores usam a codificação preferida do sistema. No Linux e no macOS ela costuma ser UTF-8, mas no Windows pode ser outra, e o programa que funciona na sua máquina mostra acentos quebrados, ou falha com `UnicodeDecodeError`, na máquina de outra pessoa. Com o `encoding` explícito, o resultado é o mesmo em qualquer sistema e em qualquer versão.

Percorrer o arquivo com `for` lê uma linha por vez, o que funciona até com arquivos enormes. Já `read()` carrega tudo de uma vez na memória.

Para operações simples, o `pathlib` deixa o código ainda mais curto:

```python
from pathlib import Path

caminho = Path("dados") / "config.json"
texto = caminho.read_text(encoding="utf-8")
```

O `Path` monta caminhos com o separador certo para cada sistema e ainda oferece métodos como `exists()` e `glob()`.
