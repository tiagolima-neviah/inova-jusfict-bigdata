"""Etapa 1 · staging: copia a produção para um Postgres local.

Problema que resolve: consulta analítica não pode causar lentidão no sistema
que as pessoas usam. A extração é uma leitura simples por tabela (COPY); tudo
que é pesado acontece depois, longe da produção.

Carga completa a cada execução: com centenas de linhas, recarregar tudo é mais
simples e mais seguro do que controlar incremento. O limite dessa escolha
está documentado no runbook.
"""

from __future__ import annotations

import subprocess
from typing import Any

import psycopg

from inova_bigdata.config import FUSO, RAIZ, Config
from inova_bigdata.pipeline import TABELAS


def garantir_staging(cfg: Config) -> bool:
    """Sobe o container do staging se ele não estiver respondendo.

    Devolve True se precisou subir. O staging é descartável (a extração recria
    tudo), então subir sob demanda é seguro; e o WSL desliga a distro quando
    ninguém a usa, o que derruba o container entre uma execução e outra.
    """
    try:
        psycopg.connect(cfg.staging_url, connect_timeout=3).close()
        return False
    except psycopg.OperationalError:
        subprocess.run(
            ["docker", "compose", "up", "-d", "--wait"],
            cwd=RAIZ,
            check=True,
            capture_output=True,
            timeout=240,
        )
        return True


def _tipos(origem: psycopg.Connection[Any], tabela: str, colunas: list[str]) -> list[tuple[str, str]]:
    """O tipo de cada coluna na origem, para recriar a tabela igual no staging."""
    linhas = origem.execute(
        """
        SELECT a.attname, format_type(a.atttypid, a.atttypmod)
        FROM pg_attribute a
        WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped
        """,
        (f"inova.{tabela}",),
    ).fetchall()
    tipo = dict(linhas)
    return [(coluna, tipo[coluna]) for coluna in colunas]


def extrair(cfg: Config) -> dict[str, int]:
    """Recria cada tabela no staging e copia as linhas da produção."""
    garantir_staging(cfg)
    contagem: dict[str, int] = {}
    with (
        psycopg.connect(cfg.plataforma_url, options=FUSO) as origem,
        psycopg.connect(cfg.staging_url, options=FUSO) as destino,
    ):
        destino.execute("CREATE SCHEMA IF NOT EXISTS inova")
        destino.execute(
            """
            CREATE TABLE IF NOT EXISTS inova._carga (
                tabela      text PRIMARY KEY,
                linhas      integer NOT NULL,
                extraido_em timestamptz NOT NULL
            )
            """
        )
        # Os nomes de tabela e coluna vêm da constante TABELAS, nunca de entrada externa.
        for tabela, colunas_sql in TABELAS.items():
            colunas = [coluna.strip() for coluna in colunas_sql.split(",")]
            definicao = ", ".join(f"{coluna} {tipo}" for coluna, tipo in _tipos(origem, tabela, colunas))
            destino.execute(f"DROP TABLE IF EXISTS inova.{tabela}")
            destino.execute(f"CREATE TABLE inova.{tabela} ({definicao})")
            with (
                origem.cursor().copy(f"COPY (SELECT {colunas_sql} FROM inova.{tabela}) TO STDOUT") as saida,
                destino.cursor().copy(f"COPY inova.{tabela} ({colunas_sql}) FROM STDIN") as entrada,
            ):
                for bloco in saida:
                    entrada.write(bloco)
            linha = destino.execute(f"SELECT count(*) FROM inova.{tabela}").fetchone()
            contagem[tabela] = int(linha[0]) if linha else 0
            destino.execute(
                """
                INSERT INTO inova._carga (tabela, linhas, extraido_em) VALUES (%s, %s, now())
                ON CONFLICT (tabela) DO UPDATE
                SET linhas = EXCLUDED.linhas, extraido_em = EXCLUDED.extraido_em
                """,
                (tabela, contagem[tabela]),
            )
    return contagem
