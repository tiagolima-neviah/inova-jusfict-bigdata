"""Régua do sintético: confere a base gerada antes de ela tocar o banco.

Defeito de base sintética se regenera, não se contorna: se alguma regra
falhar, o gerador para (exit 1) e nada é gravado. As regras são as da
plataforma, então a régua também serve de especificação executável delas.
"""

from __future__ import annotations

from inova_bigdata.gerador.simulacao import DATA_CORTE, DATA_INICIO, Base

STATUS_ARQUIVO = ("arquivo_morto", "arquivo_morto_proposto", "arquivo_morto_sugerido")

# Toda transição que a plataforma permite (de, para). Marco fino é de == para.
TRANSICOES_VALIDAS = {
    ("na_fila", "em_avaliacao"),
    ("em_avaliacao", "com_diretor"),
    ("em_avaliacao", "arquivo_morto_sugerido"),
    ("arquivo_morto_sugerido", "arquivo_morto_proposto"),
    ("arquivo_morto_sugerido", "brainstorm"),
    ("arquivo_morto_sugerido", "arquivo_morto"),
    ("arquivo_morto_proposto", "arquivo_morto"),
    ("arquivo_morto_proposto", "brainstorm"),
    ("com_diretor", "brainstorm"),
    ("com_diretor", "em_escopo"),
    ("com_diretor", "arquivo_morto_proposto"),
    ("com_diretor", "arquivo_morto"),
    ("brainstorm", "em_escopo"),
    ("brainstorm", "em_espera"),
    ("brainstorm", "ja_existe"),
    ("em_espera", "com_diretor"),
    ("em_escopo", "mvp"),
    ("em_escopo", "em_implementacao"),
    ("mvp", "em_implementacao"),
    ("em_implementacao", "implementada"),
}


def conferir(base: Base) -> list[str]:
    """Devolve a lista de reprovações; lista vazia significa base aprovada."""
    erros: list[str] = []
    nivel = {pessoa.login: pessoa.nivel for pessoa in base.pessoas}
    departamentos = {dep for pessoa in base.pessoas for dep in pessoa.departamentos}

    logins = [pessoa.login for pessoa in base.pessoas]
    if len(set(logins)) != len(logins):
        erros.append("pessoas: login repetido")

    for indice, inovacao in enumerate(base.inovacoes):
        onde = f"inovação {indice} ({inovacao.titulo!r})"
        eventos = inovacao.eventos
        if not eventos:
            erros.append(f"{onde}: sem histórico")
            continue
        if eventos[0].status_de is not None or eventos[0].ator != inovacao.autor:
            erros.append(f"{onde}: o primeiro evento não é a criação pelo autor")
        if eventos[0].quando != inovacao.criada_em:
            erros.append(f"{onde}: a criação não bate com criada_em")
        if not DATA_INICIO <= inovacao.criada_em.date() <= DATA_CORTE:
            erros.append(f"{onde}: criada fora da janela")
        if inovacao.departamento not in departamentos:
            erros.append(f"{onde}: departamento desconhecido")

        nivel_autor = nivel[inovacao.autor]
        esperado_ao_nascer = "na_fila" if nivel_autor == 1 else "com_diretor"
        if eventos[0].status_para != esperado_ao_nascer:
            erros.append(f"{onde}: nasceu em {eventos[0].status_para}, deveria ser {esperado_ao_nascer}")

        for anterior, evento in zip(eventos, eventos[1:], strict=False):
            if evento.status_de != anterior.status_para:
                erros.append(f"{onde}: histórico não encadeia em {evento.status_para}")
            if evento.quando <= anterior.quando:
                erros.append(f"{onde}: evento fora de ordem em {evento.status_para}")
            if evento.quando.date() > DATA_CORTE:
                erros.append(f"{onde}: evento depois do corte")
            marco = evento.status_de == evento.status_para
            if not marco and (evento.status_de, evento.status_para) not in TRANSICOES_VALIDAS:
                erros.append(f"{onde}: transição inválida {evento.status_de} -> {evento.status_para}")
            # Regra central: quem trata está sempre acima do autor.
            if nivel[evento.ator] <= nivel_autor:
                erros.append(f"{onde}: {evento.ator} tratou inovação de alguém do mesmo nível ou acima")
            # Nenhum arquivamento se consuma sem a presidência.
            if evento.status_para == "arquivo_morto" and nivel[evento.ator] != 4:
                erros.append(f"{onde}: arquivada por quem não é a presidência")
            abre_cadeia = evento.status_para in STATUS_ARQUIVO and evento.status_de not in STATUS_ARQUIVO
            if abre_cadeia and not (evento.observacao or "").strip():
                erros.append(f"{onde}: arquivamento sem justificativa")

        if inovacao.status == "brainstorm" and inovacao.brainstorm_em is None:
            erros.append(f"{onde}: em brainstorm sem reunião agendada")
        if inovacao.departamento_responsavel is None and inovacao.status in (
            "em_escopo",
            "mvp",
            "em_implementacao",
            "implementada",
        ):
            erros.append(f"{onde}: passou do escopo sem departamento responsável")
        if (inovacao.custo_tipo == "sem_custo") != (inovacao.custo_valor is None):
            erros.append(f"{onde}: custo incoerente com o tipo")

    total = len(base.inovacoes)
    if not 500 <= total <= 700:
        erros.append(f"volume: {total} inovações, fora da faixa de 500 a 700")
    if total:
        implementadas = sum(1 for inovacao in base.inovacoes if inovacao.status == "implementada")
        if not 0.15 <= implementadas / total <= 0.50:
            erros.append(f"volume: {implementadas} implementadas de {total}, fora de 15% a 50%")
        com_inovacao = {inovacao.departamento for inovacao in base.inovacoes}
        if com_inovacao != departamentos:
            erros.append("volume: há departamento sem nenhuma inovação")
    return erros
