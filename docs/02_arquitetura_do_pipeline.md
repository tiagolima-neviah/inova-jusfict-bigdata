<a id="topo"></a>

# 02 · Arquitetura do pipeline

<!-- nav:start -->
[Home](../README.md) | [Hub de docs](README.md) | [← Problema](01_problema_e_necessidade.md)
<!-- nav:end -->

> O caminho do dado, camada por camada. Cada camada existe para resolver um problema nomeado; ferramenta sem problema não entra (é a regra da casa, e a ausência deliberada de uma ferramenta também é critério).

## 1. Visão geral

```
produção (Postgres no Neon, schema inova)
        │  extração D-1 (conexão direta, sem -pooler)
staging (Postgres local na WSL)            isola a análise da produção
        │  extração completa por tabela
bronze (parquet)                           foto fiel e barata da origem, com linhagem
        │  limpeza, tipos, regras
silver (DuckDB sobre parquet)              dado confiável; a régua de qualidade reprova sozinha
        │  modelagem dimensional
gold (parquet, star schema, grão dia)      um número só para cada pergunta do negócio
        │  carga por partição
warehouse (mesmo Neon, schema dw)          onde painel, ML e agente leem
```

A produção da plataforma e o warehouse vivem no mesmo projeto Neon free, em schemas separados ([ADR 0002](03_adr/0002-producao-e-warehouse-no-mesmo-neon.md)); staging e camadas de arquivo ficam locais na WSL.

## 2. Por que cada camada existe

| Camada | Problema que resolve |
|---|---|
| Staging | Consulta analítica não pode causar lentidão no sistema que os colaboradores usam. A réplica D-1, extraída do Neon para a WSL, isola os mundos, exatamente como no case do operador logístico |
| Bronze | Guardar a foto fiel da origem em formato colunar barato (parquet), com data de extração e linhagem, para reprocessar sem voltar à origem |
| Silver | Tipos certos, textos saneados, regras de integridade conferidas. A régua de qualidade é código que falha (exit 1) quando o dado reprova: validação prova concordância, não premissa |
| Gold | Star schema no grão dia: dimensões `dim_data`, `dim_departamento`, `dim_usuario`, `dim_status`, `dim_destino`; fatos `fato_inovacao` (uma linha por inovação, com as datas de cada marco) e `fato_movimentacao` (uma linha por transição de status). É o que garante "um número só" |
| Warehouse | Postgres dimensional para o painel e qualquer ferramenta de BI (Excel, Power BI, Tableau) conectarem; vive no schema `dw` do mesmo projeto Neon da produção (ADR 0002), público para a demo |

## 3. Ferramentas e o porquê

- **Python** como código core; **DuckDB** para transformar parquet com SQL sem subir servidor; **Arrow** para mover dado entre Postgres e parquet sem perder tipo.
- **fsspec** abstrai o storage (`file://` hoje, `s3://` se um dia for para AWS, GCP ou Azure; em volume grande, as transformações migrariam para Spark com o mesmo desenho de camadas). Portabilidade é desenho, não promessa.
- **Gerador sintético determinístico** com semente fixa popula a produção com 3 anos de uso simulado; régua própria reprova e regenera, porque defeito de base sintética se regenera, não se contorna. Decisão declarada: o dado sintético nasce limpo, sem sujeira fabricada; a régua da silver roda do mesmo jeito e a aprovação integral é o resultado esperado. Num cliente real é essa régua que segura a carga.
- **Esteira de qualidade de código** (ruff, mypy, pytest, CI no GitHub Actions) desde o primeiro commit.
- **Sem orquestrador na v1** ([ADR 0001](03_adr/0001-sem-orquestrador-na-v1.md)): a carga D-1 é uma sequência de funções puras chamadas por linha de comando, prontas para virarem assets de Dagster se o projeto crescer.

## 4. Consumidores da gold

1. **Painel de Inovações** (`inova-jusfict-app`, rota `/painel`): KPIs por departamento, colaborador, período, status e destino.
2. **Modelo de probabilidade de implementação**: LightGBM treinado sobre o histórico, com features congeladas no momento do cadastro (anti-vazamento), validação temporal e limiar por custo.
3. **Assessor de IA**: pareceres estruturados por inovação, gravados em banco e exibidos com selo de conteúdo gerado por IA sobre dados sintéticos.

---

[Início](#topo)
