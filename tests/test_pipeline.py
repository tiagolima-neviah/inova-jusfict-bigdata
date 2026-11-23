"""Testes da silver e da gold sobre uma bronze mínima montada em disco.

Sem banco: a bronze de teste é escrita em parquet numa pasta temporária, e as
etapas silver e gold rodam de verdade sobre ela (DuckDB em memória).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from inova_bigdata.config import Config
from inova_bigdata.pipeline import ReguaReprovou, gold, silver

SP = ZoneInfo("America/Sao_Paulo")
TS = pa.timestamp("us", tz="America/Sao_Paulo")

ESQUEMAS: dict[str, pa.Schema] = {
    "departamento": pa.schema([("id", pa.int16()), ("nome", pa.string())]),
    "papel": pa.schema([("id", pa.int16()), ("nome", pa.string()), ("nivel", pa.int16())]),
    "usuario": pa.schema(
        [
            ("id", pa.int32()),
            ("nome", pa.string()),
            ("login", pa.string()),
            ("cargo", pa.string()),
            ("papel_id", pa.int16()),
            ("ativo", pa.bool_()),
            ("demonstracao", pa.bool_()),
            ("criado_em", TS),
        ]
    ),
    "usuario_departamento": pa.schema([("usuario_id", pa.int32()), ("departamento_id", pa.int16())]),
    "inovacao": pa.schema(
        [
            ("id", pa.int32()),
            ("titulo", pa.string()),
            ("descricao", pa.string()),
            ("objetivo", pa.string()),
            ("beneficios", pa.string()),
            ("desafios", pa.string()),
            ("ferramentas_tecnicas", pa.string()),
            ("indicador_sucesso", pa.string()),
            ("prazo_desejado", pa.date32()),
            ("custo_tipo", pa.string()),
            ("custo_valor", pa.decimal128(12, 2)),
            ("destino", pa.string()),
            ("status", pa.string()),
            ("brainstorm_em", TS),
            ("brainstorm_local", pa.string()),
            ("autor_id", pa.int32()),
            ("departamento_id", pa.int16()),
            ("departamento_responsavel_id", pa.int16()),
            ("criada_em", TS),
            ("atualizada_em", TS),
            ("origem", pa.string()),
        ]
    ),
    "inovacao_historico": pa.schema(
        [
            ("id", pa.int32()),
            ("inovacao_id", pa.int32()),
            ("status_de", pa.string()),
            ("status_para", pa.string()),
            ("usuario_id", pa.int32()),
            ("observacao", pa.string()),
            ("em", TS),
        ]
    ),
    "interacao": pa.schema(
        [
            ("id", pa.int32()),
            ("inovacao_id", pa.int32()),
            ("autor_id", pa.int32()),
            ("texto", pa.string()),
            ("em", TS),
        ]
    ),
    "parecer_ia": pa.schema(
        [
            ("id", pa.int32()),
            ("inovacao_id", pa.int32()),
            ("score_0_100", pa.int16()),
            ("recomenda", pa.bool_()),
            ("resumo", pa.string()),
            ("custo_estimado", pa.string()),
            ("ganho_estimado", pa.string()),
            ("retorno_estimado_meses", pa.int16()),
            ("equipe_e_ferramentas", pa.string()),
            ("gerado_em", TS),
            ("modelo", pa.string()),
        ]
    ),
}


def _quando(dia: int, hora: int = 9) -> datetime:
    return datetime(2026, 3, dia, hora, 0, tzinfo=SP)


def _base_valida() -> dict[str, list[dict[str, Any]]]:
    """1 colaboradora, 1 supervisor, 1 diretor; 2 inovações, 1 delas implementada."""
    inovacao = {
        "descricao": "d",
        "objetivo": "o",
        "beneficios": "b",
        "desafios": None,
        "ferramentas_tecnicas": None,
        "indicador_sucesso": None,
        "prazo_desejado": None,
        "brainstorm_em": None,
        "brainstorm_local": None,
        "autor_id": 1,
        "departamento_id": 2,
        "origem": "sintetico",
    }
    return {
        "departamento": [{"id": 2, "nome": "Tecnologia "}],  # com espaço sobrando: a silver apara
        "papel": [
            {"id": 1, "nome": "colaborador", "nivel": 1},
            {"id": 2, "nome": "supervisor", "nivel": 2},
            {"id": 3, "nome": "diretor", "nivel": 3},
        ],
        "usuario": [
            {"id": 1, "nome": "Ana", "login": "ana", "cargo": "Analista", "papel_id": 1},
            {"id": 2, "nome": "Elias", "login": "elias", "cargo": "Coordenador", "papel_id": 2},
            {"id": 3, "nome": "Davi", "login": "davi", "cargo": "Diretor", "papel_id": 3},
        ],
        "usuario_departamento": [
            {"usuario_id": 1, "departamento_id": 2},
            {"usuario_id": 2, "departamento_id": 2},
        ],
        "inovacao": [
            inovacao
            | {
                "id": 10,
                "titulo": "Relatório automático",
                "custo_tipo": "sem_custo",
                "custo_valor": None,
                "destino": "automacao",
                "status": "implementada",
                "departamento_responsavel_id": 2,
                "criada_em": _quando(2),
                "atualizada_em": _quando(20),
            },
            inovacao
            | {
                "id": 11,
                "titulo": "Painel de chamados",
                "custo_tipo": "software",
                "custo_valor": Decimal("5000.00"),
                "destino": None,
                "status": "na_fila",
                "departamento_responsavel_id": None,
                "criada_em": _quando(10),
                "atualizada_em": _quando(10),
            },
        ],
        "inovacao_historico": [
            {
                "id": 1,
                "inovacao_id": 10,
                "status_de": None,
                "status_para": "na_fila",
                "usuario_id": 1,
                "em": _quando(2),
            },
            {
                "id": 2,
                "inovacao_id": 10,
                "status_de": "na_fila",
                "status_para": "em_avaliacao",
                "usuario_id": 2,
                "em": _quando(4),
            },
            {
                "id": 3,
                "inovacao_id": 10,
                "status_de": "em_avaliacao",
                "status_para": "em_avaliacao",
                "usuario_id": 2,
                "em": _quando(5),
            },
            {
                "id": 4,
                "inovacao_id": 10,
                "status_de": "em_avaliacao",
                "status_para": "com_diretor",
                "usuario_id": 2,
                "em": _quando(6),
            },
            {
                "id": 5,
                "inovacao_id": 10,
                "status_de": "com_diretor",
                "status_para": "em_escopo",
                "usuario_id": 3,
                "em": _quando(9),
            },
            {
                "id": 6,
                "inovacao_id": 10,
                "status_de": "em_escopo",
                "status_para": "em_implementacao",
                "usuario_id": 3,
                "em": _quando(12),
            },
            {
                "id": 7,
                "inovacao_id": 10,
                "status_de": "em_implementacao",
                "status_para": "implementada",
                "usuario_id": 3,
                "em": _quando(20),
            },
            {
                "id": 8,
                "inovacao_id": 11,
                "status_de": None,
                "status_para": "na_fila",
                "usuario_id": 1,
                "em": _quando(10),
            },
        ],
        "interacao": [
            {"id": 1, "inovacao_id": 10, "autor_id": 2, "texto": " Quantas pessoas? ", "em": _quando(4, 11)}
        ],
        "parecer_ia": [],
    }


def _escrever_bronze(lake: Path, base: dict[str, list[dict[str, Any]]]) -> Config:
    padrao_usuario = {"ativo": True, "demonstracao": False, "criado_em": _quando(1)}
    for tabela, esquema in ESQUEMAS.items():
        # campo ausente vira nulo no parquet; só o usuário ganha valores padrão
        linhas = [padrao_usuario | linha for linha in base[tabela]] if tabela == "usuario" else base[tabela]
        pasta = lake / "bronze" / tabela / "extracao=2026-03-21"
        pasta.mkdir(parents=True)
        pq.write_table(pa.Table.from_pylist(linhas, schema=esquema), pasta / f"{tabela}.parquet")
    return Config(plataforma_url="", staging_url="", dw_url="", lake=lake)


def _ler(arquivo: Path, consulta: str) -> list[tuple[Any, ...]]:
    return duckdb.connect().execute(consulta.format(t=f"read_parquet('{arquivo}')")).fetchall()


def test_base_valida_passa_na_silver_e_apara_texto(tmp_path: Path) -> None:
    cfg = _escrever_bronze(tmp_path, _base_valida())
    contagem = silver.transformar(cfg)
    assert contagem["inovacao"] == 2
    assert contagem["inovacao_historico"] == 8
    assert _ler(tmp_path / "silver" / "departamento.parquet", "SELECT nome FROM {t}") == [("Tecnologia",)]
    # o marco fino (status_de = status_para) é identificado na silver
    marcos = _ler(tmp_path / "silver" / "inovacao_historico.parquet", "SELECT id FROM {t} WHERE marco")
    assert marcos == [(3,)]


def test_status_fora_do_dominio_reprova_a_silver(tmp_path: Path) -> None:
    base = _base_valida()
    base["inovacao"][1]["status"] = "inventado"
    cfg = _escrever_bronze(tmp_path, base)
    with pytest.raises(ReguaReprovou) as reprovacao:
        silver.transformar(cfg)
    assert "inovacao: status fora do domínio" in reprovacao.value.reprovacoes


def test_historico_que_nao_encadeia_reprova_a_silver(tmp_path: Path) -> None:
    base = _base_valida()
    base["inovacao_historico"][4]["status_de"] = "brainstorm"  # pulou um passo que não existiu
    cfg = _escrever_bronze(tmp_path, base)
    with pytest.raises(ReguaReprovou) as reprovacao:
        silver.transformar(cfg)
    assert "historico: evento sem encadear com o anterior" in reprovacao.value.reprovacoes


def test_inovacao_orfa_de_autor_reprova_a_silver(tmp_path: Path) -> None:
    base = _base_valida()
    base["inovacao"][1]["autor_id"] = 999
    cfg = _escrever_bronze(tmp_path, base)
    with pytest.raises(ReguaReprovou) as reprovacao:
        silver.transformar(cfg)
    assert "inovacao: autor inexistente" in reprovacao.value.reprovacoes


def test_gold_calcula_os_marcos_e_as_medidas(tmp_path: Path) -> None:
    cfg = _escrever_bronze(tmp_path, _base_valida())
    silver.transformar(cfg)
    contagem = gold.modelar(cfg)
    assert contagem["fato_inovacao"] == 2
    assert contagem["fato_movimentacao"] == 8
    assert contagem["dim_status"] == 13
    fato = tmp_path / "gold" / "fato_inovacao.parquet"
    implementada = _ler(
        fato,
        "SELECT data_criacao, data_em_avaliacao, data_implementada, dias_ate_avaliacao, "
        "dias_ate_implementada, qtd_movimentacoes, qtd_interacoes, destino "
        "FROM {t} WHERE inovacao_id = 10",
    )
    assert implementada == [(date(2026, 3, 2), date(2026, 3, 4), date(2026, 3, 20), 2, 18, 5, 1, "automacao")]
    # o marco fino não conta como movimentação; quem não foi classificada cai em 'nao_classificado'
    na_fila = _ler(
        fato, "SELECT destino, qtd_movimentacoes, data_implementada FROM {t} WHERE inovacao_id = 11"
    )
    assert na_fila == [("nao_classificado", 0, None)]
