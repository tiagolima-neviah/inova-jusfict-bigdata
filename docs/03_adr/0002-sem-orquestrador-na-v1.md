<a id="topo"></a>

# ADR 0002 · Sem orquestrador na v1, com ganchos para o Dagster

<!-- nav:start -->
[Home](../../README.md) | [Hub de docs](../README.md)
<!-- nav:end -->

> Status: aceita, 19/11/2026.

## Contexto

O pipeline tem uma carga diária D-1 com etapas encadeadas (staging → bronze → silver → gold → warehouse). Orquestradores como o Dagster resolvem dependência, agendamento, retry e observabilidade de execução. O projeto tem prazo curto (entrega até 24/11/2026) e volume pequeno.

## Decisão

A v1 roda a carga por linha de comando (um comando por etapa e um comando que encadeia tudo), agendável por cron. O Dagster não entra na v1, e entra como P2 se o cronograma fechar antes do previsto.

## Justificativa

Com uma execução por dia, volume pequeno e um único operador, o custo de instalar, configurar e explicar o Dagster supera o ganho nesta primeira versão. A necessidade real que um orquestrador atende aqui (dependência entre etapas com retry e visibilidade) é registrada e o código nasce preparado: cada etapa é uma função pura com entrada e saída explícitas, exatamente o formato que vira um asset de Dagster sem reescrita. Precedente da casa: o projeto Fictitur fechou sem orquestrador pela mesma régua.

## Consequências

- `make carga` (ou comando equivalente) executa a sequência completa; o log estruturado de cada etapa registra início, fim, linhas movidas e falhas.
- Se o Dagster entrar (P2), cada função vira um asset e o agendamento sai do cron para o schedule do Dagster, sem mudar a lógica.
- Grafana segue o mesmo princípio: os logs nascem estruturados e prontos para leitura, e o dashboard de observabilidade é P2.

---

[Início](#topo)
