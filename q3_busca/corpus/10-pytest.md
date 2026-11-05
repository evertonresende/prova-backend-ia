# Testes automatizados com pytest

Testar na mão, rodando o programa e conferindo a saída, funciona até a terceira mudança no código. Depois disso, um teste automatizado avisa na hora quando algo que funcionava deixou de funcionar. O pytest é a ferramenta mais popular para isso, e a sintaxe é só Python: funções cujo nome começa com `test_` e o `assert` de sempre.

```python
# test_precos.py
import pytest
from precos import aplicar_desconto

def test_desconto_de_dez_por_cento():
    assert aplicar_desconto(100, 0.1) == pytest.approx(90)

def test_desconto_acima_de_100_por_cento():
    with pytest.raises(ValueError):
        aplicar_desconto(100, 1.5)
```

Rodando `pytest` no terminal, ele encontra os arquivos `test_*.py`, executa cada teste e, quando um `assert` falha, mostra os valores envolvidos, sem que você precise escrever mensagem nenhuma. O `pytest.approx` compara números de ponto flutuante com uma tolerância, já que `0.1 + 0.2 == 0.3` é falso.

Para repetir um teste com várias entradas, use `parametrize`:

```python
@pytest.mark.parametrize("valor, esperado", [(0, 0), (50, 45), (200, 180)])
def test_varios_valores(valor, esperado):
    assert aplicar_desconto(valor, 0.1) == pytest.approx(esperado)
```

As fixtures preparam o que os testes precisam, como um banco de dados temporário, e são injetadas pelo nome do parâmetro. A fixture embutida `tmp_path`, por exemplo, entrega uma pasta temporária nova para cada teste.

Bons testes verificam comportamento, não detalhes de implementação. Assim você pode reescrever uma função inteira com a segurança de que, se os testes continuam verdes, nada quebrou.
