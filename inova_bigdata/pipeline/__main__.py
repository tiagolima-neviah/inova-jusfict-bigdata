"""O comando único do pipeline.

    uv run python -m inova_bigdata.pipeline                # todas as etapas, em ordem
    uv run python -m inova_bigdata.pipeline silver gold    # só as etapas pedidas

Sai com código 0 se tudo passou e 1 se alguma etapa falhou ou se uma régua de
qualidade reprovou. Uma etapa que falha interrompe as seguintes: gold nunca
é modelada sobre uma silver reprovada, e o warehouse nunca recebe gold ruim.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable

from inova_bigdata import config
from inova_bigdata.pipeline import ReguaReprovou, bronze, gold, silver, staging, warehouse

Etapa = Callable[[config.Config], dict[str, int]]

ETAPAS: dict[str, tuple[str, Etapa]] = {
    "staging": ("produção (Neon) -> staging (Postgres local)", staging.extrair),
    "bronze": ("staging -> parquet com linhagem", bronze.gravar),
    "silver": ("limpeza, tipos e régua de qualidade", silver.transformar),
    "gold": ("star schema e régua da modelagem", gold.modelar),
    "warehouse": ("gold -> schema dw (Neon)", warehouse.carregar),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline de dados da JusFict Inova.")
    parser.add_argument("etapas", nargs="*", choices=[*ETAPAS, []], help="padrão: todas, em ordem")
    args = parser.parse_args()
    pedidas = args.etapas or list(ETAPAS)

    cfg = config.carregar()
    if not cfg.plataforma_url or not cfg.staging_url:
        print(
            "PLATAFORMA_URL ou STAGING_URL ausente: copie .env.example para .env e preencha.", file=sys.stderr
        )
        return 1

    inicio_total = time.perf_counter()
    for nome in ETAPAS:  # sempre na ordem do pipeline, não na ordem digitada
        if nome not in pedidas:
            continue
        descricao, funcao = ETAPAS[nome]
        inicio = time.perf_counter()
        try:
            linhas = funcao(cfg)
        except ReguaReprovou as reprovacao:
            print(f"[{nome}] RÉGUA REPROVOU; o pipeline para aqui:", file=sys.stderr)
            for regra, quantidade in reprovacao.reprovacoes.items():
                print(f"    {regra}: {quantidade}", file=sys.stderr)
            return 1
        except Exception as erro:  # noqa: BLE001
            print(f"[{nome}] FALHOU: {type(erro).__name__}: {erro}", file=sys.stderr)
            if nome == "staging":
                print("    o staging está de pé? rode: docker compose up -d", file=sys.stderr)
            return 1
        duracao = time.perf_counter() - inicio
        resumo = ", ".join(f"{tabela} {quantidade}" for tabela, quantidade in linhas.items())
        print(f"[{nome}] ok em {duracao:.1f}s · {descricao}")
        print(f"    {resumo}")
    print(f"pipeline concluído em {time.perf_counter() - inicio_total:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
