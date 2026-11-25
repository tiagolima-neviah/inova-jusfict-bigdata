<a id="topo"></a>

# inova-jusfict-bigdata

<!-- nav:start -->
[Documentação](docs/README.md)
<!-- nav:end -->

> Pipeline de dados de ponta a ponta da **JusFict Inova**, a plataforma interna de gestão de inovações da JusFict, uma legal tech **fictícia**. Todos os dados deste repositório são **sintéticos e declarados**: nenhum dado real de pessoa ou empresa entra aqui. Projeto de portfólio e estudo da Neviah.

## O que é

A JusFict Inova registra as ideias dos colaboradores e garante que nenhuma se perca até a decisão da alta liderança. Este repositório cuida do caminho do dado, em 3 peças:

1. **Gerador sintético** (`inova_bigdata/gerador`): cria na plataforma a história de 3 anos de uso, cerca de 600 inovações, a partir de uma semente fixa e com régua própria.
2. **Pipeline** (`inova_bigdata/pipeline`): leva o dado da produção ao warehouse que o Painel de Inovações lê, por staging, bronze, silver e gold, com réguas de qualidade que param a carga quando o dado reprova.
3. **Têmis em lote** (`inova_bigdata/temis`): a assessora de IA emite o parecer de cada inovação pela API da Anthropic, com saída estruturada e o custo à vista.

O código da plataforma, do painel e da conversa com a Têmis vive no repositório irmão `inova-jusfict-app`.

## Arquitetura em uma linha

Produção (Postgres da plataforma, no Neon) → pareceres da Têmis → staging Postgres local → bronze (parquet) → silver (DuckDB, com régua de qualidade que se reprova sozinha) → gold (star schema, grão dia) → warehouse (mesmo projeto Neon, schema `dw`) → painel.

Detalhes em [docs/02_arquitetura_do_pipeline.md](docs/02_arquitetura_do_pipeline.md).

## Como usar

**Primeira vez?** A ordem que atravessa os 2 repositórios (a plataforma cria o banco, este repositório gera a história e carrega o painel, a plataforma sobe) está no [00 · Primeiros passos](https://github.com/tiagolima-neviah/inova-jusfict-app/blob/main/docs/00_primeiros_passos.md) do `inova-jusfict-app`.

```bash
uv sync && cp .env.example .env               # instale; copie o modelo (não renomeie) e preencha o .env
uv run python -m inova_bigdata.pipeline       # atualiza o painel, de ponta a ponta
uv run python -m inova_bigdata.pipeline.conferir   # prova que o painel bate com a plataforma
uv run python -m inova_bigdata.temis --estimar     # quanto custa emitir os pareceres que faltam
```

O passo a passo, da instalação ao que fazer quando algo falha, está no [manual de operação](docs/04_manual_de_operacao.md).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `docs/` | Hub de documentação: problema, arquitetura, decisões (ADRs) e manual de operação |
| `inova_bigdata/gerador/` | O gerador sintético: catálogo de temas, simulação, régua e carga |
| `inova_bigdata/pipeline/` | As etapas do pipeline e a conferência produção x warehouse |
| `inova_bigdata/temis/` | Os pareceres da Têmis: prompt, saída estruturada, lote e controle de custo |
| `tests/` | Testes do gerador, do pipeline e da Têmis, sem banco e sem rede |
| `docker-compose.yml` | O Postgres local do staging |

## Licença

MIT. Dados 100% sintéticos, gerados por código determinístico com semente fixa.

---

[Início](#topo)
