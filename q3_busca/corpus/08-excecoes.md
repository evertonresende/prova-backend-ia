# Tratando exceções com try e except

Quando algo dá errado durante a execução, o Python levanta uma exceção. Se ninguém a tratar, o programa para e mostra o traceback. Com `try` e `except`, você decide o que fazer no lugar:

```python
try:
    idade = int(input("Idade: "))
except ValueError:
    print("Digite um número inteiro.")
else:
    print(f"Ano que vem você terá {idade + 1} anos.")
finally:
    print("Fim do cadastro.")
```

O bloco `else` só roda se nenhuma exceção aconteceu, e o `finally` roda sempre, com ou sem erro. É o lugar certo para liberar recursos.

A regra de ouro é capturar só o que você sabe tratar. Um `except Exception:` genérico, ou pior, um `except:` vazio, esconde bugs de verdade: um erro de digitação no nome de uma variável vira um `NameError` engolido em silêncio, e você passa horas procurando o problema.

Também dá para levantar as suas próprias exceções e criar classes para os erros do seu domínio:

```python
class SaldoInsuficiente(Exception):
    pass

def sacar(saldo, valor):
    if valor > saldo:
        raise SaldoInsuficiente(f"saldo {saldo}, saque {valor}")
    return saldo - valor
```

Ao converter uma exceção em outra, prefira `raise NovoErro(...) from erro`. Sem o `from`, o traceback também mostra as duas, mas como um erro durante o tratamento da primeira; com ele, a original aparece como causa direta (`__cause__`). Por fim, exceções não são só para falhas raras: em Python é comum tentar a operação e tratar o erro, em vez de checar tudo antes. Esse estilo tem até nome, EAFP: é mais fácil pedir perdão do que permissão.
