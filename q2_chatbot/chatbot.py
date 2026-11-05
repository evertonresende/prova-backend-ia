"""Núcleo do chatbot da Q2: o modelo da OpenAI, o agente do LangChain e a memória.

Fluxo de cada pergunta: o agente monta [prompt de sistema + histórico da
conversa + pergunta], chama o modelo e salva a pergunta e a resposta no
histórico daquela conversa.
"""

import os

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

PROMPT_SISTEMA = """Você é um assistente especialista em Python.

- Responda sempre em português do Brasil.
- Explique em detalhes e inclua exemplos de código Python comentados sempre que eles ajudarem a entender.
- Se a pergunta não for sobre Python, diga com educação que você só ajuda com Python e convide a pessoa a perguntar algo sobre a linguagem.
- Cumprimentos e agradecimentos (como "Olá" ou "Obrigado") não são fora do tema: responda normalmente, com simpatia.
- Se não souber a resposta ou não tiver certeza, diga isso com clareza em vez de inventar."""

MODELO_PADRAO = "gpt-6-luna"
TIMEOUT_S = 60
MAX_TENTATIVAS = 2
ESFORCO_RACIOCINIO = "low"

MENSAGEM_SEM_CHAVE = (
    "OPENAI_API_KEY não definida. Copie .env.example para .env e preencha a chave. "
    "A API só lê o .env se subir com: uvicorn app.main:app --env-file .env"
)
MENSAGEM_FALHA_OPENAI = "Falha ao consultar o modelo da OpenAI. Tente de novo em instantes."


class ChaveAusenteError(RuntimeError):
    """A `OPENAI_API_KEY` não está definida no ambiente."""


def criar_modelo() -> ChatOpenAI:
    """Cria o modelo real da OpenAI a partir das variáveis de ambiente.

    Levanta `ChaveAusenteError` (com `MENSAGEM_SEM_CHAVE`) se faltar a chave.
    """
    # A checagem vem antes de construir: sem chave, o próprio construtor do
    # ChatOpenAI já falha, mas com um erro do SDK em inglês. Aqui ele vira uma
    # mensagem em PT-BR que o CLI e a API mostram sem traceback.
    if not os.getenv("OPENAI_API_KEY"):
        raise ChaveAusenteError(MENSAGEM_SEM_CHAVE)
    return ChatOpenAI(
        # `model` sempre explícito: sem ele, o padrão da classe é gpt-3.5-turbo.
        # `or` em vez do padrão do getenv para que `OPENAI_MODEL=` vazio no .env
        # também caia no modelo padrão.
        model=os.getenv("OPENAI_MODEL") or MODELO_PADRAO,
        # Por padrão o ChatOpenAI não tem timeout nenhum: uma chamada travada
        # prenderia o CLI ou a rota para sempre. O limite vale por tentativa, e o
        # teste `live` confere que a resposta real chega antes dele.
        timeout=TIMEOUT_S,
        # `max_retries` conta as novas tentativas depois da primeira.
        max_retries=MAX_TENTATIVAS,
        # O gpt-6-luna é modelo de raciocínio (padrão `medium`). `low` corta
        # latência e custo; pergunta de Python não pede raciocínio profundo.
        # `reasoning_effort` vai sempre: um `OPENAI_MODEL` sem raciocínio o recusa.
        reasoning_effort=ESFORCO_RACIOCINIO,
        # Sem `temperature`/`top_p` de propósito: a OpenAI manda removê-los nos
        # modelos de raciocínio quando o esforço não é `none`, e o
        # langchain-openai não os remove sozinho para a família gpt-6.
    )


def criar_chatbot(modelo: BaseChatModel) -> CompiledStateGraph:
    """Monta o agente do LangChain com memória por conversa.

    Recebe o modelo pronto: o código real passa `criar_modelo()` e os testes
    passam um modelo fake, sem rede.
    """
    # Memória por `thread_id`: o checkpointer guarda o estado do grafo (a lista
    # de mensagens) separado por `thread_id`, e cada `conversa_id` é usado como
    # `thread_id`. Assim cada conversa tem o próprio histórico, e conversas
    # diferentes não se misturam. O prompt de sistema não entra no histórico: o
    # agente o coloca na frente das mensagens a cada chamada ao modelo.
    # Sem ferramentas (`tools=[]`), o agente é um único nó de modelo: não há
    # laço de ferramentas nem `bind_tools`.
    # Limitação: a memória é volátil (some quando o processo reinicia) e não tem
    # limite de tamanho (o histórico inteiro vai para o modelo a cada pergunta).
    # Duas perguntas simultâneas no mesmo `conversa_id` partem do mesmo histórico,
    # e a última gravação vence (um turno some da memória).
    # Em produção: checkpointer em SQLite/Postgres, corte do histórico e uma trava
    # por conversa.
    return create_agent(
        model=modelo,
        tools=[],
        system_prompt=PROMPT_SISTEMA,
        checkpointer=InMemorySaver(),
    )


def perguntar(chatbot: CompiledStateGraph, pergunta: str, conversa_id: str, origem: str) -> str:
    """Envia `pergunta` na conversa `conversa_id` e devolve o texto da resposta.

    `origem` (`cli` ou `api`) vira tag e metadata do run, para filtrar os traces
    no LangSmith quando o tracing estiver ligado.
    """
    resultado = chatbot.invoke(
        # Só a mensagem nova: o histórico vem do checkpointer, pelo `thread_id`.
        {"messages": [HumanMessage(pergunta)]},
        config={
            "configurable": {"thread_id": conversa_id},
            "tags": [origem],
            "metadata": {"origem": origem},
        },
    )
    # `.text` e não `.content`: em modelos de raciocínio o `content` pode vir
    # como lista de blocos; `.text` junta só os blocos de texto numa string.
    return resultado["messages"][-1].text
