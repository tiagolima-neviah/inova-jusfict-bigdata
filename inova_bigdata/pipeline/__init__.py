"""Pipeline de dados da JusFict Inova.

produção (Neon, schema inova) -> staging (Postgres local) -> bronze (parquet)
-> silver (DuckDB, com régua de qualidade) -> gold (star schema) -> warehouse
(Neon, schema dw). Cada etapa é uma função chamada por linha de comando: sem
orquestrador na v1 (ADR 0001), pronta para virar asset se o projeto crescer.
"""

# O que sai da produção, tabela a tabela. A lista de colunas é explícita de
# propósito: `usuario.senha_hash` NÃO sai da produção. Hash de senha não tem
# uso analítico e não deve existir fora do sistema que autentica.
TABELAS: dict[str, str] = {
    "departamento": "id, nome",
    "papel": "id, nome, nivel",
    "usuario": "id, nome, login, cargo, papel_id, ativo, demonstracao, criado_em",
    "usuario_departamento": "usuario_id, departamento_id",
    "inovacao": (
        "id, titulo, descricao, objetivo, beneficios, desafios, ferramentas_tecnicas, "
        "indicador_sucesso, prazo_desejado, custo_tipo, custo_valor, destino, status, "
        "brainstorm_em, brainstorm_local, autor_id, departamento_id, "
        "departamento_responsavel_id, criada_em, atualizada_em, origem"
    ),
    "inovacao_historico": "id, inovacao_id, status_de, status_para, usuario_id, observacao, em",
    "interacao": "id, inovacao_id, autor_id, texto, em",
    "parecer_ia": (
        "id, inovacao_id, score_0_100, recomenda, resumo, custo_estimado, ganho_estimado, "
        "retorno_estimado_meses, equipe_e_ferramentas, gerado_em, modelo"
    ),
}


class ReguaReprovou(Exception):  # noqa: N818
    """A régua de qualidade encontrou dado que não pode seguir adiante."""

    def __init__(self, camada: str, reprovacoes: dict[str, int]) -> None:
        self.camada = camada
        self.reprovacoes = reprovacoes
        detalhe = ", ".join(f"{regra}: {n}" for regra, n in reprovacoes.items())
        super().__init__(f"régua da {camada} reprovou: {detalhe}")
