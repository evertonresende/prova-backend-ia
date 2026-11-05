"""CLI da Q2: `python -m q2_chatbot` (conversa no terminal) ou `python -m q2_chatbot --demo`.

Todas as perguntas de uma execução ficam na mesma conversa: o bot lembra do que
já foi dito até o programa terminar.
"""

import argparse
import sys
from uuid import uuid4

import openai
from dotenv import load_dotenv
from langchain_core.tracers.langchain import wait_for_all_tracers
from langgraph.graph.state import CompiledStateGraph

from q2_chatbot.chatbot import (
    MENSAGEM_FALHA_OPENAI,
    MENSAGEM_SEM_CHAVE,
    ChaveAusenteError,
    criar_chatbot,
    criar_modelo,
    perguntar,
)

# 1) o exemplo do enunciado; 2) uma continuação que só faz sentido com o histórico
# ("nela" = a lista da resposta anterior); 3) uma pergunta fora do tema, para
# mostrar que o bot se limita a Python.
PERGUNTAS_DEMO = [
    "Como criar uma lista em Python?",
    "E como adiciono um item nela?",
    "Qual é a capital da França?",
]


def _responder(chatbot: CompiledStateGraph, pergunta: str, conversa_id: str) -> bool:
    """Imprime a resposta do bot; numa falha da OpenAI, avisa no stderr e devolve False."""
    try:
        resposta = perguntar(chatbot, pergunta, conversa_id, "cli")
    except openai.OpenAIError as erro:
        # O CLI roda no terminal de quem tem a chave, e o detalhe (chave inválida,
        # modelo inexistente, cota esgotada) é o que permite corrigir o problema.
        # Na API, o detalhe fica só no log do servidor.
        print(MENSAGEM_FALHA_OPENAI, file=sys.stderr)
        print(f"Detalhe: {erro}", file=sys.stderr)
        return False
    print(f"Bot: {resposta}\n")
    return True


def _rodar_demo(chatbot: CompiledStateGraph, conversa_id: str) -> int:
    """Faz as `PERGUNTAS_DEMO` em ordem; devolve 1 se alguma falhar.

    Uma falha não interrompe a demo: as outras perguntas ainda rodam, e o código
    de saída avisa que algo deu errado.
    """
    falhas = 0
    for pergunta in PERGUNTAS_DEMO:
        # `flush`: com a saída redirecionada (`| tee`), o stdout fica em buffer, e o
        # aviso de falha, que vai para o stderr, sairia antes da pergunta.
        print(f"Você: {pergunta}", flush=True)
        if not _responder(chatbot, pergunta, conversa_id):
            falhas += 1
    return 1 if falhas else 0


def _rodar_interativo(chatbot: CompiledStateGraph, conversa_id: str) -> int:
    """Lê perguntas do terminal até `sair`; uma falha da OpenAI não encerra o loop."""
    print("Chatbot de Python — digite 'sair' para encerrar.")
    while True:
        pergunta = input("Você: ").strip()
        if not pergunta:
            continue
        if pergunta.lower() == "sair":
            return 0
        _responder(chatbot, pergunta, conversa_id)


def main(argv: list[str] | None = None) -> int:
    """Roda o chatbot no terminal e devolve o código de saída do processo.

    0 = tudo certo; 1 = sem `OPENAI_API_KEY` ou alguma pergunta da demo falhou.
    """
    # No Windows, com a saída redirecionada (`> arquivo`, `| tee`), o Python grava
    # em cp1252. Os acentos do português cabem, mas um "→" ou um emoji na resposta
    # do modelo derrubaria o CLI com `UnicodeEncodeError` (traceback). Com
    # `errors="replace"`, o caractere que não cabe vira "?".
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(errors="replace")

    parser = argparse.ArgumentParser(
        prog="python -m q2_chatbot",
        description="Chatbot especialista em Python (LangChain + OpenAI).",
    )
    parser.add_argument("--demo", action="store_true", help="faz as perguntas de exemplo e sai")
    args = parser.parse_args(argv)

    try:
        chatbot = criar_chatbot(criar_modelo())
    except ChaveAusenteError:
        print(MENSAGEM_SEM_CHAVE, file=sys.stderr)
        return 1

    # Um id por execução: a memória guarda as perguntas e respostas desta sessão
    # sob esse id (o `thread_id` do LangGraph).
    conversa_id = str(uuid4())
    try:
        if args.demo:
            return _rodar_demo(chatbot, conversa_id)
        return _rodar_interativo(chatbot, conversa_id)
    except (EOFError, KeyboardInterrupt):
        # Ctrl+D (EOFError) ou Ctrl+C (KeyboardInterrupt), na digitação ou na
        # espera da resposta: encerra sem traceback. A linha em branco evita que o
        # prompt do shell apareça grudado no "Você: ".
        print()
        return 0
    finally:
        # Os traces do LangSmith (quando o tracing está ligado) sobem numa thread
        # em segundo plano. Sem esperar por ela, o processo pode terminar antes do
        # envio, e o trace desta execução se perde.
        wait_for_all_tracers()


if __name__ == "__main__":
    # O .env só é lido aqui, no ponto de entrada: os testes chamam `main()` direto
    # e não podem herdar a chave real do desenvolvedor.
    load_dotenv()
    sys.exit(main())
