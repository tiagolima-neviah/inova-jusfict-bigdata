"""Testes do gerador sintético: tudo sem banco, porque a simulação é pura."""

from dataclasses import replace

from inova_bigdata.gerador import regua, simulacao


def test_mesma_semente_mesma_base() -> None:
    primeira = simulacao.gerar()
    segunda = simulacao.gerar()
    assert [(i.titulo, i.autor, i.criada_em, i.status) for i in primeira.inovacoes] == [
        (i.titulo, i.autor, i.criada_em, i.status) for i in segunda.inovacoes
    ]
    assert [p.login for p in primeira.pessoas] == [p.login for p in segunda.pessoas]


def test_semente_diferente_base_diferente() -> None:
    assert [i.titulo for i in simulacao.gerar(1).inovacoes] != [
        i.titulo for i in simulacao.gerar(2).inovacoes
    ]


def test_base_padrao_passa_na_regua() -> None:
    assert regua.conferir(simulacao.gerar()) == []


def test_volume_e_janela_das_premissas() -> None:
    base = simulacao.gerar()
    assert len(base.pessoas) == 170 + 5 + 2  # 170 colaboradores, 5 supervisores, diretor e presidente
    assert 500 <= len(base.inovacoes) <= 700
    datas = [inovacao.criada_em.date() for inovacao in base.inovacoes]
    assert min(datas) >= simulacao.DATA_INICIO
    assert max(datas) <= simulacao.DATA_CORTE
    assert {data.year for data in datas} == {2024, 2025, 2026}


def test_dezembro_e_o_vale_da_sazonalidade() -> None:
    base = simulacao.gerar()
    por_mes = {mes: 0 for mes in range(1, 13)}
    for inovacao in base.inovacoes:
        if inovacao.criada_em.year in (2024, 2025):  # só os anos cheios
            por_mes[inovacao.criada_em.month] += 1
    assert por_mes[12] == min(por_mes.values())


def test_quem_trata_esta_sempre_acima_do_autor() -> None:
    base = simulacao.gerar()
    nivel = {pessoa.login: pessoa.nivel for pessoa in base.pessoas}
    for inovacao in base.inovacoes:
        for evento in inovacao.eventos[1:]:
            assert nivel[evento.ator] > nivel[inovacao.autor]


def test_so_a_presidencia_consuma_arquivamento() -> None:
    base = simulacao.gerar()
    arquivadas = [i for i in base.inovacoes if i.status == "arquivo_morto"]
    assert arquivadas, "a base deveria ter inovações arquivadas"
    for inovacao in arquivadas:
        assert inovacao.eventos[-1].ator == simulacao.PRESIDENTE


def test_regua_reprova_base_adulterada() -> None:
    base = simulacao.gerar()
    vitima = next(i for i in base.inovacoes if len(i.eventos) > 1)
    # O próprio autor "avaliando" a sua ideia: a régua tem de pegar.
    vitima.eventos[1] = replace(vitima.eventos[1], ator=vitima.autor)
    erros = regua.conferir(base)
    assert any("mesmo nível ou acima" in erro for erro in erros)


def test_regua_reprova_evento_depois_do_corte() -> None:
    base = simulacao.gerar()
    vitima = next(i for i in base.inovacoes if len(i.eventos) > 1)
    futuro = vitima.eventos[-1].quando.replace(year=2027)
    vitima.eventos[-1] = replace(vitima.eventos[-1], quando=futuro)
    assert any("depois do corte" in erro for erro in regua.conferir(base))
