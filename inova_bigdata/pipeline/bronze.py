"""Etapa 2 · bronze: a foto fiel do staging em parquet, com linhagem.

Problema que resolve: guardar a origem como ela era no dia da extração, em
formato colunar barato, para reprocessar silver e gold sem voltar ao banco.
Nenhuma regra de negócio aqui: só tipo certo e 2 colunas de linhagem
(`_extraido_em` e `_origem`). Uma pasta por dia de extração.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import psycopg
import pyarrow as pa
import pyarrow.parquet as pq

from inova_bigdata.config import FUSO, Config
from inova_bigdata.pipeline import TABELAS

FUSO_LOCAL = "America/Sao_Paulo"

# OID do tipo no Postgres -> tipo Arrow. Explícito para que tabela vazia
# (parecer_ia antes da Têmis) tenha o mesmo esquema de tabela cheia.
_ARROW_POR_OID: dict[int, Any] = {
    16: pa.bool_(),
    20: pa.int64(),
    21: pa.int16(),
    23: pa.int32(),
    25: pa.string(),
    1043: pa.string(),
    1082: pa.date32(),
    1184: pa.timestamp("us", tz=FUSO_LOCAL),
    1700: pa.decimal128(12, 2),
}


def pasta_da_extracao(cfg: Config, tabela: str, quando: datetime) -> Path:
    return cfg.lake / "bronze" / tabela / f"extracao={quando:%Y-%m-%d}"


def gravar(cfg: Config, quando: datetime | None = None) -> dict[str, int]:
    """Lê cada tabela do staging e grava um parquet na pasta do dia."""
    quando = quando or datetime.now(ZoneInfo(FUSO_LOCAL))
    contagem: dict[str, int] = {}
    with psycopg.connect(cfg.staging_url, options=FUSO) as conexao, conexao.cursor() as cursor:
        for tabela, colunas_sql in TABELAS.items():
            cursor.execute(f"SELECT {colunas_sql} FROM inova.{tabela}")
            descricao = cursor.description or []
            linhas = cursor.fetchall()
            colunas = list(zip(*linhas, strict=True)) if linhas else [() for _ in descricao]
            dados = {
                campo.name: pa.array(list(valores), type=_ARROW_POR_OID[campo.type_code])
                for campo, valores in zip(descricao, colunas, strict=True)
            }
            dados["_extraido_em"] = pa.array([quando] * len(linhas), type=pa.timestamp("us", tz=FUSO_LOCAL))
            dados["_origem"] = pa.array([f"staging.inova.{tabela}"] * len(linhas), type=pa.string())
            pasta = pasta_da_extracao(cfg, tabela, quando)
            pasta.mkdir(parents=True, exist_ok=True)
            pq.write_table(pa.table(dados), pasta / f"{tabela}.parquet")
            contagem[tabela] = len(linhas)
    return contagem
