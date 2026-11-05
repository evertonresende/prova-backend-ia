# Threads, processos e o GIL

O CPython, o interpretador oficial, tem o GIL (Global Interpreter Lock): uma trava que deixa só uma thread executar bytecode Python por vez. Na prática, quatro threads somando números não deixam o cálculo quatro vezes mais rápido, porque elas se revezam em vez de rodar em paralelo.

Isso não torna as threads inúteis. Quando uma thread espera por rede ou disco, ela solta o GIL, e outra pode trabalhar. Para baixar várias páginas ou ler muitos arquivos, threads funcionam muito bem.

Para cálculo pesado, a saída é usar processos. Cada processo tem o próprio interpretador e o próprio GIL, então todos os núcleos trabalham de verdade. O módulo `concurrent.futures` oferece a mesma interface para os dois casos:

```python
from concurrent.futures import ProcessPoolExecutor

def divisores(n):
    return [d for d in range(1, n + 1) if n % d == 0]

if __name__ == "__main__":
    with ProcessPoolExecutor() as executor:
        resultados = list(executor.map(divisores, [10_000_000, 20_000_000]))
```

Para usar threads, basta trocar `ProcessPoolExecutor` por `ThreadPoolExecutor`; a escolha depende do gargalo. A guarda `if __name__ == "__main__"` é obrigatória com processos no Windows, no macOS e, desde o Python 3.14, também no Linux: os processos novos importam o módulo principal, e sem a guarda cada um tentaria criar outros, o que termina em erro.

O custo é maior: processos demoram mais para iniciar, e os dados trocados entre eles são serializados com pickle. Vale acompanhar também o free-threading, um CPython sem GIL: experimental no 3.13, oficial desde o 3.14, mas ainda opcional.
