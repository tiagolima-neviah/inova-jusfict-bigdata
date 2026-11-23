<a id="topo"></a>

# Hub de documentação · inova-jusfict-bigdata

<!-- nav:start -->
[Home](../README.md)
<!-- nav:end -->

> Todo documento deste hub segue o padrão da casa: o problema antes da solução, número sempre, dado sintético declarado. Comece pelo 01 se é a sua primeira visita; para operar, vá direto ao 04.

| Documento | O que responde |
|---|---|
| [01 · Problema e necessidade](01_problema_e_necessidade.md) | Por que a JusFict Inova existe e que perguntas o dado precisa responder |
| [02 · Arquitetura do pipeline](02_arquitetura_do_pipeline.md) | O caminho do dado, camada por camada, com as ferramentas e o porquê de cada uma |
| [04 · Manual de operação](04_manual_de_operacao.md) | Instalar, gerar a base, atualizar o painel com 1 comando, emitir os pareceres da Têmis com o custo à vista e resolver o que falhar |
| [ADR 0001 · Sem orquestrador na v1](03_adr/0001-sem-orquestrador-na-v1.md) | Por que a carga D-1 roda por comando e como o Dagster entraria |
| [ADR 0002 · Produção e warehouse no mesmo Neon](03_adr/0002-producao-e-warehouse-no-mesmo-neon.md) | Por que os dois schemas vivem no mesmo projeto Neon free |

As regras de qualidade e o modelo da gold estão documentados no próprio código: `REGUA` em `pipeline/silver.py` e em `pipeline/gold.py`, e `MODELO` em `pipeline/gold.py`.

---

[Início](#topo)
