"""Grava a base sintética na produção da plataforma (schema inova).

Tudo numa transação só: ou a base inteira entra, ou nada muda. O que foi
cadastrado à mão na plataforma (origem = 'plataforma') e as 12 pessoas de
demonstração nunca são tocados; só o que é sintético é apagado e recriado.
"""

from __future__ import annotations

import secrets
from typing import Any

import psycopg

from inova_bigdata.config import FUSO
from inova_bigdata.gerador.simulacao import Base

# Os colaboradores sintéticos não fazem login: recebem um texto aleatório no
# lugar do hash, que nenhuma senha consegue igualar.
_SEM_LOGIN = "sem-login-" + secrets.token_hex(16)


def _limpar_sintetico(cursor: psycopg.Cursor[Any]) -> None:
    cursor.execute("SELECT id FROM inovacao WHERE origem = 'sintetico'")
    ids = [linha[0] for linha in cursor.fetchall()]
    if ids:
        cursor.execute("DELETE FROM parecer_ia WHERE inovacao_id = ANY(%s)", (ids,))
        cursor.execute("DELETE FROM interacao WHERE inovacao_id = ANY(%s)", (ids,))
        cursor.execute("DELETE FROM inovacao_historico WHERE inovacao_id = ANY(%s)", (ids,))
        cursor.execute("DELETE FROM inovacao WHERE id = ANY(%s)", (ids,))
    cursor.execute(
        "DELETE FROM usuario_departamento WHERE usuario_id IN (SELECT id FROM usuario WHERE NOT demonstracao)"
    )
    cursor.execute("DELETE FROM usuario WHERE NOT demonstracao")


def gravar(url: str, base: Base) -> dict[str, int]:
    """Recria o sintético e devolve quantas linhas entraram em cada tabela."""
    with psycopg.connect(url, options=FUSO) as conexao, conexao.cursor() as cursor:
        cursor.execute("SET search_path TO inova")
        _limpar_sintetico(cursor)

        cursor.execute("SELECT nome, id FROM departamento")
        departamento_id: dict[str, int] = dict(cursor.fetchall())
        cursor.execute("SELECT id FROM papel WHERE nivel = 1")
        linha = cursor.fetchone()
        if linha is None:
            raise RuntimeError("papel de colaborador não encontrado: o banco foi semeado?")
        papel_colaborador = linha[0]

        sinteticos = [pessoa for pessoa in base.pessoas if not pessoa.demonstracao]
        cursor.executemany(
            """
            INSERT INTO usuario (nome, login, senha_hash, cargo, papel_id, demonstracao)
            VALUES (%s, %s, %s, %s, %s, false)
            """,
            [(p.nome, p.login, _SEM_LOGIN, p.cargo, papel_colaborador) for p in sinteticos],
        )
        cursor.execute("SELECT login, id FROM usuario")
        usuario_id: dict[str, int] = dict(cursor.fetchall())
        faltando = [p.login for p in base.pessoas if p.login not in usuario_id]
        if faltando:
            raise RuntimeError(f"pessoas de demonstração ausentes no banco: {faltando}")
        cursor.executemany(
            "INSERT INTO usuario_departamento (usuario_id, departamento_id) VALUES (%s, %s)",
            [(usuario_id[p.login], departamento_id[dep]) for p in sinteticos for dep in p.departamentos],
        )

        historico: list[tuple[Any, ...]] = []
        mensagens: list[tuple[Any, ...]] = []
        for inovacao in base.inovacoes:
            responsavel = inovacao.departamento_responsavel
            cursor.execute(
                """
                INSERT INTO inovacao
                    (titulo, descricao, objetivo, beneficios, desafios, ferramentas_tecnicas,
                     indicador_sucesso, prazo_desejado, custo_tipo, custo_valor, destino, status,
                     brainstorm_em, brainstorm_local, autor_id, departamento_id,
                     departamento_responsavel_id, criada_em, atualizada_em, origem)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'sintetico')
                RETURNING id
                """,
                (
                    inovacao.titulo,
                    inovacao.descricao,
                    inovacao.objetivo,
                    inovacao.beneficios,
                    inovacao.desafios,
                    inovacao.ferramentas,
                    inovacao.indicador,
                    inovacao.prazo_desejado,
                    inovacao.custo_tipo,
                    inovacao.custo_valor,
                    inovacao.destino,
                    inovacao.status,
                    inovacao.brainstorm_em,
                    inovacao.brainstorm_local,
                    usuario_id[inovacao.autor],
                    departamento_id[inovacao.departamento],
                    departamento_id[responsavel] if responsavel else None,
                    inovacao.criada_em,
                    inovacao.atualizada_em,
                ),
            )
            criada = cursor.fetchone()
            if criada is None:
                raise RuntimeError("INSERT sem retorno de id")
            inovacao_id = criada[0]
            historico.extend(
                (inovacao_id, e.status_de, e.status_para, usuario_id[e.ator], e.observacao, e.quando)
                for e in inovacao.eventos
            )
            mensagens.extend(
                (inovacao_id, usuario_id[m.autor], m.texto, m.quando) for m in inovacao.mensagens
            )

        cursor.executemany(
            """
            INSERT INTO inovacao_historico (inovacao_id, status_de, status_para, usuario_id, observacao, em)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            historico,
        )
        cursor.executemany(
            "INSERT INTO interacao (inovacao_id, autor_id, texto, em) VALUES (%s, %s, %s, %s)",
            mensagens,
        )
    return {
        "usuario": len(sinteticos),
        "inovacao": len(base.inovacoes),
        "inovacao_historico": len(historico),
        "interacao": len(mensagens),
    }
