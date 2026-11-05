# Geradores e a palavra-chave yield

Uma função comum calcula tudo e devolve o resultado de uma vez. Um gerador faz diferente: entrega um valor por vez, só quando alguém pede o próximo. Basta usar `yield` no lugar de `return`:

```python
def contagem_regressiva(n):
    while n > 0:
        yield n
        n -= 1

for numero in contagem_regressiva(3):
    print(numero)  # 3, depois 2, depois 1
```

Chamar `contagem_regressiva(3)` não executa nada ainda: devolve um objeto gerador. O corpo só roda quando o `for`, ou a função `next`, pede um valor. A execução avança até o próximo `yield`, entrega o valor e fica pausada ali, com as variáveis locais preservadas, até o pedido seguinte.

A grande vantagem é a memória. Para filtrar um arquivo de log de vários gigabytes, você não precisa carregá-lo inteiro:

```python
def linhas_com_erro(caminho):
    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            if "ERROR" in linha:
                yield linha
```

A cada momento, só uma linha está na memória. Geradores também podem ser encadeados, como etapas de uma linha de montagem, e podem até representar sequências infinitas, desde que quem consome pare em algum momento.

O detalhe que pega muita gente: um gerador só pode ser percorrido uma vez. Depois que ele se esgota, um segundo `for` não encontra nada. Se você precisa dos valores de novo, crie outro gerador ou guarde o resultado numa lista.
