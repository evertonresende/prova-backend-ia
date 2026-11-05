import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apoio_q3 import POSTS, EmbedderFalso, escrever_corpus
from q3_busca.__main__ import main
from q3_busca.indice import Buscador, carregar_corpus
from q3_busca.router import router

app_de_teste = FastAPI()
app_de_teste.include_router(router)


@pytest.fixture
def buscador_falso(tmp_path):
    escrever_corpus(tmp_path / "corpus", POSTS)
    return Buscador(EmbedderFalso(), carregar_corpus(tmp_path / "corpus"), pasta_indice=tmp_path / "idx")


@pytest.fixture
def cliente(monkeypatch, buscador_falso):
    monkeypatch.setattr("q3_busca.router.obter_buscador", lambda: buscador_falso)
    return TestClient(app_de_teste)


def test_busca_devolve_resultados_no_formato_certo(cliente):
    resposta = cliente.get("/busca", params={"q": "dicionarios chaves", "k": 2})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 2
    assert set(corpo[0]) == {"titulo", "arquivo", "score", "trecho"}
    assert corpo[0]["arquivo"] == "02-dicionarios.md"


@pytest.mark.parametrize("url", ["/busca", "/busca?q=", "/busca?q=%20%20", "/busca?q=x&k=0", "/busca?q=x&k=11"])
def test_busca_valida_parametros(cliente, url):
    assert cliente.get(url).status_code == 422


@pytest.mark.parametrize(
    "params",
    [{}, {"q": ""}, {"q": "   "}, {"q": "x" * 501}, {"q": "listas", "k": 0}, {"q": "listas", "k": 11}],
)
def test_busca_invalida_da_422_sem_carregar_o_modelo(monkeypatch, params):
    chamadas = []
    monkeypatch.setattr("q3_busca.router.obter_buscador", lambda: chamadas.append(1))
    resposta = TestClient(app_de_teste).get("/busca", params=params)
    assert resposta.status_code == 422
    assert isinstance(resposta.json()["detail"], list)
    assert chamadas == []


def test_busca_k_maior_que_corpus_json_valido(cliente):
    resposta = cliente.get("/busca", params={"q": "listas", "k": 10})
    assert resposta.status_code == 200
    assert len(resposta.json()) == 3


def test_cli_consulta(capsys, monkeypatch, buscador_falso):
    monkeypatch.setattr("q3_busca.__main__.obter_buscador", lambda: buscador_falso)
    assert main(["dicionarios chaves", "-k", "2"]) == 0
    saida = capsys.readouterr().out
    assert "1. [" in saida and "2. [" in saida and "Dicionários" in saida


def test_cli_demo(capsys, monkeypatch, buscador_falso):
    monkeypatch.setattr("q3_busca.__main__.obter_buscador", lambda: buscador_falso)
    monkeypatch.setattr("q3_busca.__main__.CONSULTAS_DEMO", [("listas append", "01-listas.md")])
    assert main(["--demo"]) == 0
    assert 'Consulta: "listas append"' in capsys.readouterr().out


def test_cli_sem_argumentos_sai_com_2():
    with pytest.raises(SystemExit) as saida:
        main([])
    assert saida.value.code == 2


def test_cli_demo_e_consulta_juntos_sai_com_2(monkeypatch, buscador_falso):
    monkeypatch.setattr("q3_busca.__main__.obter_buscador", lambda: buscador_falso)
    with pytest.raises(SystemExit) as saida:
        main(["listas", "--demo"])
    assert saida.value.code == 2


def test_cli_ctrl_c_sai_sem_traceback(monkeypatch):
    def interromper():
        raise KeyboardInterrupt

    monkeypatch.setattr("q3_busca.__main__.obter_buscador", interromper)
    assert main(["listas"]) == 0


def test_cli_k_invalido(capsys, monkeypatch, buscador_falso):
    monkeypatch.setattr("q3_busca.__main__.obter_buscador", lambda: buscador_falso)
    assert main(["listas", "-k", "0"]) == 2
    assert "k precisa" in capsys.readouterr().err
