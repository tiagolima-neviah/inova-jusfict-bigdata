<a id="topo"></a>

# ADR 0003 · Produção e warehouse no mesmo projeto Neon, schemas separados

<!-- nav:start -->
[Home](../../README.md) | [Hub de docs](../README.md)
<!-- nav:end -->

> Status: aceita, 19/11/2026.

## Contexto

A demo precisa de dois bancos públicos: a produção da plataforma (schema relacional 3FN que o `inova-jusfict-app` usa) e o warehouse dimensional que o painel lê. O plano gratuito do Neon oferece 1 projeto com cerca de 0,5 GB. O desenho anterior mantinha a produção local e subia só um recorte do warehouse.

## Decisão

A produção da plataforma mora no Neon desde o início, no schema `inova`, e o warehouse mora no mesmo projeto, no schema `dw`. O pipeline extrai a réplica D-1 lendo a produção direto no Neon; staging, bronze, silver e gold ficam locais na WSL; a carga final escreve de volta no Neon, no schema `dw`.

## Justificativa

A plataforma no Render precisa de um Postgres acessível na internet de qualquer forma; mantê-la no Neon elimina um banco local a sincronizar e deixa a demo inteira viva com 1 serviço de banco. O volume do case (poucos milhares de inovações e suas movimentações) cabe com folga no limite do plano. O isolamento entre produção e análise continua provado onde importa: nenhuma consulta analítica roda na produção, porque a análise acontece no staging local e nas camadas de arquivo.

## Consequências

- O isolamento produção × análise na demo é lógico (schemas e conexões distintas) e o físico fica documentado como a evolução natural num cliente real.
- Extração e carga usam o endpoint direto (sem `-pooler`); a aplicação e o painel consultam pelo endpoint com `-pooler`.
- O `.env.example` reflete os dois papéis do Neon: `PLATAFORMA_URL` (schema `inova`) e `DW_NEON_URL` (schema `dw`).

---

[Início](#topo)
