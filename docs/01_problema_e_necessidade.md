<a id="topo"></a>

# 01 · Problema e necessidade

<!-- nav:start -->
[Home](../README.md) | [Hub de docs](README.md) | [Arquitetura →](02_arquitetura_do_pipeline.md)
<!-- nav:end -->

> Contexto fictício, declarado: a JusFict é uma legal tech de gestão de processos para Procuradorias Públicas, com cerca de 170 colaboradores. Os números deste documento são premissas do case, não medições reais.

## 1. O problema

A JusFict cresceu rápido e as ideias dos colaboradores se perdiam: sugestões ditas em reunião sem registro, e-mails esquecidos, planilhas paralelas por departamento. Três consequências para o negócio:

1. **Ideia boa morria no caminho.** Nenhum rastro de quem sugeriu, quem avaliou e por que parou.
2. **O colaborador desanimava.** Sem retorno, a segunda ideia não vinha. Para uma empresa cujos valores incluem reconhecimento e respeito, isso é passivo cultural.
3. **A liderança decidia às cegas.** Sem visão de quantas ideias existem, onde estão paradas e quanto tempo levam até a decisão, não há gestão de inovação, há sorte.

## 2. A necessidade

Um lugar único onde toda inovação é registrada, avaliada com rastro auditável e chega garantidamente à alta liderança, e um painel que responda, por departamento, colaborador, período, status e destino:

- Quantas inovações existem e em que etapa do ciclo de vida estão?
- Quanto tempo uma inovação leva em cada etapa, e onde está o gargalo?
- Quantas chegam à implementação, e quantas morrem? Quem decide, decide rápido?
- Que departamentos e colaboradores mais contribuem?
- Quais ideias boas estão paradas sem avaliação?

## 3. A solução em duas peças

1. **A plataforma** (repositório `inova-jusfict-app`): o sistema transacional onde a inovação nasce e vive. Escopo completo em `docs/02_escopo_plataforma_inovacoes.md` daquele repositório.
2. **Este pipeline**: leva o dado transacional, sem pesar na produção, até um warehouse dimensional onde o Painel de Inovações, o modelo de probabilidade de implementação e o Assessor de IA leem.

## 4. Premissas do case

- Produção da plataforma e warehouse vivem no mesmo projeto Neon free, em schemas separados ([ADR 0002](03_adr/0002-producao-e-warehouse-no-mesmo-neon.md)).
- Carga em D-1: o painel conta a história até ontem, e isso fica declarado no rodapé dele.
- Volume sintético: plataforma viva desde 02/01/2024 (2024 e 2025 cheios, 2026 até 20/11), com algumas centenas de inovações do cotidiano e histórico de transições e interações coerentes.

---

[Início](#topo)
