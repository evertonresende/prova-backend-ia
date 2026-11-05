# Requisições HTTP com requests

Consumir uma API web é rotina para quem programa em Python, e o pacote `requests` é o jeito mais conhecido de fazer isso. Ele não vem com o Python; instale com `python -m pip install requests`.

```python
import requests

resposta = requests.get(
    "https://api.github.com/search/repositories",
    params={"q": "fastapi", "per_page": 3},
    timeout=10,
)
resposta.raise_for_status()
for repo in resposta.json()["items"]:
    print(repo["full_name"], repo["stargazers_count"])
```

O argumento `params` monta a query string com o escape correto, sem concatenar textos na URL. O `raise_for_status()` transforma respostas de erro, como 404 e 500, em exceção; sem ele, o código seguiria tratando uma página de erro como se fosse o dado esperado. E o `json()` converte o corpo da resposta em dicionários e listas.

O detalhe mais esquecido é o `timeout`. Sem ele, o requests pode esperar indefinidamente: se o servidor parar de responder, o programa fica travado. Informe sempre um limite em segundos.

Para enviar dados, use `requests.post(url, json={"nome": "Ana"}, timeout=10)`, que serializa o dicionário e já define o cabeçalho `Content-Type`. Quando o código faz muitas chamadas ao mesmo servidor, uma `requests.Session()` reaproveita a conexão e guarda cabeçalhos comuns, como um token de autenticação.

Em código assíncrono, o requests não é a escolha certa, porque ele bloqueia enquanto espera a resposta; prefira um cliente assíncrono, como o `aiohttp`. E, para algo simples sem instalar nada, a biblioteca padrão tem o `urllib.request`, com uma interface menos amigável.
