"""Linha de comando do gerador sintético.

    uv run python -m inova_bigdata.gerador              # simula, confere e grava
    uv run python -m inova_bigdata.gerador --so-conferir  # simula e confere, sem tocar o banco

Recria só o que é sintético: inovações com origem 'sintetico' e os
colaboradores que não são de demonstração. O que foi cadastrado na tela fica.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from inova_bigdata import config
from inova_bigdata.gerador import carga, regua, simulacao


def main() -> int:
    parser = argparse.ArgumentParser(description="Gerador sintético da JusFict Inova.")
    parser.add_argument("--so-conferir", action="store_true", help="não grava no banco")
    parser.add_argument("--semente", type=int, default=simulacao.SEMENTE)
    args = parser.parse_args()

    base = simulacao.gerar(args.semente)
    por_status = Counter(inovacao.status for inovacao in base.inovacoes)
    por_ano = Counter(inovacao.criada_em.year for inovacao in base.inovacoes)
    print(f"simulação: {len(base.pessoas)} pessoas, {len(base.inovacoes)} inovações (semente {args.semente})")
    print("  por ano:    " + ", ".join(f"{ano}: {n}" for ano, n in sorted(por_ano.items())))
    print("  por status: " + ", ".join(f"{status}: {n}" for status, n in por_status.most_common()))

    erros = regua.conferir(base)
    if erros:
        print(f"RÉGUA REPROVOU ({len(erros)} problemas); nada foi gravado:", file=sys.stderr)
        for erro in erros[:20]:
            print(f"  - {erro}", file=sys.stderr)
        return 1
    print("régua do sintético: aprovada")

    if args.so_conferir:
        return 0
    cfg = config.carregar()
    if not cfg.plataforma_url:
        print("PLATAFORMA_URL ausente: copie .env.example para .env e preencha.", file=sys.stderr)
        return 1
    linhas = carga.gravar(cfg.plataforma_url, base)
    print("gravado no schema inova: " + ", ".join(f"{tabela}: {n}" for tabela, n in linhas.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
