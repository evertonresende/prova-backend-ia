"""Consultas da demonstração da busca semântica (`python -m q3_busca --demo`).

Cada item é (consulta, arquivo do post que tem que vir em 1º lugar). O teste `slow` de
`tests/test_q3_corpus.py` confere isso com o modelo real de embeddings.
"""

# A consulta que mostra que a busca é por significado, não por palavra: nenhuma palavra de
# conteúdo dela ("isolar", "bibliotecas", "projeto") aparece no post de ambientes virtuais, que
# diz a mesma coisa com outras palavras ("dependências", "pacotes", "aplicação"). Uma busca por
# palavras-chave não acharia esse post; a busca por embeddings acha.
CONSULTA_SEM_PALAVRAS_EM_COMUM: tuple[str, str] = (
    "como isolar as bibliotecas de cada projeto?",
    "09-ambientes-virtuais.md",
)

CONSULTAS_DEMO: list[tuple[str, str]] = [
    ("encontrar todos os endereços de e-mail dentro de um texto", "16-regex.md"),
    ("medir quanto tempo uma função demora para rodar", "05-decorators.md"),
    ("que horas são em Tóquio agora?", "15-datetime.md"),
    ("por que meu programa com várias threads não fica mais rápido?", "13-threads-processos-gil.md"),
    CONSULTA_SEM_PALAVRAS_EM_COMUM,
]
