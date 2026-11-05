# Decorators: comportamento extra sem mexer na função

Em Python, funções são objetos: podem ser guardadas em variáveis, passadas como argumento e devolvidas por outras funções. Um decorator aproveita isso. Ele é uma função que recebe outra função e devolve uma nova versão dela, com algum comportamento a mais.

Um exemplo clássico é cronometrar a execução:

```python
import functools
import time

def cronometrar(funcao):
    @functools.wraps(funcao)
    def envolvida(*args, **kwargs):
        inicio = time.perf_counter()
        resultado = funcao(*args, **kwargs)
        duracao = time.perf_counter() - inicio
        print(f"{funcao.__name__} levou {duracao:.3f}s")
        return resultado
    return envolvida

@cronometrar
def processar(dados):
    return sorted(dados)
```

A linha `@cronometrar` é só açúcar sintático para `processar = cronometrar(processar)`. A partir daí, toda chamada a `processar` passa pela função `envolvida`, que mede o tempo e repassa os argumentos com `*args` e `**kwargs`.

O `functools.wraps` copia o nome, a docstring e outros metadados da função original. Sem ele, ferramentas de depuração e de documentação enxergariam todas as funções decoradas com o nome `envolvida`.

A biblioteca padrão já traz decorators prontos: `functools.lru_cache` guarda o resultado de chamadas anteriores, e `property`, `staticmethod` e `classmethod` mudam a forma como os métodos de uma classe se comportam. Frameworks como FastAPI e pytest usam decorators para registrar rotas e fixtures.
