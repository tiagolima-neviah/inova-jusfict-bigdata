"""O laço dos pareceres: em paralelo, retomável e com o custo à vista.

- Em paralelo: as chamadas à API rodam em algumas linhas de execução; a
  gravação é feita uma a uma, na ordem em que as respostas chegam.
- Retomável: cada parecer é gravado na hora. Se o lote cair, rodar de novo
  avalia só o que ficou faltando.
- Custo à vista: o consumo de tokens é somado e vira uma estimativa em dólar.
- No pipeline, a etapa só avalia sozinha um número pequeno de inovações novas
  (`LIMITE_NO_PIPELINE`); um lote grande exige o comando explícito, para
  ninguém gastar sem saber.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from inova_bigdata import config, temis
from inova_bigdata.temis import banco, parecer

# Quantas inovações sem parecer a etapa do pipeline avalia sem perguntar.
LIMITE_NO_PIPELINE = 30


@dataclass
class Resultado:
    feitos: int = 0
    falhas: int = 0
    entrada: int = 0
    saida: int = 0

    @property
    def dolares(self) -> float:
        return parecer.Uso(self.entrada, self.saida).dolares


def criar_cliente() -> parecer.Cliente:
    import anthropic  # importado aqui: o resto do pipeline roda sem a biblioteca carregada

    # A chave vem de ANTHROPIC_API_KEY. O SDK já tenta de novo, com espera
    # crescente, em limite de taxa (429) e erro do servidor (5xx).
    return anthropic.Anthropic(max_retries=6)


def rodar(
    cfg: config.Config,
    cliente: parecer.Cliente,
    *,
    limite: int | None = None,
    paralelo: int = 4,
    refazer: bool = False,
    ao_progredir: Callable[[int, int, parecer.Inovacao, parecer.Parecer | None, str], None] | None = None,
) -> Resultado:
    """Avalia as inovações pendentes e grava cada parecer assim que ele chega."""
    modelo = temis.modelo()
    resultado = Resultado()
    with banco.conectar(cfg.plataforma_url) as conexao:
        fila = banco.pendentes(conexao, limite, refazer)
        with ThreadPoolExecutor(max_workers=max(1, paralelo)) as executor:
            futuros = {
                executor.submit(parecer.avaliar, cliente, inovacao, modelo): inovacao for inovacao in fila
            }
            for numero, futuro in enumerate(as_completed(futuros), start=1):
                inovacao = futuros[futuro]
                try:
                    emitido, uso = futuro.result()
                except Exception as erro:  # noqa: BLE001
                    # Uma falha não derruba o lote: a inovação fica sem parecer e entra na próxima rodada.
                    resultado.falhas += 1
                    if ao_progredir:
                        ao_progredir(numero, len(fila), inovacao, None, f"{type(erro).__name__}: {erro}")
                    continue
                banco.gravar(conexao, inovacao.id, emitido, modelo)
                resultado.feitos += 1
                resultado.entrada += uso.entrada
                resultado.saida += uso.saida
                if ao_progredir:
                    ao_progredir(numero, len(fila), inovacao, emitido, "")
    return resultado


def etapa(cfg: config.Config) -> dict[str, int]:
    """A etapa `temis` do pipeline: parecer para as inovações novas, antes da extração."""
    limite = int(os.environ.get("TEMIS_LIMITE_NO_PIPELINE") or LIMITE_NO_PIPELINE)
    with banco.conectar(cfg.plataforma_url) as conexao:
        faltam = banco.contar_pendentes(conexao)
    if faltam == 0:
        return {"pareceres novos": 0}
    if not temis.tem_chave():
        print(
            "    sem ANTHROPIC_API_KEY no .env: etapa pulada, o pipeline segue sem pareceres novos",
            file=sys.stderr,
        )
        return {"pareceres novos": 0, "sem parecer": faltam}
    if faltam > limite:
        print(
            f"    {faltam} inovações sem parecer, acima do limite automático ({limite}). "
            "Rode o lote, que mostra o custo: uv run python -m inova_bigdata.temis",
            file=sys.stderr,
        )
        return {"pareceres novos": 0, "sem parecer": faltam}
    resultado = rodar(cfg, criar_cliente())
    saida = {"pareceres novos": resultado.feitos}
    if resultado.falhas:
        saida["falhas"] = resultado.falhas
    return saida
