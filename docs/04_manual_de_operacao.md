<a id="topo"></a>

# 04 · Manual de operação: instalar, atualizar o painel e resolver o que falhar

<!-- nav:start -->
[Home](../README.md) | [Hub de docs](README.md) | [← Arquitetura](02_arquitetura_do_pipeline.md)
<!-- nav:end -->

> Para quem opera o dado da JusFict Inova. Ensina a instalar este repositório do zero, a gerar a base sintética, a atualizar o Painel de Inovações com 1 comando, a emitir os pareceres da Têmis com o custo à vista, a conferir se o painel bate com a plataforma e o que fazer quando uma etapa falha. Quem seguir este manual consegue atender ao pedido "preciso do painel atualizado" sem perguntar a ninguém. Todos os dados são sintéticos.

## 1. O que este repositório faz, em 4 comandos

| Comando | O que faz | Quando usar |
|---|---|---|
| `uv run python -m inova_bigdata.pipeline` | atualiza o painel: parecer das inovações novas, cópia da produção, camadas de qualidade e carga do warehouse | sempre que pedirem o painel atualizado |
| `uv run python -m inova_bigdata.pipeline.conferir` | compara os números da plataforma com os do painel | depois de uma carga, ou para saber se o painel está defasado |
| `uv run python -m inova_bigdata.temis` | emite os pareceres da Têmis para tudo que está sem parecer | na primeira carga, ou depois de recriar a base sintética |
| `uv run python -m inova_bigdata.gerador` | recria a história sintética de 3 anos na plataforma | uma vez, na instalação; de novo só se quiser recomeçar |

## 2. Instalação

Pré-requisitos: Linux ou WSL, Python 3.12, [uv](https://docs.astral.sh/uv/) e Docker (para o staging). E a plataforma já instalada: o banco do `inova-jusfict-app` precisa existir, com o schema `inova` e as 12 pessoas de demonstração (o manual técnico de lá ensina). Primeira vez com o projeto? O [00 · Primeiros passos](https://github.com/tiagolima-neviah/inova-jusfict-app/blob/main/docs/00_primeiros_passos.md) mostra a ordem dos 2 repositórios num caminho só.

```bash
cd inova-jusfict-bigdata
uv sync                   # instala as dependências no .venv
cp .env.example .env      # depois edite o .env
```

**Por que copiar o `.env.example`, e não renomear.** O `.env.example` é o modelo: fica no git, não tem segredo e mostra quais variáveis existem. O `.env` é a sua cópia preenchida, com a string do banco e a chave, e o `.gitignore` o mantém fora do git. Renomear tira o modelo do lugar: o `git status` acusa o `.env.example` como apagado, e um commit descuidado o apaga do repositório para todo mundo. Por isso o comando é `cp`.

O `.env`:

| Variável | Para quê | Valor |
|---|---|---|
| `PLATAFORMA_URL` | a produção da plataforma (schema `inova`) | a MESMA string de `DATABASE_URL` no `.env` do `inova-jusfict-app`: a conexão direta do Neon, sem `-pooler` |
| `STAGING_URL` | o Postgres local do staging | já vem certo: `postgresql://staging:staging@localhost:5433/jusfict_staging` |
| `DW_NEON_URL` | o warehouse (schema `dw`) | em branco: usa o mesmo banco da produção ([ADR 0002](03_adr/0002-producao-e-warehouse-no-mesmo-neon.md)) |
| `LAKE_DIR` | onde ficam bronze, silver e gold | em branco: a pasta `lake/` deste repositório, fora do git |
| `ANTHROPIC_API_KEY` | a chave da API da Anthropic, para os pareceres da Têmis | criada em console.anthropic.com, em API Keys. Cole depois do `=`, sem aspas. Opcional: sem ela o pipeline roda igual, só não emite pareceres |
| `TEMIS_MODELO`, `TEMIS_LIMITE_NO_PIPELINE` | opcionais da Têmis | em branco valem os padrões (`claude-opus-5-5` e 30) |

O `.env` nunca vai para o git, e nem a string do banco nem a chave vão para uma conversa, um print ou um commit.

Na Neviah, este repositório vive na distro WSL `neviah-bigdata-dev` (a plataforma fica na `neviah-dash-dev`), com o Docker do staging já instalado. O `uv` vem pelo `mise`: em terminal interativo basta `uv ...`; em script, `~/.local/bin/mise exec -- uv ...`.

Confira a instalação sem tocar em nada:

```bash
uv run pytest                                        # 29 testes, sem banco e sem rede
uv run python -m inova_bigdata.gerador --so-conferir # simula a base e passa a régua, sem gravar
uv run python -m inova_bigdata.temis --estimar       # conta o que falta de parecer e estima o custo
```

## 3. Primeira carga, do zero

Faça 1 vez, nesta ordem:

```bash
uv run python -m inova_bigdata.gerador     # 1. a história sintética entra na plataforma
uv run python -m inova_bigdata.temis       # 2. a Têmis emite o parecer de cada inovação
uv run python -m inova_bigdata.pipeline    # 3. o painel recebe tudo
uv run python -m inova_bigdata.pipeline.conferir   # 4. a prova de que bate
```

**O gerador** cria cerca de 600 inovações de 2024 até hoje, com autores, histórico de status e conversas, a partir de uma semente fixa: rodar de novo gera a mesma base. Ele só apaga e recria o que é sintético. O que foi cadastrado na tela da plataforma e as 12 pessoas de demonstração nunca são tocados. Atenção: recriar a base sintética apaga os pareceres das inovações sintéticas, e eles custam para refazer (seção 5).

## 4. Atualizar o painel sob demanda

O cenário: alguém cadastrou ou moveu inovações na plataforma e o diretor pede o painel atualizado. O painel não lê a plataforma direto; ele lê o warehouse, que só muda quando o pipeline roda. Então:

```bash
uv run python -m inova_bigdata.pipeline
```

O que aparece na tela, etapa por etapa:

| Etapa | O que faz | Sinal de que deu certo |
|---|---|---|
| `temis` | pede à Têmis o parecer das inovações que ainda não têm | `pareceres novos N` |
| `staging` | copia a produção (Neon) para o Postgres local. Sobe o container sozinho se ele estiver parado | a contagem de linhas de cada tabela |
| `bronze` | grava a cópia em parquet, com a data da extração | idem |
| `silver` | limpa, tipa e passa a régua de qualidade | sem "RÉGUA REPROVOU" |
| `gold` | monta o modelo em estrela e passa a régua da modelagem | idem |
| `warehouse` | troca o schema `dw` inteiro, de uma vez, e grava a hora da carga | `pipeline concluído em Ns` |

Leva menos de 1 minuto (mais o tempo dos pareceres novos, alguns segundos cada). Depois, recarregue o painel no navegador: o rodapé mostra a hora nova.

**A prova.** `uv run python -m inova_bigdata.pipeline.conferir` compara 8 números entre a plataforma e o warehouse (inovações, eventos, implementadas, arquivadas, na fila, autores, custo total e pareceres). Depois de uma carga, todos batem e o comando sai com 0. Se alguém mexeu na plataforma depois da carga, a diferença aparece ali: é exatamente o que uma nova carga resolve.

**Só uma parte.** `uv run python -m inova_bigdata.pipeline silver gold` roda só as etapas pedidas, sempre na ordem do pipeline. Útil para reprocessar sem extrair de novo.

**Por que não é automático.** A carga roda por comando, de propósito ([ADR 0001](03_adr/0001-sem-orquestrador-na-v1.md)). Para agendar, basta chamar o mesmo comando de um agendador (cron, por exemplo) no horário desejado.

## 5. Os pareceres da Têmis e o custo

A Têmis lê uma inovação por vez e emite um parecer estruturado (score de 0 a 100, se recomenda, resumo, custo, ganho, retorno em meses, equipe e ferramentas), gravado em `inova.parecer_ia`. Cada parecer é uma chamada paga à API da Anthropic.

**Antes de gastar, estime:**

```bash
uv run python -m inova_bigdata.temis --estimar
```

Mostra quantas inovações estão sem parecer e a estimativa em dólar, sem chamar a API. Para a base inteira (cerca de 600 inovações), a ordem de grandeza é de US$ 10 a 20 com o modelo padrão.

**O lote:**

```bash
uv run python -m inova_bigdata.temis                 # tudo que está sem parecer
uv run python -m inova_bigdata.temis --limite 10     # só as 10 mais novas sem parecer
uv run python -m inova_bigdata.temis --paralelo 2    # menos chamadas simultâneas (padrão 4)
uv run python -m inova_bigdata.temis --refazer --limite 5   # parecer novo para 5 que já têm
```

O que saber:

- **Pode parar e retomar.** Cada parecer é gravado assim que chega. `Ctrl+C` interrompe; rodar de novo continua de onde parou, sem refazer nem cobrar de novo o que já foi gravado.
- **O custo real aparece no fim:** tokens de entrada, de saída e o valor aproximado. A fatura de verdade é a do console da Anthropic, onde também se define um limite de gasto mensal: defina.
- **Uma falha não derruba o lote.** A inovação que falhou fica sem parecer e entra na próxima rodada. O comando sai com 1 se houve falha.
- **Refazer não apaga.** `--refazer` grava um parecer novo ao lado do antigo; a plataforma e o painel usam sempre o mais recente.

**No pipeline, a etapa `temis` não gasta sozinha acima de um limite.** Ela avalia por conta própria até 30 inovações novas (`TEMIS_LIMITE_NO_PIPELINE`). Se houver mais do que isso sem parecer, ela não avalia nenhuma, avisa e manda rodar o lote, que mostra o custo: ninguém dispara 600 chamadas pagas sem saber. Sem chave no `.env`, a etapa é pulada com um aviso e o resto do pipeline roda igual.

## 6. Quando algo falha

| O que aparece | Causa provável | O que fazer |
|---|---|---|
| `PLATAFORMA_URL ou STAGING_URL ausente` | não existe `.env`, ou falta a variável | `cp .env.example .env` e preencha |
| `[staging] FALHOU` com erro de conexão em `localhost:5433` | o Docker não está rodando, ou o container não subiu | abra o Docker e rode `docker compose up -d`; depois, o pipeline de novo |
| `[staging] FALHOU` com erro de conexão no host do Neon | sem internet, string errada, ou o banco do Neon em repouso | confira a `PLATAFORMA_URL`; o Neon acorda sozinho na primeira conexão, então tente de novo |
| `RÉGUA REPROVOU; o pipeline para aqui`, seguido das regras | o dado não passou na qualidade (por exemplo, inovação sem autor ou data fora de ordem) | leia a regra reprovada: ela diz o que e quantas linhas. Corrija na origem e rode de novo. O warehouse fica como estava: carga ruim não entra |
| `[temis]` com `sem ANTHROPIC_API_KEY no .env: etapa pulada` | falta a chave | é só aviso. Para ter pareceres, ponha a chave no `.env` |
| `[temis]` com `N inovações sem parecer, acima do limite automático` | muita inovação sem parecer para a etapa avaliar sozinha | rode `uv run python -m inova_bigdata.temis` e, depois, o pipeline |
| lote da Têmis com `AuthenticationError` | chave inválida ou revogada | gere outra no console e troque no `.env` |
| lote da Têmis com `RateLimitError` repetido | conta nova, com limite de requisições baixo | rode com `--paralelo 1` ou `2`; o lote é retomável |
| o painel abre com "Painel ainda sem dados" | o schema `dw` não existe: o pipeline nunca rodou neste banco | rode o pipeline |
| o `conferir` mostra diferença | alguém mexeu na plataforma depois da última carga | rode o pipeline e confira de novo |

O staging é descartável: a extração recria tudo a cada rodada. `docker compose down -v` apaga os dados dele sem prejuízo. O mesmo vale para a pasta `lake/`.

## 7. O teste de aceite, do lado do dado

É o roteiro 5 do manual do usuário do `inova-jusfict-app`, visto daqui:

1. Na plataforma, cadastre 10 inovações e deixe-as em estados variados.
2. `uv run python -m inova_bigdata.pipeline.conferir`: a linha "inovações" mostra a diferença de 10 entre a plataforma e o warehouse.
3. `uv run python -m inova_bigdata.pipeline`: a etapa `temis` informa `pareceres novos 10`, e as demais carregam o warehouse.
4. `uv run python -m inova_bigdata.pipeline.conferir`: tudo bate.
5. No painel, o total subiu 10 e o rodapé mostra a hora nova; na área da Têmis, os 10 pareceres estão na lista.

---

[Início](#topo)
