<a id="topo"></a>

# ADR 0001 · Origem Oracle documentada, demo em Postgres de ponta a ponta

<!-- nav:start -->
[Home](../../README.md) | [Hub de docs](../README.md)
<!-- nav:end -->

> Status: aceita, 19/11/2026.

## Contexto

No case fictício, o sistema de produção da JusFict rodaria em Oracle, cenário comum em empresa desse porte. A demo precisa ficar no ar em serviços gratuitos: o Neon, que hospeda os bancos da demo, é Postgres e somente Postgres. Um Oracle XE em Docker local seria tecnicamente possível e gratuito.

## Decisão

A produção da plataforma na demo é Postgres, no Neon, e o Oracle fica documentado como a origem do cenário real. Não se constrói Oracle XE.

## Justificativa

O que a arquitetura precisa provar é o isolamento entre produção e análise via staging em D-1, e isso independe do fornecedor da origem: trocar o conector de extração é detalhe de driver, não de desenho. Construir o Oracle XE custaria dias de imagem, driver e réplica heterogênea sem acrescentar nada que o avaliador consiga ver na demo. Regra da casa: tecnologia só entra quando atende uma necessidade do caso; quando a única justificativa seria exibição, ela fica de fora, e a ausência deliberada também é evidência de critério.

## Consequências

- O staging lê a produção por conexão Postgres; num cliente Oracle, o mesmo passo usaria o driver Oracle com o mesmo contrato de saída (bronze idêntico).
- Na entrevista, a apresentação da arquitetura declara isso explicitamente, como honestidade de portfólio.
- Um laboratório com Oracle XE em Docker fica como estudo futuro (P2), fora deste repositório.

---

[Início](#topo)
