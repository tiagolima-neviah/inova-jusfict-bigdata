"""Etapa 4 · gold: o star schema, no grão dia.

Problema que resolve: "um número só" para cada pergunta do negócio. Em vez de
cada relatório recalcular à sua maneira, a regra de cálculo mora aqui, uma
vez. 5 dimensões e 2 fatos:

- dim_data, dim_departamento, dim_usuario, dim_status, dim_destino
- fato_inovacao: 1 linha por inovação, com a data de cada marco e as medidas
- fato_movimentacao: 1 linha por evento do histórico (a trilha de auditoria)

A régua da gold confere que nada se perdeu nem se duplicou na modelagem.
"""

from __future__ import annotations

import json

import duckdb

from inova_bigdata.config import Config
from inova_bigdata.pipeline import ReguaReprovou

# (status, rótulo da interface, ordem no funil, grupo, está no trilho?)
# O funil do painel usa só os 8 do trilho; os demais são desfechos fora dele.
STATUS = (
    ("na_fila", "Na fila", 1, "em andamento", True),
    ("em_avaliacao", "Em avaliação", 2, "em andamento", True),
    ("com_diretor", "Com o diretor", 3, "em andamento", True),
    ("brainstorm", "Brainstorm", 4, "em andamento", True),
    ("em_escopo", "Em escopo", 5, "em andamento", True),
    ("mvp", "MVP", 6, "em andamento", True),
    ("em_implementacao", "Em implementação", 7, "em andamento", True),
    ("implementada", "Implementada", 8, "implementada", True),
    ("arquivo_morto_sugerido", "Arquivamento sugerido", 9, "em arquivamento", False),
    ("arquivo_morto_proposto", "Arquivamento proposto", 10, "em arquivamento", False),
    ("arquivo_morto", "Arquivada", 11, "arquivada", False),
    ("em_espera", "Em espera · revisitar", 12, "em espera", False),
    ("ja_existe", "Já existe", 13, "já existe", False),
)
DESTINOS = (
    ("app", "Aplicativo"),
    ("automacao", "Automação"),
    ("relatorio", "Relatório"),
    ("processo", "Processo (sem TI)"),
    ("outro", "Outro"),
    ("nao_classificado", "Ainda não classificado"),
)

_VALORES_STATUS = ", ".join(
    f"('{status}', '{rotulo}', {ordem}, '{grupo}', {str(trilho).lower()})"
    for status, rotulo, ordem, grupo, trilho in STATUS
)
_VALORES_DESTINO = ", ".join(f"('{destino}', '{rotulo}')" for destino, rotulo in DESTINOS)


def _primeira_vez(status: str) -> str:
    """Data em que a inovação entrou num status pela primeira vez."""
    return f"CAST(min(em) FILTER (WHERE status_para = '{status}' AND NOT marco) AS DATE)"


MODELO: dict[str, str] = {
    "dim_data": """
        SELECT CAST(dia AS DATE) AS data,
               year(dia) AS ano,
               month(dia) AS mes,
               strftime(dia, '%Y-%m') AS ano_mes,
               quarter(dia) AS trimestre,
               isodow(dia) AS dia_da_semana,
               isodow(dia) < 6 AS dia_util
        FROM generate_series(
            (SELECT CAST(min(criada_em) AS DATE) FROM s_inovacao),
            (SELECT greatest(CAST(max(em) AS DATE), current_date) FROM s_inovacao_historico),
            INTERVAL 1 DAY
        ) AS serie(dia)
    """,
    "dim_departamento": "SELECT id AS departamento_id, nome FROM s_departamento",
    "dim_usuario": """
        SELECT id AS usuario_id, nome, cargo, papel, nivel, departamento_id, demonstracao
        FROM s_usuario
    """,
    "dim_status": f"""
        SELECT * FROM (VALUES {_VALORES_STATUS}) AS t(status, rotulo, ordem, grupo, no_trilho)
    """,
    "dim_destino": f"SELECT * FROM (VALUES {_VALORES_DESTINO}) AS t(destino, rotulo)",
    "fato_inovacao": f"""
        WITH marcos AS (
            SELECT inovacao_id,
                   {_primeira_vez("em_avaliacao")} AS data_em_avaliacao,
                   {_primeira_vez("com_diretor")} AS data_com_diretor,
                   {_primeira_vez("brainstorm")} AS data_brainstorm,
                   {_primeira_vez("em_escopo")} AS data_em_escopo,
                   {_primeira_vez("mvp")} AS data_mvp,
                   {_primeira_vez("em_implementacao")} AS data_em_implementacao,
                   {_primeira_vez("implementada")} AS data_implementada,
                   {_primeira_vez("arquivo_morto")} AS data_arquivada,
                   CAST(max(em) AS DATE) AS data_ultima_movimentacao,
                   count(*) FILTER (WHERE NOT marco) - 1 AS qtd_movimentacoes
            FROM s_inovacao_historico
            GROUP BY inovacao_id
        ),
        conversas AS (
            SELECT inovacao_id, count(*) AS qtd_interacoes FROM s_interacao GROUP BY inovacao_id
        ),
        pareceres AS (
            SELECT inovacao_id,
                   arg_max(score_0_100, gerado_em) AS score_temis,
                   arg_max(recomenda, gerado_em) AS temis_recomenda
            FROM s_parecer_ia
            GROUP BY inovacao_id
        )
        SELECT i.id AS inovacao_id,
               i.titulo,
               CAST(i.criada_em AS DATE) AS data_criacao,
               i.autor_id,
               i.departamento_id,
               i.departamento_responsavel_id,
               i.status,
               coalesce(i.destino, 'nao_classificado') AS destino,
               i.custo_tipo,
               CAST(i.custo_valor AS DOUBLE) AS custo_valor,
               i.origem,
               m.data_em_avaliacao,
               m.data_com_diretor,
               m.data_brainstorm,
               m.data_em_escopo,
               m.data_mvp,
               m.data_em_implementacao,
               m.data_implementada,
               m.data_arquivada,
               m.data_ultima_movimentacao,
               date_diff('day', CAST(i.criada_em AS DATE), m.data_em_avaliacao) AS dias_ate_avaliacao,
               date_diff('day', CAST(i.criada_em AS DATE), m.data_com_diretor) AS dias_ate_diretor,
               date_diff('day', CAST(i.criada_em AS DATE), m.data_implementada) AS dias_ate_implementada,
               date_diff('day', m.data_ultima_movimentacao, current_date) AS dias_no_status_atual,
               m.qtd_movimentacoes,
               coalesce(c.qtd_interacoes, 0) AS qtd_interacoes,
               p.score_temis,
               p.temis_recomenda
        FROM s_inovacao i
        JOIN marcos m ON m.inovacao_id = i.id
        LEFT JOIN conversas c ON c.inovacao_id = i.id
        LEFT JOIN pareceres p ON p.inovacao_id = i.id
    """,
    "fato_movimentacao": """
        SELECT h.id AS movimentacao_id,
               h.inovacao_id,
               CAST(h.em AS DATE) AS data,
               h.em AS momento,
               coalesce(h.status_de, 'criacao') AS status_de,
               h.status_para,
               h.usuario_id,
               i.departamento_id,
               h.marco,
               h.ordem,
               date_diff(
                   'day',
                   CAST(lag(h.em) OVER (PARTITION BY h.inovacao_id ORDER BY h.ordem) AS DATE),
                   CAST(h.em AS DATE)
               ) AS dias_desde_o_evento_anterior
        FROM s_inovacao_historico h
        JOIN s_inovacao i ON i.id = h.inovacao_id
    """,
}

REGUA: dict[str, str] = {
    "fato_inovacao: linhas diferem da silver": """
        SELECT abs((SELECT count(*) FROM g_fato_inovacao) - (SELECT count(*) FROM s_inovacao))
    """,
    "fato_inovacao: inovação repetida": """
        SELECT count(*) - count(DISTINCT inovacao_id) FROM g_fato_inovacao
    """,
    "fato_movimentacao: linhas diferem da silver": """
        SELECT abs((SELECT count(*) FROM g_fato_movimentacao) - (SELECT count(*) FROM s_inovacao_historico))
    """,
    "fato_inovacao: status sem dimensão": """
        SELECT count(*) FROM g_fato_inovacao f ANTI JOIN g_dim_status d ON d.status = f.status
    """,
    "fato_inovacao: destino sem dimensão": """
        SELECT count(*) FROM g_fato_inovacao f ANTI JOIN g_dim_destino d ON d.destino = f.destino
    """,
    "fato_inovacao: autor sem dimensão": """
        SELECT count(*) FROM g_fato_inovacao f ANTI JOIN g_dim_usuario d ON d.usuario_id = f.autor_id
    """,
    "fato_inovacao: departamento sem dimensão": """
        SELECT count(*) FROM g_fato_inovacao f
        ANTI JOIN g_dim_departamento d ON d.departamento_id = f.departamento_id
    """,
    "fato_inovacao: data de criação fora do calendário": """
        SELECT count(*) FROM g_fato_inovacao f ANTI JOIN g_dim_data d ON d.data = f.data_criacao
    """,
    "fato_inovacao: implementada sem data de implementação": """
        SELECT count(*) FROM g_fato_inovacao WHERE status = 'implementada' AND data_implementada IS NULL
    """,
    "fato_inovacao: prazo negativo até a implementação": """
        SELECT count(*) FROM g_fato_inovacao WHERE dias_ate_implementada < 0
    """,
}

TABELAS_SILVER = ("departamento", "usuario", "inovacao", "inovacao_historico", "interacao", "parecer_ia")


def modelar(cfg: Config) -> dict[str, int]:
    """Grava a gold e roda a régua dela. Levanta ReguaReprovou se algo violar."""
    silver = cfg.lake / "silver"
    pasta = cfg.lake / "gold"
    pasta.mkdir(parents=True, exist_ok=True)
    conexao = duckdb.connect()
    contagem: dict[str, int] = {}
    try:
        for tabela in TABELAS_SILVER:
            conexao.execute(
                f"CREATE VIEW s_{tabela} AS SELECT * FROM read_parquet('{silver / (tabela + '.parquet')}')"
            )
        for tabela, consulta in MODELO.items():
            destino = pasta / f"{tabela}.parquet"
            conexao.execute(f"COPY ({consulta}) TO '{destino}' (FORMAT PARQUET)")
            conexao.execute(f"CREATE VIEW g_{tabela} AS SELECT * FROM read_parquet('{destino}')")
            linha = conexao.execute(f"SELECT count(*) FROM g_{tabela}").fetchone()
            contagem[tabela] = int(linha[0]) if linha else 0
        resultado: dict[str, int] = {}
        for regra, consulta in REGUA.items():
            linha = conexao.execute(consulta).fetchone()
            resultado[regra] = int(linha[0]) if linha else 0
    finally:
        conexao.close()

    (pasta / "_regua.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    reprovacoes = {regra: n for regra, n in resultado.items() if n != 0}
    if reprovacoes:
        raise ReguaReprovou("gold", reprovacoes)
    return contagem
