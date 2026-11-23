"""O que a Têmis lê e grava na produção da plataforma (schema inova).

Leitura: as inovações que ainda não têm parecer (ou todas, com `refazer`).
Gravação: uma linha nova em inova.parecer_ia por parecer, nunca um UPDATE; o
histórico fica, e a gold usa sempre o parecer mais recente de cada inovação.
"""

from __future__ import annotations

from typing import Any

import psycopg

from inova_bigdata.config import FUSO
from inova_bigdata.temis.parecer import Inovacao, Parecer

_PENDENTES = """
    SELECT i.id, i.titulo, i.descricao, i.objetivo, i.beneficios, i.desafios, i.ferramentas_tecnicas,
           i.indicador_sucesso, i.prazo_desejado, i.custo_tipo, i.custo_valor, i.destino, i.status, d.nome,
           (
               SELECT h.observacao
               FROM inova.inovacao_historico h
               WHERE h.inovacao_id = i.id
                 AND h.status_para IN ('arquivo_morto_sugerido', 'arquivo_morto_proposto', 'arquivo_morto')
                 AND h.observacao IS NOT NULL
               ORDER BY h.em DESC
               LIMIT 1
           )
    FROM inova.inovacao i
    JOIN inova.departamento d ON d.id = i.departamento_id
    WHERE %(refazer)s OR NOT EXISTS (SELECT 1 FROM inova.parecer_ia p WHERE p.inovacao_id = i.id)
    ORDER BY i.criada_em DESC, i.id DESC
    LIMIT %(limite)s
"""


def conectar(url: str) -> psycopg.Connection[Any]:
    # autocommit: cada parecer gravado fica gravado, mesmo se o lote cair no meio.
    return psycopg.connect(url, options=FUSO, autocommit=True)


def contar_pendentes(conexao: psycopg.Connection[Any]) -> int:
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*) FROM inova.inovacao i
            WHERE NOT EXISTS (SELECT 1 FROM inova.parecer_ia p WHERE p.inovacao_id = i.id)
            """
        )
        linha = cursor.fetchone()
    return int(linha[0]) if linha else 0


def pendentes(conexao: psycopg.Connection[Any], limite: int | None, refazer: bool = False) -> list[Inovacao]:
    """As inovações a avaliar, das mais novas para as mais antigas."""
    with conexao.cursor() as cursor:
        cursor.execute(_PENDENTES, {"refazer": refazer, "limite": limite})
        return [Inovacao(*linha) for linha in cursor.fetchall()]


def gravar(conexao: psycopg.Connection[Any], inovacao_id: int, parecer: Parecer, modelo: str) -> None:
    with conexao.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO inova.parecer_ia
                (inovacao_id, score_0_100, recomenda, resumo, custo_estimado, ganho_estimado,
                 retorno_estimado_meses, equipe_e_ferramentas, modelo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                inovacao_id,
                parecer.score_0_100,
                parecer.recomenda,
                parecer.resumo,
                parecer.custo_estimado,
                parecer.ganho_estimado,
                parecer.retorno_estimado_meses,
                parecer.equipe_e_ferramentas,
                modelo,
            ),
        )
