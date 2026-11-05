# Context managers e o bloco with

Muitos recursos precisam ser liberados depois do uso: arquivos e conexões de banco têm que ser fechados, travas entre threads têm que ser soltas. Esquecer essa etapa, ou pulá-la porque uma exceção aconteceu no meio do caminho, causa vazamentos difíceis de rastrear. O bloco `with` resolve isso.

O objeto usado no `with` é um context manager. Ele implementa dois métodos: `__enter__`, chamado na entrada do bloco, cujo retorno vai para a variável depois do `as`; e `__exit__`, chamado na saída, aconteça o que acontecer. O `__exit__` recebe a exceção, se houve uma, e pode até suprimi-la devolvendo `True`.

Escrever uma classe com esses dois métodos funciona, mas o módulo `contextlib` oferece um atalho com geradores:

```python
import sqlite3
from contextlib import contextmanager

@contextmanager
def conexao(caminho):
    conn = sqlite3.connect(caminho)
    try:
        yield conn
    finally:
        conn.close()

with conexao("loja.db") as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS clientes (nome TEXT)")
```

Tudo antes do `yield` roda na entrada do bloco, e o valor entregue pelo `yield` é o que vai para o `as`. O `finally` garante que a conexão seja fechada mesmo que o bloco levante uma exceção.

O exemplo não é à toa. O próprio objeto de conexão do `sqlite3` pode ser usado num `with`, mas ele só faz commit ou rollback da transação: a conexão continua aberta. É um bom lembrete de que cada context manager decide o que acontece na saída, e vale conferir a documentação.
