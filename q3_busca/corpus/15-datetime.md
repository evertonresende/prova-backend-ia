# Datas, horas e fusos com datetime

O módulo `datetime` resolve quase tudo que envolve datas em Python. As classes principais são `date` (só a data), `datetime` (data e hora) e `timedelta` (uma duração).

```python
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

agora = datetime.now(timezone.utc)
local = agora.astimezone(ZoneInfo("America/Sao_Paulo"))
vencimento = local + timedelta(days=30)
print(vencimento.strftime("%d/%m/%Y %H:%M"))
```

A distinção mais importante é entre datas ingênuas e conscientes. Um `datetime` ingênuo, sem fuso horário, é só uma leitura de relógio: "10h" não diz se são 10h em São Paulo ou em Lisboa. Um `datetime` consciente carrega o fuso no atributo `tzinfo` e representa um instante exato. Subtrair um do outro, ou compará-los com `<`, levanta `TypeError`.

Uma regra que evita dor de cabeça: guarde e calcule tudo em UTC, e converta para o fuso local só na hora de mostrar ao usuário. O módulo `zoneinfo`, disponível desde o Python 3.9, usa o banco de fusos da IANA e conhece as regras de horário de verão de cada região. No Windows, que não traz esse banco, instale o pacote `tzdata`.

Para transformar texto em data, o `strptime` faz o caminho inverso do `strftime`:

```python
nascimento = datetime.strptime("25/12/1990", "%d/%m/%Y").date()
```

Para trocar datas entre sistemas, em APIs ou arquivos JSON, prefira o formato ISO 8601, com `isoformat()` e `fromisoformat()`.
