"""CLI da busca semântica: `python -m q3_busca "consulta" [-k N]` ou `python -m q3_busca --demo`."""

import argparse
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
    if not args.demo and not (args.consulta and args.consulta.strip()):
        parser.error("informe uma consulta ou use --demo.")
    if args.k < 1:
        print("k precisa ser pelo menos 1.", file=sys.stderr)
        return 2

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
