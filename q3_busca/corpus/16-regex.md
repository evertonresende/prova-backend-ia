# Expressões regulares com o módulo re

Expressões regulares descrevem padrões de texto. Com elas, você valida o formato de um CEP, extrai todos os e-mails de um documento ou muda datas de formato, tudo em poucas linhas. Em Python, elas ficam no módulo `re`.

```python
import re

texto = "Fale com ana@exemplo.com ou rui@empresa.com.br até 15/03/2026."

emails = re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", texto)
# ['ana@exemplo.com', 'rui@empresa.com.br']

data = re.search(r"(\d{2})/(\d{2})/(\d{4})", texto)
print(data.group(3))  # 2026

iso = re.sub(r"(\d{2})/(\d{2})/(\d{4})", r"\3-\2-\1", texto)
```

As funções principais são `search`, que acha a primeira ocorrência em qualquer ponto do texto; `match`, que só testa o começo; `fullmatch`, que exige que o texto inteiro case com o padrão; `findall`, que devolve todas as ocorrências; e `sub`, que substitui. Os parênteses criam grupos, que você recupera com `group(n)` ou reaproveita na substituição com `\1`, `\2` e assim por diante.

Escreva os padrões sempre como raw strings, com o prefixo `r`. Sem ele, o Python interpreta as barras invertidas antes do módulo `re`, e `"\b"` vira um caractere de backspace em vez de limite de palavra.

Se o mesmo padrão aparece em vários pontos, `re.compile` dá um nome a ele e deixa o código mais claro. E saiba a hora de parar: para HTML, JSON ou CSV, use um parser de verdade, porque a regex sempre quebra num caso que você não previu.
