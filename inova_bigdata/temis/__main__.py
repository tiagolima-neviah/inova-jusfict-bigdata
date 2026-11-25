"""O comando do lote de pareceres da Têmis.

    uv run python -m inova_bigdata.temis                 # avalia tudo que está sem parecer
    uv run python -m inova_bigdata.temis --estimar       # só conta e estima o custo, sem chamar a API
    uv run python -m inova_bigdata.temis --limite 10     # avalia as 10 mais novas sem parecer
    uv run python -m inova_bigdata.temis --refazer --limite 5   # emite parecer novo para as 5 mais novas

Pode ser interrompido (Ctrl+C) e retomado: o que já foi gravado não é refeito.
Sai com 0 se tudo que foi pedido ganhou parecer e 1 se houve falha.
"""

from __future__ import annotations

import argparse
import sys
import time

from inova_bigdata import config, temis
from inova_bigdata.temis import banco, lote, parecer

# Ordem de grandeza por parecer (registro curto, esforço baixo); serve só para o --estimar.
# O número de verdade é o que o lote imprime no fim, somado do consumo que a API devolve.
TOKENS_DE_ENTRADA_POR_PARECER = 1300
TOKENS_DE_SAIDA_POR_PARECER = 700


def _progresso(
    numero: int, total: int, inovacao: parecer.Inovacao, emitido: parecer.Parecer | None, erro: str
) -> None:
    if emitido is None:
        print(f"  [{numero}/{total}] #{inovacao.id} FALHOU: {erro}", file=sys.stderr)
        return
    veredito = "recomenda" if emitido.recomenda else "não recomenda"
    print(
        f"  [{numero}/{total}] #{inovacao.id} {emitido.score_0_100:>3}/100 {veredito} · "
        f"{inovacao.titulo[:60]}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Pareceres da Têmis em lote (grava em inova.parecer_ia).")
    parser.add_argument("--limite", type=int, default=None, help="no máximo N inovações (as mais novas)")
    parser.add_argument("--paralelo", type=int, default=4, help="chamadas simultâneas à API (padrão 4)")
    parser.add_argument("--refazer", action="store_true", help="emite parecer novo também para quem já tem")
    parser.add_argument("--estimar", action="store_true", help="só conta e estima o custo; não chama a API")
    args = parser.parse_args()

    cfg = config.carregar()
    if not cfg.plataforma_url:
        print("PLATAFORMA_URL ausente: copie .env.example para .env e preencha.", file=sys.stderr)
        return 1

    with banco.conectar(cfg.plataforma_url) as conexao:
        quantas = len(banco.pendentes(conexao, args.limite, args.refazer))
    estimativa = parecer.Uso(
        quantas * TOKENS_DE_ENTRADA_POR_PARECER, quantas * TOKENS_DE_SAIDA_POR_PARECER
    ).dolares
    print(
        f"Têmis · modelo {temis.modelo()} · {quantas} inovações a avaliar · "
        f"estimativa de US$ {estimativa:.2f}"
    )
    if args.estimar or quantas == 0:
        return 0
    if not temis.tem_chave():
        print("ANTHROPIC_API_KEY ausente no .env: sem chave a Têmis não avalia.", file=sys.stderr)
        return 1

    inicio = time.perf_counter()
    try:
        resultado = lote.rodar(
            cfg,
            lote.criar_cliente(),
            limite=args.limite,
            paralelo=args.paralelo,
            refazer=args.refazer,
            ao_progredir=_progresso,
        )
    except KeyboardInterrupt:
        print("\ninterrompido: o que já foi gravado fica; rode de novo para continuar.", file=sys.stderr)
        return 1
    duracao = time.perf_counter() - inicio
    print(
        f"{resultado.feitos} pareceres gravados, {resultado.falhas} falhas, em {duracao:.0f}s · "
        f"{resultado.entrada} tokens de entrada, {resultado.saida} de saída · "
        f"cerca de US$ {resultado.dolares:.2f}"
    )
    return 1 if resultado.falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
