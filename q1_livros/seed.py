"""Seed da Q1: `python -m q1_livros.seed` cadastra 10 livros brasileiros.

Pode rodar quantas vezes quiser: só entram os livros que ainda não existem.
"""

from dotenv import load_dotenv
from sqlmodel import Session, select

from q1_livros.db import criar_engine, criar_tabelas, url_padrao
from q1_livros.modelos import Livro, LivroCriar

# Só o ano de publicação é conhecido. Para caber no campo de data, usamos 1º de
# janeiro (AAAA-01-01): o dia e o mês não são reais.
# "Erico Verissimo" é a grafia que o próprio autor usava, sem acento.
LIVROS_EXEMPLO: list[dict[str, str]] = [
    {
        "titulo": "Iracema",
        "autor": "José de Alencar",
        "data_publicacao": "1865-01-01",
        "resumo": "Romance indianista sobre o amor entre a índia tabajara Iracema e o colonizador "
        "português Martim, no Ceará do século XVII. A obra funciona como lenda de origem "
        "do povo cearense.",
    },
    {
        "titulo": "Memórias Póstumas de Brás Cubas",
        "autor": "Machado de Assis",
        "data_publicacao": "1881-01-01",
        "resumo": "O defunto Brás Cubas conta a própria vida com ironia e humor ácido. "
        "O livro inaugura o Realismo no Brasil e critica a elite carioca do século XIX.",
    },
    {
        "titulo": "O Cortiço",
        "autor": "Aluísio Azevedo",
        "data_publicacao": "1890-01-01",
        "resumo": "Romance naturalista sobre a vida num cortiço do Rio de Janeiro, onde moradores "
        "pobres são explorados pelo dono, o português João Romão. Mostra como o meio e a "
        "ambição moldam as personagens.",
    },
    {
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "data_publicacao": "1899-01-01",
        "resumo": "Bentinho, já velho, narra o amor por Capitu e a desconfiança de que ela o traiu "
        "com o amigo Escobar. Até hoje os leitores discutem se a traição existiu ou se foi "
        "só o ciúme do narrador.",
    },
    {
        "titulo": "Macunaíma",
        "autor": "Mário de Andrade",
        "data_publicacao": "1928-01-01",
        "resumo": "Rapsódia sobre Macunaíma, o \"herói sem nenhum caráter\", que sai da floresta "
        "para recuperar o amuleto muiraquitã. Mistura lendas indígenas, africanas e europeias "
        "e é obra central do Modernismo.",
    },
    {
        "titulo": "Capitães da Areia",
        "autor": "Jorge Amado",
        "data_publicacao": "1937-01-01",
        "resumo": "Meninos de rua de Salvador, liderados por Pedro Bala, vivem de pequenos furtos "
        "num trapiche abandonado. O romance denuncia a miséria e o abandono da infância.",
    },
    {
        "titulo": "Vidas Secas",
        "autor": "Graciliano Ramos",
        "data_publicacao": "1938-01-01",
        "resumo": "A família do vaqueiro Fabiano foge da seca pelo sertão nordestino, junto com a "
        "cachorra Baleia. Em linguagem seca e econômica, o livro mostra a pobreza dos retirantes.",
    },
    {
        "titulo": "O Continente",
        "autor": "Erico Verissimo",
        "data_publicacao": "1949-01-01",
        "resumo": "Primeira parte da trilogia O Tempo e o Vento, conta a formação do Rio Grande do "
        "Sul do século XVIII ao XIX, acompanhando as famílias Terra, Cambará e Amaral.",
    },
    {
        "titulo": "Grande Sertão: Veredas",
        "autor": "João Guimarães Rosa",
        "data_publicacao": "1956-01-01",
        "resumo": "O ex-jagunço Riobaldo conta sua vida pelo sertão de Minas Gerais, o amor por "
        "Diadorim e a dúvida sobre um pacto com o diabo. A linguagem inventiva faz dele um "
        "dos maiores romances da literatura brasileira.",
    },
    {
        "titulo": "A Hora da Estrela",
        "autor": "Clarice Lispector",
        "data_publicacao": "1977-01-01",
        "resumo": "O narrador Rodrigo S.M. conta a vida de Macabéa, jovem nordestina pobre e "
        "ingênua que vive no Rio de Janeiro. Foi o último romance que Clarice publicou em vida.",
    },
]


def popular(sessao: Session) -> int:
    """Insere os livros de exemplo que ainda não existem e devolve quantos entraram.

    Um livro "já existe" quando o par (título, autor) está na tabela. Passa pelo
    mesmo caminho do POST (`LivroCriar` e depois `model_validate`), nunca `Livro(...)`
    direto, porque a tabela não valida.
    """
    existentes = set(sessao.exec(select(Livro.titulo, Livro.autor)).all())
    novos = [
        Livro.model_validate(LivroCriar(**dados))
        for dados in LIVROS_EXEMPLO
        if (dados["titulo"], dados["autor"]) not in existentes
    ]
    sessao.add_all(novos)
    sessao.commit()
    return len(novos)


def main() -> None:
    """Cria o banco (se preciso) e cadastra os livros de exemplo."""
    # O engine é criado aqui, e não no import: o `engine` de `q1_livros.db` nasce
    # antes de o `.env` ser lido, e o seed precisa usar o mesmo LIVROS_DB_PATH da API.
    engine = criar_engine(url_padrao())
    criar_tabelas(engine)
    with Session(engine) as sessao:
        n = popular(sessao)
    print(f"{n} livro(s) cadastrado(s).")


if __name__ == "__main__":
    load_dotenv()
    main()
