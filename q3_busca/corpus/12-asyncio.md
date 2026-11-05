# Programação assíncrona com asyncio

Um programa que conversa com a rede passa boa parte do tempo esperando: a resposta de uma API, o retorno de um banco de dados. O `asyncio` aproveita essa espera. Enquanto uma tarefa aguarda, o event loop passa a vez para outra, tudo numa única thread.

```python
import asyncio

async def baixar(nome, segundos):
    await asyncio.sleep(segundos)  # simula uma chamada de rede
    return f"{nome} pronto"

async def main():
    resultados = await asyncio.gather(
        baixar("a", 2), baixar("b", 2), baixar("c", 2)
    )
    print(resultados)  # ['a pronto', 'b pronto', 'c pronto']

asyncio.run(main())
```

O programa termina em cerca de dois segundos, e não em seis, porque as três esperas acontecem ao mesmo tempo. Uma função definida com `async def` é uma corrotina: chamá-la não executa o corpo, só cria um objeto que o event loop sabe rodar. O `await` marca os pontos em que a corrotina pode pausar e ceder a vez.

Esse modelo é cooperativo, e isso tem um preço. Se uma corrotina fizer um cálculo pesado ou chamar uma função bloqueante, como `time.sleep`, o loop inteiro trava junto. Por isso o ecossistema assíncrono tem clientes próprios, como o `aiohttp`, e o `asyncio.to_thread` existe para empurrar código bloqueante para uma thread separada.

O asyncio brilha com muitas operações de entrada e saída simultâneas: servidores web, crawlers, bots. Para cálculo pesado ele não ajuda; aí o caminho é usar vários processos.
