"""Etapa 5 · warehouse: a gold vira tabelas no schema dw do Neon.

Problema que resolve: o painel (e qualquer ferramenta de BI) precisa de um
banco para consultar. A carga é completa e atômica: tudo acontece numa
transação só, então quem está lendo o painel nunca vê tabela pela metade.
A tabela dw.carga guarda quando cada carga aconteceu: é dela que o painel
tira o "dados atualizados em".
"""

from __future__ import annotations

import json
from typing import Any

import psycopg
import pyarrow as pa
import pyarrow.parquet as pq

from inova_bigdata.config import FUSO, Config

TABELAS = (
    "dim_data",
    "dim_departamento",
    "dim_usuario",
    "dim_status",
    "dim_destino",
    "fato_inovacao",
    "fato_movimentacao",
)


def _tipo_postgres(tipo: Any) -> str:
    if pa.types.is_boolean(tipo):
        return "boolean"
    if pa.types.is_int64(tipo) or pa.types.is_uint32(tipo):
        return "bigint"
    if pa.types.is_integer(tipo):
        return "integer"
    if pa.types.is_floating(tipo):
        return "double precision"
    if pa.types.is_decimal(tipo):
        return f"numeric({tipo.precision}, {tipo.scale})"
    if pa.types.is_date(tipo):
        return "date"
    if pa.types.is_timestamp(tipo):
        return "timestamp"
    return "text"


def carregar(cfg: Config) -> dict[str, int]:
    """Recria as tabelas do dw a partir dos parquets da gold, numa transação."""
    contagem: dict[str, int] = {}
    with psycopg.connect(cfg.dw_url, options=FUSO) as conexao, conexao.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS dw")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS dw.carga (
                id           integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                carregado_em timestamptz NOT NULL DEFAULT now(),
                linhas       jsonb NOT NULL
            )
            """
        )
        # Os nomes vêm da constante TABELAS e do esquema do parquet, nunca de entrada externa.
        for tabela in TABELAS:
            dados = pq.read_table(cfg.lake / "gold" / f"{tabela}.parquet")
            colunas = ", ".join(f"{campo.name} {_tipo_postgres(campo.type)}" for campo in dados.schema)
            cursor.execute(f"DROP TABLE IF EXISTS dw.{tabela}")
            cursor.execute(f"CREATE TABLE dw.{tabela} ({colunas})")
            nomes = ", ".join(dados.schema.names)
            with cursor.copy(f"COPY dw.{tabela} ({nomes}) FROM STDIN") as copia:
                for linha in dados.to_pylist():
                    copia.write_row(tuple(linha.values()))
            contagem[tabela] = dados.num_rows
        cursor.execute("CREATE INDEX ON dw.fato_inovacao (departamento_id)")
        cursor.execute("CREATE INDEX ON dw.fato_inovacao (data_criacao)")
        cursor.execute("CREATE INDEX ON dw.fato_movimentacao (inovacao_id)")
        cursor.execute("INSERT INTO dw.carga (linhas) VALUES (%s)", (json.dumps(contagem),))
    return contagem
