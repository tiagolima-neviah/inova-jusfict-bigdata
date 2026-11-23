"""Têmis em lote: o parecer de cada inovação, gravado em inova.parecer_ia.

A Têmis é a Assessora de IA da JusFict. Aqui ela lê uma inovação por vez e
emite um parecer estruturado (score de 0 a 100, se recomenda, resumo, custo,
ganho, retorno em meses, equipe e ferramentas). A conversa ao vivo mora no
inova-jusfict-app; este pacote só escreve os pareceres.

- `parecer.py`: o prompt, o formato da resposta e a chamada à API da Anthropic;
- `banco.py`: quais inovações ainda não têm parecer e a gravação;
- `lote.py`: o laço (em paralelo, retomável) e o controle de custo;
- `__main__.py`: o comando `uv run python -m inova_bigdata.temis`.

A chave fica em ANTHROPIC_API_KEY, no .env (nunca no git). Sem chave, o
pipeline segue sem a etapa e avisa.
"""

from __future__ import annotations

import os

# O modelo de cada parecer fica gravado na linha (coluna `modelo`).
MODELO_PADRAO = "claude-opus-5-5"

# Preço por milhão de tokens, em dólar, só para a estimativa impressa no fim
# do lote (a fatura de verdade é a do console da Anthropic).
PRECO_ENTRADA_USD = 4.0
PRECO_SAIDA_USD = 20.0


def modelo() -> str:
    return os.environ.get("TEMIS_MODELO") or MODELO_PADRAO


def tem_chave() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))
