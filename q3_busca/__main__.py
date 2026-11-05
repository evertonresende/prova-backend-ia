"""CLI da busca semântica: `python -m q3_busca "consulta" [-k N]` ou `python -m q3_busca --demo`."""

import argparse
import logging
import sys

from q3_busca.demo import CONSULTAS_DEMO
from q3_busca.indice import Resultado, obter_buscador


def _imprimir(resultados: list[Resultado]) -> None:
    for i, r in enumerate(resultados, start=1):
        print(f"  {i}. [{r.score:.3f}] {r.titulo} ({r.arquivo})")
        print(f"     {r.trecho}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m q3_busca", description="Busca semântica nos posts sobre Python.")
    parser.add_argument("consulta", nargs="?", help="o que procurar, em linguagem natural")
    parser.add_argument("-k", type=int, default=3, help="quantos posts mostrar (padrão: 3)")
    parser.add_argument("--demo", action="store_true", help="roda as consultas de demonstração")
    args = parser.parse_args(argv)

    # Valida tudo antes de carregar o modelo: carregar leva segundos (e baixa ~0,49 GB na primeira
    # vez), e não faz sentido pagar isso para depois recusar a entrada.
    if args.demo and args.consulta is not None:
        parser.error("use uma consulta ou --demo, não os dois.")
    if not args.demo and not (args.consulta and args.consulta.strip()):
        parser.error("informe uma consulta ou use --demo.")
    if args.k < 1:
        print("k precisa ser pelo menos 1.", file=sys.stderr)
        return 2

    try:
        # No stderr para não misturar com os resultados no stdout.
        print("Carregando o modelo de embeddings (na primeira vez baixa ~0,49 GB)...", file=sys.stderr)
        buscador = obter_buscador()

        # CONSULTAS_DEMO é lido aqui, na hora da chamada, para o teste poder trocá-lo com monkeypatch.
        consultas = [c for c, _ in CONSULTAS_DEMO] if args.demo else [args.consulta]
        try:
            for consulta in consultas:
                if args.demo:
                    print(f'Consulta: "{consulta}"')
                _imprimir(buscador.buscar(consulta, args.k))
                if args.demo:
                    print()
        except ValueError as erro:
            print(erro, file=sys.stderr)
            return 2
    except KeyboardInterrupt:
        # Ctrl+C durante a carga do modelo (que leva segundos e, na primeira vez, baixa ~0,49 GB)
        # ou a busca: encerra sem traceback, como o CLI da Q2. A linha em branco evita que o
        # prompt do shell apareça grudado no "^C".
        print(file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    # O log é configurado só aqui, no ponto de entrada (os testes chamam `main()` direto e ficam
    # quietos). Com ele, o aviso de `indice.py` de que o índice está sendo criado aparece no stderr
    # (o StreamHandler escreve no stderr e, sem formatter, só a mensagem). O handler fica no logger
    # do pacote, e não na raiz (`basicConfig`): o huggingface_hub já tem handler próprio e também
    # propaga para a raiz, então um handler lá imprimiria cada aviso dele duas vezes.
    logger_q3 = logging.getLogger("q3_busca")
    logger_q3.addHandler(logging.StreamHandler())
    logger_q3.setLevel(logging.INFO)
    sys.exit(main())
