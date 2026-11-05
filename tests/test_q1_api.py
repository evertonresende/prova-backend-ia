import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from q1_livros.db import criar_engine, criar_tabelas, obter_sessao
from q1_livros.router import router

LIVRO = {"titulo": "Dom Casmurro", "autor": "Machado de Assis",
         "data_publicacao": "1899-01-01", "resumo": "Bentinho e Capitu."}


@pytest.fixture
def cliente():
    engine = criar_engine("sqlite://")
    criar_tabelas(engine)

    def sessao_de_teste():
        with Session(engine) as sessao:
            yield sessao

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[obter_sessao] = sessao_de_teste
    return TestClient(app)


def cadastrar(cliente, **campos):
    return cliente.post("/livros", json=LIVRO | campos)


def titulos(resposta):
    return [livro["titulo"] for livro in resposta.json()]


def test_cadastrar_devolve_201_com_id_e_location(cliente):
    resposta = cadastrar(cliente)
    assert resposta.status_code == 201
    assert resposta.json()["id"] == 1
    assert resposta.json()["titulo"] == "Dom Casmurro"
    assert resposta.headers["location"] == "/livros/1"


@pytest.mark.parametrize("corpo", [
    {k: v for k, v in LIVRO.items() if k != "resumo"},
    LIVRO | {"data_publicacao": "2026-02-30"},
    LIVRO | {"titulo": "   "},
])
def test_cadastrar_invalido_devolve_422(cliente, corpo):
    assert cliente.post("/livros", json=corpo).status_code == 422
    # Entrada inválida não grava nada.
    assert cliente.get("/livros").json() == []


def test_buscar_por_trecho_do_titulo(cliente):
    cadastrar(cliente)
    cadastrar(cliente, titulo="Memórias Póstumas de Brás Cubas")
    assert titulos(cliente.get("/livros", params={"titulo": "casmur"})) == ["Dom Casmurro"]


@pytest.mark.parametrize("termo", ["ERICO", "veríssimo", "erico ver"])
def test_buscar_autor_ignora_maiusculas_e_acentos(cliente, termo):
    cadastrar(cliente, titulo="O Continente", autor="Érico Veríssimo")
    resposta = cliente.get("/livros", params={"autor": termo})
    assert [l["autor"] for l in resposta.json()] == ["Érico Veríssimo"]


def test_titulo_e_autor_juntos_combinam_com_e(cliente):
    cadastrar(cliente)
    cadastrar(cliente, titulo="Memórias Póstumas de Brás Cubas")
    cadastrar(cliente, titulo="Iracema", autor="José de Alencar")
    assert titulos(cliente.get("/livros", params={"autor": "machado", "titulo": "memorias"})) == ["Memórias Póstumas de Brás Cubas"]
    assert cliente.get("/livros", params={"autor": "alencar", "titulo": "memorias"}).json() == []


def test_sem_resultado_devolve_lista_vazia(cliente):
    resposta = cliente.get("/livros", params={"titulo": "inexistente"})
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_sem_filtro_ou_filtro_vazio_devolve_todos_em_ordem(cliente):
    for titulo in ("A", "B", "C"):
        cadastrar(cliente, titulo=titulo)
    esperado = [1, 2, 3]
    assert [l["id"] for l in cliente.get("/livros").json()] == esperado
    assert [l["id"] for l in cliente.get("/livros", params={"titulo": "", "autor": "  "}).json()] == esperado


@pytest.mark.parametrize("termo, esperado", [
    ("50%", ["50% de desconto"]),
    ("50％", ["50% de desconto"]),
    ("a_b", ["A_B"]),
    ("a＿b", ["A_B"]),
])
def test_curingas_sao_literais(cliente, termo, esperado):
    for titulo in ("50% de desconto", "50 anos de história", "A_B", "AxB"):
        cadastrar(cliente, titulo=titulo)
    assert titulos(cliente.get("/livros", params={"titulo": termo})) == esperado


@pytest.mark.parametrize("filtro", ["titulo", "autor"])
def test_filtro_tem_no_maximo_200_caracteres(cliente, filtro):
    # Com a tabela vazia o LIKE nem roda: o teste precisa de um livro.
    cadastrar(cliente)
    assert cliente.get("/livros", params={filtro: "x" * 201}).status_code == 422
    resposta = cliente.get("/livros", params={filtro: "x" * 200})
    assert resposta.status_code == 200
    assert resposta.json() == []
    # Sem o limite, o NFKD transforma cada U+FDFA em 18 caracteres, o padrão do LIKE
    # passa de 50.000 bytes e o SQLite o recusa: a resposta era 500.
    assert cliente.get("/livros", params={filtro: "ﷺ" * 1600}).status_code == 422


def test_obter_por_id(cliente):
    cadastrar(cliente)
    assert cliente.get("/livros/1").json()["titulo"] == "Dom Casmurro"
    resposta = cliente.get("/livros/99")
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Livro não encontrado"}


@pytest.mark.parametrize("livro_id", ["abc", "0", "-1", "99999999999999999999"])
def test_obter_id_invalido_da_422(cliente, livro_id):
    # Fora de 1..2**63-1 não cabe no INTEGER do SQLite; tem que ser 422, nunca 500.
    resposta = cliente.get(f"/livros/{livro_id}")
    assert resposta.status_code == 422


def test_obter_id_no_limite_do_sqlite_da_404(cliente):
    assert cliente.get(f"/livros/{2**63 - 1}").status_code == 404


def test_openapi_documenta_as_rotas(cliente):
    esquema = cliente.app.openapi()
    assert esquema["paths"]["/livros"]["post"]["summary"]
    assert esquema["paths"]["/livros"]["get"]["summary"]
    assert "404" in esquema["paths"]["/livros/{livro_id}"]["get"]["responses"]
    assert "examples" in esquema["components"]["schemas"]["LivroCriar"]


def test_openapi_tem_exemplos_location_e_corpo_do_404(cliente):
    esquema = cliente.app.openapi()
    resposta_404 = esquema["paths"]["/livros/{livro_id}"]["get"]["responses"]["404"]
    assert resposta_404["content"]["application/json"]["example"] == {"detail": "Livro não encontrado"}
    resposta_201 = esquema["paths"]["/livros"]["post"]["responses"]["201"]
    assert resposta_201["headers"]["Location"]["schema"] == {"type": "string"}
    assert resposta_201["content"]["application/json"]["schema"]["$ref"].endswith("/LivroLer")
    filtros = {p["name"]: p for p in esquema["paths"]["/livros"]["get"]["parameters"]}
    assert [e["value"] for e in filtros["titulo"]["examples"].values()] == ["casmurro"]
    assert [e["value"] for e in filtros["autor"]["examples"].values()] == ["alencar"]
