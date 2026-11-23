"""Conferência produção x warehouse: os números batem?

    uv run python -m inova_bigdata.pipeline.conferir

Compara, número por número, o que a plataforma tem (schema inova) com o que
o painel lê (schema dw). Depois de uma carga, tudo tem de bater; se alguém
cadastrou ou moveu uma inovação depois da carga, a diferença aparece aqui, e
é exatamente o que uma nova carga resolve. Sai com 0 se bate e 1 se difere.
"""

from __future__ import annotations

import sys

import psycopg

from inova_bigdata import config

COMPARACOES: dict[str, tuple[str, str]] = {
    "inovações": (
        "SELECT count(*) FROM inova.inovacao",
        "SELECT count(*) FROM dw.fato_inovacao",
    ),
    "eventos de histórico": (
        "SELECT count(*) FROM inova.inovacao_historico",
        "SELECT count(*) FROM dw.fato_movimentacao",
    ),
    "implementadas": (
        "SELECT count(*) FROM inova.inovacao WHERE status = 'implementada'",
        "SELECT count(*) FROM dw.fato_inovacao WHERE status = 'implementada'",
    ),
    "arquivadas": (
        "SELECT count(*) FROM inova.inovacao WHERE status = 'arquivo_morto'",
        "SELECT count(*) FROM dw.fato_inovacao WHERE status = 'arquivo_morto'",
    ),
    "na fila": (
        "SELECT count(*) FROM inova.inovacao WHERE status = 'na_fila'",
        "SELECT count(*) FROM dw.fato_inovacao WHERE status = 'na_fila'",
    ),
    "autores distintos": (
        "SELECT count(DISTINCT autor_id) FROM inova.inovacao",
        "SELECT count(DISTINCT autor_id) FROM dw.fato_inovacao",
    ),
    "custo estimado total (R$)": (
        "SELECT coalesce(sum(custo_valor), 0)::bigint FROM inova.inovacao",
        "SELECT coalesce(sum(custo_valor), 0)::bigint FROM dw.fato_inovacao",
    ),
    "com parecer da Têmis": (
        "SELECT count(DISTINCT inovacao_id) FROM inova.parecer_ia",
        "SELECT count(*) FROM dw.fato_inovacao WHERE score_temis IS NOT NULL",
    ),
}


def main() -> int:
    cfg = config.carregar()
    diferencas = 0
    with psycopg.connect(cfg.plataforma_url, options=config.FUSO) as conexao, conexao.cursor() as cursor:
        cursor.execute("SELECT carregado_em FROM dw.carga ORDER BY id DESC LIMIT 1")
        carga = cursor.fetchone()
        print(f"última carga do warehouse: {carga[0]:%d/%m/%Y %H:%M}" if carga else "warehouse sem carga")
        print(f"{'medida':<28}{'produção':>12}{'warehouse':>12}")
        for medida, (na_producao, no_warehouse) in COMPARACOES.items():
            cursor.execute(na_producao)
            producao = cursor.fetchone()
            cursor.execute(no_warehouse)
            warehouse = cursor.fetchone()
            a, b = (producao[0] if producao else None), (warehouse[0] if warehouse else None)
            marca = "" if a == b else "   <- difere"
            diferencas += a != b
            print(f"{medida:<28}{a!s:>12}{b!s:>12}{marca}")
    if diferencas:
        print(f"{diferencas} medida(s) diferem: o warehouse está atrás da produção; rode o pipeline.")
        return 1
    print("produção e warehouse batem em todas as medidas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
