<a id="topo"></a>

# inova-jusfict-bigdata

<!-- nav:start -->
[Documentação](docs/README.md)
<!-- nav:end -->

> Pipeline de dados de ponta a ponta da **JusFict Inova**, a plataforma interna de gestão de inovações da JusFict, uma legal tech **fictícia**. Todos os dados deste repositório são **sintéticos e declarados**: nenhum dado real de pessoa ou empresa entra aqui. Projeto de portfólio e estudo da Neviah.

## O que é

A JusFict Inova registra as ideias dos colaboradores e garante que nenhuma se perca até a decisão da alta liderança. Este repositório cuida do caminho do dado: a partir do banco relacional da plataforma (produção), monta o staging em D-1, as camadas bronze, silver e gold em parquet e o warehouse multidimensional em Postgres, que alimenta o Painel de Inovações, o modelo de machine learning e o Assessor de IA.

O código da plataforma e do painel vive no repositório irmão `inova-jusfict-app`.

## Arquitetura em uma linha

Produção (Postgres da plataforma; no cliente real seria Oracle, ver ADR 0001) → staging Postgres (réplica D-1) → bronze (parquet) → silver (DuckDB, com régua de qualidade que se reprova sozinha) → gold (star schema, grão dia) → warehouse Postgres (recorte no Neon) → painel, ML e agente.

Detalhes em [docs/02_arquitetura_do_pipeline.md](docs/02_arquitetura_do_pipeline.md).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `docs/` | Hub de documentação: problema, arquitetura, decisões (ADRs) |
| `src/` | Código do pipeline (nasce na fase v0.4.0) |
| `sql/` | DDL do staging e do warehouse (nasce na fase v0.4.0) |

## Licença

MIT. Dados 100% sintéticos, gerados por código determinístico com semente fixa.

---

[Início](#topo)
