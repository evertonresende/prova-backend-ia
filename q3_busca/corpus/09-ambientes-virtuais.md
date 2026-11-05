# Ambientes virtuais: dependências separadas para cada aplicação

Imagine duas aplicações na mesma máquina: uma depende do Django 4 e a outra do Django 5. Se os pacotes forem instalados direto no Python do sistema, as duas disputam a mesma pasta `site-packages`, e atualizar uma quebra a outra. O ambiente virtual resolve esse conflito: é uma pasta com o seu próprio interpretador e o seu próprio diretório de pacotes.

O módulo `venv` já vem com o Python:

```bash
python -m venv .venv
source .venv/bin/activate     # Linux e macOS
.venv\Scripts\activate        # Windows
python -m pip install requests
```

Com o ambiente ativado, os comandos `python` e `pip` passam a apontar para a pasta `.venv`, e tudo que você instala fica lá dentro, sem tocar no sistema nem nas outras aplicações. Para sair, basta rodar `deactivate`. E se algo der muito errado, apague a pasta e crie de novo: o ambiente é descartável.

Para que outra pessoa monte o mesmo ambiente, registre as dependências num arquivo:

```bash
python -m pip freeze > requirements.txt
python -m pip install -r requirements.txt
```

O `freeze` lista os pacotes instalados com as versões exatas, e o `install -r` reproduz essa lista em outra máquina ou no servidor. O arquivo vai para o controle de versão; a pasta `.venv`, não, porque ela guarda caminhos absolutos da sua máquina e pode ser recriada a qualquer momento.

Repare que os exemplos usam `python -m pip` em vez de `pip`. Assim não há dúvida sobre qual interpretador recebe a instalação.
