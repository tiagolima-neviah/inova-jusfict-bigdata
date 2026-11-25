"""Etapa 3 · silver: dado confiável, com régua de qualidade que reprova.

Problema que resolve: antes de modelar, garantir que o dado é íntegro. O
DuckDB lê os parquets da bronze com SQL, sem subir servidor: textos sem
espaço sobrando, datas no horário de Brasília, papel e departamento
resolvidos. Depois a régua roda: cada regra é uma consulta que conta
violações. Se alguma regra contar mais que zero, a etapa levanta
ReguaReprovou, o pipeline para com exit 1 e a gold não é tocada.

Decisão declarada: o dado sintético nasce limpo, então a aprovação integral é
o resultado esperado. Num cliente real, é esta régua que segura a carga.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from inova_bigdata.config import Config
from inova_bigdata.pipeline import TABELAS, ReguaReprovou

STATUS_VALIDOS = (
    "na_fila", "em_avaliacao", "com_diretor", "brainstorm", "em_escopo", "mvp", "em_implementacao",
    "implementada", "arquivo_morto_sugerido", "arquivo_morto_proposto", "arquivo_morto", "em_espera",
    "ja_existe",
)  # fmt: skip
DESTINOS_VALIDOS = ("app", "automacao", "relatorio", "processo", "outro")

_LOCAL = "AT TIME ZONE 'America/Sao_Paulo'"

# Uma consulta por tabela da silver. As views b_<tabela> são a bronze do dia.
TRANSFORMACOES: dict[str, str] = {
    "departamento": "SELECT id, trim(nome) AS nome FROM b_departamento",
    "usuario": f"""
        SELECT u.id, trim(u.nome) AS nome, u.login, trim(u.cargo) AS cargo,
               p.nome AS papel, p.nivel, u.ativo, u.demonstracao,
               CAST(u.criado_em {_LOCAL} AS TIMESTAMP) AS criado_em,
               min(ud.departamento_id) AS departamento_id,
               count(ud.departamento_id) AS qtd_departamentos
        FROM b_usuario u
        JOIN b_papel p ON p.id = u.papel_id
        LEFT JOIN b_usuario_departamento ud ON ud.usuario_id = u.id
        GROUP BY ALL
    """,
    "usuario_departamento": "SELECT usuario_id, departamento_id FROM b_usuario_departamento",
    "inovacao": f"""
        SELECT id, trim(titulo) AS titulo, trim(descricao) AS descricao, trim(objetivo) AS objetivo,
               trim(beneficios) AS beneficios, trim(desafios) AS desafios,
               trim(ferramentas_tecnicas) AS ferramentas_tecnicas,
               trim(indicador_sucesso) AS indicador_sucesso, prazo_desejado,
               custo_tipo, custo_valor, destino, status,
               CAST(brainstorm_em {_LOCAL} AS TIMESTAMP) AS brainstorm_em, brainstorm_local,
               autor_id, departamento_id, departamento_responsavel_id,
               CAST(criada_em {_LOCAL} AS TIMESTAMP) AS criada_em,
               CAST(atualizada_em {_LOCAL} AS TIMESTAMP) AS atualizada_em,
               origem
        FROM b_inovacao
    """,
    "inovacao_historico": f"""
        SELECT id, inovacao_id, status_de, status_para, usuario_id, trim(observacao) AS observacao,
               CAST(em {_LOCAL} AS TIMESTAMP) AS em,
               coalesce(status_de = status_para, false) AS marco,
               row_number() OVER (PARTITION BY inovacao_id ORDER BY em, id) AS ordem
        FROM b_inovacao_historico
    """,
    "interacao": f"""
        SELECT id, inovacao_id, autor_id, trim(texto) AS texto,
               CAST(em {_LOCAL} AS TIMESTAMP) AS em
        FROM b_interacao
    """,
    "parecer_ia": f"""
        SELECT id, inovacao_id, score_0_100, recomenda, trim(resumo) AS resumo, custo_estimado,
               ganho_estimado, retorno_estimado_meses, equipe_e_ferramentas,
               CAST(gerado_em {_LOCAL} AS TIMESTAMP) AS gerado_em, modelo
        FROM b_parecer_ia
    """,
}

_LISTA_STATUS = ", ".join(f"'{status}'" for status in STATUS_VALIDOS)
_LISTA_DESTINOS = ", ".join(f"'{destino}'" for destino in DESTINOS_VALIDOS)

# A régua: nome da regra -> consulta que devolve o NÚMERO DE VIOLAÇÕES.
REGUA: dict[str, str] = {
    "inovacao: id repetido": "SELECT count(*) - count(DISTINCT id) FROM s_inovacao",
    "usuario: id repetido": "SELECT count(*) - count(DISTINCT id) FROM s_usuario",
    "historico: id repetido": "SELECT count(*) - count(DISTINCT id) FROM s_inovacao_historico",
    "inovacao: autor inexistente": """
        SELECT count(*) FROM s_inovacao i ANTI JOIN s_usuario u ON u.id = i.autor_id
    """,
    "inovacao: departamento inexistente": """
        SELECT count(*) FROM s_inovacao i ANTI JOIN s_departamento d ON d.id = i.departamento_id
    """,
    "historico: inovação inexistente": """
        SELECT count(*) FROM s_inovacao_historico h ANTI JOIN s_inovacao i ON i.id = h.inovacao_id
    """,
    "historico: usuário inexistente": """
        SELECT count(*) FROM s_inovacao_historico h ANTI JOIN s_usuario u ON u.id = h.usuario_id
    """,
    "interacao: inovação inexistente": """
        SELECT count(*) FROM s_interacao t ANTI JOIN s_inovacao i ON i.id = t.inovacao_id
    """,
    "inovacao: status fora do domínio": f"""
        SELECT count(*) FROM s_inovacao WHERE status NOT IN ({_LISTA_STATUS})
    """,
    "inovacao: destino fora do domínio": f"""
        SELECT count(*) FROM s_inovacao WHERE destino IS NOT NULL AND destino NOT IN ({_LISTA_DESTINOS})
    """,
    "inovacao: título vazio": "SELECT count(*) FROM s_inovacao WHERE titulo IS NULL OR titulo = ''",
    "inovacao: custo incoerente com o tipo": """
        SELECT count(*) FROM s_inovacao WHERE (custo_tipo = 'sem_custo') <> (custo_valor IS NULL)
    """,
    "inovacao: atualizada antes de criada": """
        SELECT count(*) FROM s_inovacao WHERE atualizada_em < criada_em
    """,
    "inovacao: sem histórico": """
        SELECT count(*) FROM s_inovacao i ANTI JOIN s_inovacao_historico h ON h.inovacao_id = i.id
    """,
    "historico: primeiro evento não é a criação": """
        SELECT count(*) FROM s_inovacao_historico WHERE ordem = 1 AND status_de IS NOT NULL
    """,
    "historico: evento sem encadear com o anterior": """
        SELECT count(*) FROM (
            SELECT status_de, lag(status_para) OVER (PARTITION BY inovacao_id ORDER BY ordem) AS anterior
            FROM s_inovacao_historico
        ) WHERE anterior IS NOT NULL AND status_de IS DISTINCT FROM anterior
    """,
    "inovacao: status diferente do último evento": """
        SELECT count(*) FROM s_inovacao i
        JOIN (
            SELECT inovacao_id, arg_max(status_para, ordem) AS ultimo FROM s_inovacao_historico GROUP BY 1
        ) h ON h.inovacao_id = i.id
        WHERE i.status <> h.ultimo
    """,
    "historico: evento no futuro": """
        SELECT count(*) FROM s_inovacao_historico WHERE em > now()::TIMESTAMP + INTERVAL 1 DAY
    """,
    "parecer: score fora de 0 a 100": """
        SELECT count(*) FROM s_parecer_ia WHERE score_0_100 NOT BETWEEN 0 AND 100
    """,
}


def _particao_mais_recente(cfg: Config, tabela: str) -> Path:
    pastas = sorted((cfg.lake / "bronze" / tabela).glob("extracao=*"))
    if not pastas:
        raise FileNotFoundError(f"bronze sem extração para {tabela}: rode a etapa bronze antes")
    return pastas[-1] / f"{tabela}.parquet"


def transformar(cfg: Config) -> dict[str, int]:
    """Grava a silver e roda a régua. Levanta ReguaReprovou se algo violar."""
    pasta = cfg.lake / "silver"
    pasta.mkdir(parents=True, exist_ok=True)
    conexao = duckdb.connect()
    contagem: dict[str, int] = {}
    perdas: dict[str, int] = {}
    try:
        for tabela in TABELAS:
            origem = _particao_mais_recente(cfg, tabela)
            conexao.execute(f"CREATE VIEW b_{tabela} AS SELECT * FROM read_parquet('{origem}')")
        for tabela, consulta in TRANSFORMACOES.items():
            destino = pasta / f"{tabela}.parquet"
            conexao.execute(f"COPY ({consulta}) TO '{destino}' (FORMAT PARQUET)")
            conexao.execute(f"CREATE VIEW s_{tabela} AS SELECT * FROM read_parquet('{destino}')")
            na_silver = conexao.execute(f"SELECT count(*) FROM s_{tabela}").fetchone()
            na_bronze = conexao.execute(f"SELECT count(*) FROM b_{tabela}").fetchone()
            contagem[tabela] = int(na_silver[0]) if na_silver else 0
            if na_bronze and contagem[tabela] != int(na_bronze[0]):
                perdas[f"{tabela}: linhas da bronze ({na_bronze[0]}) e da silver diferem"] = contagem[tabela]

        resultado: dict[str, int] = {}
        for regra, consulta in REGUA.items():
            linha = conexao.execute(consulta).fetchone()
            resultado[regra] = int(linha[0]) if linha else 0
        resultado.update(perdas)
    finally:
        conexao.close()

    (pasta / "_regua.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    reprovacoes = {regra: n for regra, n in resultado.items() if n != 0}
    if reprovacoes:
        raise ReguaReprovou("silver", reprovacoes)
    return contagem
