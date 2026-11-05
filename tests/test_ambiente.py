import os


def test_ambiente_de_teste_sem_chave_e_sem_tracing():
    assert "OPENAI_API_KEY" not in os.environ
    for nome in ("LANGSMITH_TRACING", "LANGSMITH_TRACING_V2", "LANGCHAIN_TRACING", "LANGCHAIN_TRACING_V2"):
        assert os.environ[nome] == "false"


def test_slow_e_live_ficam_de_fora_por_padrao(pytestconfig):
    assert pytestconfig.getoption("markexpr") == "not slow and not live"
