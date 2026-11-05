# Logging: trocando o print por mensagens de verdade

Espalhar `print` pelo código para entender o que está acontecendo funciona no começo, mas não escala. As mensagens não têm hora nem origem, não dá para desligar só as de depuração, e elas se misturam com a saída real do programa. O módulo `logging` resolve tudo isso.

```python
import logging

logger = logging.getLogger(__name__)

def processar_pedido(pedido_id):
    logger.info("Processando o pedido %s", pedido_id)
    try:
        enviar_para_estoque(pedido_id)
    except ConnectionError:
        logger.exception("Falha no pedido %s", pedido_id)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    processar_pedido(42)
```

Cada mensagem tem um nível: `DEBUG`, `INFO`, `WARNING`, `ERROR` ou `CRITICAL`. A configuração define o nível mínimo exibido. Em produção você mostra de `INFO` para cima e, ao investigar um problema, baixa para `DEBUG` sem mexer no resto do código.

Três práticas fazem diferença. Primeiro, crie um logger por módulo com `getLogger(__name__)`, para cada linha mostrar de onde veio. Segundo, configure o logging uma única vez, no ponto de entrada do programa, e nunca dentro de uma biblioteca. Terceiro, passe os valores como argumentos, como em `"%s", pedido_id`, em vez de montar a string antes: a formatação só acontece se a mensagem for mesmo exibida.

Dentro de um `except`, o `logger.exception` registra a mensagem com nível `ERROR` e ainda inclui o traceback completo, o que poupa muito tempo na hora de depurar.
