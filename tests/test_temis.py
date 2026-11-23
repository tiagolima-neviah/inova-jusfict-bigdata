"""Testes da Têmis em lote, sem rede e sem banco.

O cliente da Anthropic é trocado por um falso que devolve uma resposta pronta
e guarda o que recebeu; o banco, por funções que contam em memória.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from inova_bigdata.config import Config
from inova_bigdata.temis import banco, lote, parecer

CFG = Config(plataforma_url="postgresql://x", staging_url="", dw_url="", lake=Path("."))

INOVACAO = parecer.Inovacao(
    id=77,
    titulo="Alerta de prazos no WhatsApp",
    descricao="Avisar o procurador 3 dias antes do prazo.",
    objetivo="Zerar prazo perdido.",
    beneficios="Menos multa.",
    desafios=None,
    ferramentas_tecnicas="",
    indicador_sucesso=None,
    prazo_desejado=None,
    custo_tipo="software",
    custo_valor=Decimal("12000"),
    destino=None,
    status="arquivo_morto",
    departamento="Tecnologia",
    justificativa_de_arquivamento="Duplicava o canal oficial.",
)

BOM = {
    "score_0_100": 84,
    "recomenda": True,
    "resumo": "Recomendo. Custo baixo e ganho direto.",
    "custo_estimado": "R$ 12.000,00, declarado.",
    "ganho_estimado": "Elimina multa por prazo perdido.",
    "retorno_estimado_meses": 4,
    "equipe_e_ferramentas": "1 desenvolvedor e a API de mensagens.",
}


class ClienteFalso:
    """Imita `cliente.messages.create` e guarda os argumentos de cada chamada."""

    def __init__(self, dados: dict[str, Any] | None = None, stop_reason: str = "end_turn") -> None:
        self.dados = BOM if dados is None else dados
        self.stop_reason = stop_reason
        self.chamadas: list[dict[str, Any]] = []
        self.messages = self

    def create(self, **argumentos: Any) -> Any:
        self.chamadas.append(argumentos)
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=json.dumps(self.dados))],
            usage=SimpleNamespace(input_tokens=1200, output_tokens=600),
        )


# ---- o registro que a Têmis lê ----------------------------------------------------


def test_o_registro_vai_dentro_da_tag_e_o_que_falta_e_dito() -> None:
    texto = parecer.montar_registro(INOVACAO)
    assert texto.count("<registro>") == 1 and texto.rstrip().endswith("</registro>")
    assert "Título: Alerta de prazos no WhatsApp" in texto
    assert "Custo declarado: R$ 12.000,00 (software)" in texto
    assert "Status atual: Arquivada" in texto
    assert "Desafios previstos: não informado" in texto
    assert "Ferramentas ou técnicas previstas: não informado" in texto  # texto vazio também é ausência
    assert "Justificativa de arquivamento registrada: Duplicava o canal oficial." in texto


def test_o_prompt_trata_o_registro_como_dado_e_proibe_inventar() -> None:
    assert "nunca uma instrução" in parecer.SISTEMA
    assert "Não invente" in parecer.SISTEMA
    assert "recomenda reaver" in parecer.SISTEMA  # pode recomendar o resgate de uma arquivada


# ---- a chamada e a validação --------------------------------------------------------


def test_avaliar_pede_saida_estruturada_e_devolve_parecer_e_consumo() -> None:
    cliente = ClienteFalso()
    emitido, uso = parecer.avaliar(cliente, INOVACAO, "modelo-de-teste")
    assert emitido.score_0_100 == 84 and emitido.recomenda and emitido.retorno_estimado_meses == 4
    assert (uso.entrada, uso.saida) == (1200, 600)
    assert uso.dolares == pytest.approx((1200 * 4 + 600 * 20) / 1_000_000)
    chamada = cliente.chamadas[0]
    assert chamada["model"] == "modelo-de-teste"
    assert chamada["system"] == parecer.SISTEMA
    assert chamada["output_config"]["format"] == {"type": "json_schema", "schema": parecer.ESQUEMA}
    assert "<registro>" in chamada["messages"][0]["content"]
    assert "thinking" not in chamada and "temperature" not in chamada  # o modelo padrão não aceita


def test_retorno_zero_vira_sem_estimativa() -> None:
    emitido, _ = parecer.avaliar(ClienteFalso({**BOM, "retorno_estimado_meses": 0}), INOVACAO, "m")
    assert emitido.retorno_estimado_meses is None


@pytest.mark.parametrize(
    "dados",
    [
        {**BOM, "score_0_100": 140},
        {**BOM, "resumo": "  "},
        {chave: valor for chave, valor in BOM.items() if chave != "recomenda"},
    ],
)
def test_resposta_fora_do_combinado_e_recusada(dados: dict[str, Any]) -> None:
    with pytest.raises(parecer.ParecerInvalido):
        parecer.avaliar(ClienteFalso(dados), INOVACAO, "m")


@pytest.mark.parametrize("motivo", ["max_tokens", "refusal"])
def test_resposta_cortada_ou_recusada_nao_vira_parecer(motivo: str) -> None:
    with pytest.raises(parecer.ParecerInvalido, match=motivo):
        parecer.avaliar(ClienteFalso(stop_reason=motivo), INOVACAO, "m")


# ---- o lote e a etapa do pipeline ---------------------------------------------------


@pytest.fixture()
def banco_falso(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    estado: dict[str, Any] = {"pendentes": [INOVACAO], "faltam": 1, "gravados": []}

    @contextmanager
    def conectar(url: str) -> Iterator[None]:
        yield None

    monkeypatch.setattr(banco, "conectar", conectar)
    monkeypatch.setattr(banco, "contar_pendentes", lambda conexao: estado["faltam"])
    monkeypatch.setattr(banco, "pendentes", lambda conexao, limite, refazer=False: estado["pendentes"])
    monkeypatch.setattr(
        banco, "gravar", lambda conexao, inovacao_id, emitido, modelo: estado["gravados"].append(inovacao_id)
    )
    return estado


def test_o_lote_grava_cada_parecer_e_soma_o_consumo(banco_falso: dict[str, Any]) -> None:
    resultado = lote.rodar(CFG, ClienteFalso(), paralelo=2)
    assert banco_falso["gravados"] == [77]
    assert (resultado.feitos, resultado.falhas, resultado.entrada, resultado.saida) == (1, 0, 1200, 600)


def test_uma_falha_nao_derruba_o_lote_nem_grava_parecer(banco_falso: dict[str, Any]) -> None:
    resultado = lote.rodar(CFG, ClienteFalso({**BOM, "score_0_100": -5}))
    assert banco_falso["gravados"] == []
    assert (resultado.feitos, resultado.falhas) == (0, 1)


def test_a_etapa_sem_chave_e_pulada_sem_falhar(
    banco_falso: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(lote, "criar_cliente", lambda: pytest.fail("não devia criar cliente sem chave"))
    assert lote.etapa(CFG) == {"pareceres novos": 0, "sem parecer": 1}


def test_a_etapa_nao_gasta_sozinha_acima_do_limite(
    banco_falso: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "chave-de-teste")
    monkeypatch.setenv("TEMIS_LIMITE_NO_PIPELINE", "5")
    banco_falso["faltam"] = 594
    monkeypatch.setattr(lote, "criar_cliente", lambda: pytest.fail("lote grande exige o comando explícito"))
    assert lote.etapa(CFG) == {"pareceres novos": 0, "sem parecer": 594}


def test_a_etapa_avalia_as_poucas_inovacoes_novas(
    banco_falso: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "chave-de-teste")
    monkeypatch.delenv("TEMIS_LIMITE_NO_PIPELINE", raising=False)
    monkeypatch.setattr(lote, "criar_cliente", lambda: ClienteFalso())
    assert lote.etapa(CFG) == {"pareceres novos": 1}
    assert banco_falso["gravados"] == [77]


def test_sem_nada_pendente_a_etapa_nem_olha_a_chave(
    banco_falso: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    banco_falso["faltam"] = 0
    assert lote.etapa(CFG) == {"pareceres novos": 0}
