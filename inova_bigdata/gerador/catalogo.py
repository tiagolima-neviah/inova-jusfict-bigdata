"""Catálogo do gerador: de onde saem os nomes, os temas e os textos.

Premissa do Tiago (20/11): inovação do cotidiano, não carro voador. O molde é
"automatizar o relatório que toma 4 horas da manhã": cada tema é uma melhoria
plausível de rotina, combinada com um alvo do dia a dia de cada departamento.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tema:
    titulo: str  # com {alvo}
    descricao: str
    objetivo: str
    beneficios: str  # com {horas} e {periodo}
    desafios: str
    ferramentas: str
    indicador: str
    destino: str  # app | automacao | relatorio | processo | outro
    custo_tipo: str  # sem_custo | software | servico | misto
    custo: tuple[int, int] | None  # faixa em reais, None quando sem custo


TEMAS: tuple[Tema, ...] = (
    Tema(
        "Automatizar o relatório de {alvo}",
        "Hoje o relatório de {alvo} é montado à mão, copiando dados de planilhas e telas. "
        "A ideia é gerar o relatório automaticamente e entregá-lo pronto no início do expediente.",
        "Eliminar o trabalho manual de montar o relatório de {alvo}.",
        "Cerca de {horas} h por {periodo} liberadas para análise, e menos erro de digitação.",
        "Padronizar a origem dos dados antes de automatizar.",
        "Python com agendamento simples, lendo o banco que já existe.",
        "Tempo de preparo do relatório de {alvo}.",
        "automacao",
        "sem_custo",
        None,
    ),
    Tema(
        "Alerta automático de {alvo}",
        "O acompanhamento de {alvo} depende de alguém lembrar de conferir. A ideia é um aviso "
        "automático, enviado a quem é responsável, quando algo entra na janela crítica.",
        "Parar de depender da memória de cada um para acompanhar {alvo}.",
        "Cerca de {horas} h por {periodo} de conferência manual eliminadas e menos risco de perda de prazo.",
        "Definir quem recebe cada aviso para não virar ruído.",
        "Rotina agendada e e-mail interno.",
        "Ocorrências de {alvo} perdidas por mês.",
        "automacao",
        "sem_custo",
        None,
    ),
    Tema(
        "Painel de acompanhamento de {alvo}",
        "As informações de {alvo} estão espalhadas em planilhas diferentes. A ideia é um painel "
        "único, atualizado todo dia, com o que está em dia, o que atrasou e quem cuida.",
        "Dar à equipe e à coordenação a mesma visão de {alvo}.",
        "Reunião semanal mais curta e cerca de {horas} h por {periodo} de consolidação manual a menos.",
        "Combinar uma definição única de cada indicador.",
        "O painel web da casa sobre o banco existente.",
        "Tempo de consolidação das informações de {alvo}.",
        "relatorio",
        "software",
        (3000, 9000),
    ),
    Tema(
        "Checklist padronizado para {alvo}",
        "Cada pessoa confere {alvo} de um jeito, e os mesmos erros voltam. A ideia é um checklist "
        "curto e obrigatório, igual para todos, revisado a cada trimestre.",
        "Reduzir o retrabalho em {alvo} causado por conferência incompleta.",
        "Menos devolução e cerca de {horas} h por {periodo} de retrabalho evitadas.",
        "Manter o checklist curto, para ser usado de verdade.",
        "Documento compartilhado; nenhuma ferramenta nova.",
        "Taxa de devolução em {alvo}.",
        "processo",
        "sem_custo",
        None,
    ),
    Tema(
        "Modelo único de documento para {alvo}",
        "Existem várias versões do mesmo documento de {alvo} circulando. A ideia é um modelo único, "
        "com os campos variáveis marcados, guardado em um lugar só.",
        "Acabar com as versões paralelas de documento em {alvo}.",
        "Documento pronto em minutos e cerca de {horas} h por {periodo} de redação repetida a menos.",
        "Aposentar os modelos antigos sem perder os casos especiais.",
        "Editor de texto e a pasta compartilhada da equipe.",
        "Tempo médio de preparo de documento em {alvo}.",
        "processo",
        "sem_custo",
        None,
    ),
    Tema(
        "Formulário digital para {alvo}",
        "Os pedidos de {alvo} chegam por e-mail, mensagem e conversa de corredor, e parte se perde. "
        "A ideia é um formulário único, com os campos obrigatórios e número de protocolo.",
        "Ter uma porta de entrada só para os pedidos de {alvo}.",
        "Nenhum pedido perdido e cerca de {horas} h por {periodo} gastas pedindo informação que faltou.",
        "Convencer as pessoas a abandonar o canal informal.",
        "Formulário web simples ligado ao banco da casa.",
        "Pedidos de {alvo} sem resposta em 48 h.",
        "app",
        "software",
        (4000, 12000),
    ),
    Tema(
        "Conferência em lote de {alvo}",
        "A conferência de {alvo} é feita item por item, na tela. A ideia é conferir tudo de uma vez, "
        "cruzando as 2 bases e mostrando só as divergências.",
        "Trocar a conferência item a item de {alvo} por conferência das exceções.",
        "Cerca de {horas} h por {periodo} liberadas e divergência achada no mesmo dia.",
        "Garantir que as 2 bases tenham uma chave em comum.",
        "Consulta SQL agendada e planilha de divergências.",
        "Tempo gasto na conferência de {alvo}.",
        "automacao",
        "sem_custo",
        None,
    ),
    Tema(
        "Base de conhecimento sobre {alvo}",
        "As mesmas dúvidas sobre {alvo} são respondidas várias vezes, por pessoas diferentes. "
        "A ideia é registrar cada resposta boa em uma base pesquisável.",
        "Parar de responder do zero a mesma dúvida sobre {alvo}.",
        "Gente nova produtiva mais cedo e cerca de {horas} h por {periodo} de interrupção a menos.",
        "Manter a base atualizada: alguém precisa ser dono dela.",
        "A wiki interna que já existe.",
        "Dúvidas repetidas sobre {alvo} por mês.",
        "processo",
        "sem_custo",
        None,
    ),
    Tema(
        "Integração entre sistemas para {alvo}",
        "Os dados de {alvo} são digitados 2 vezes, em 2 sistemas. A ideia é integrar os 2, para o "
        "dado ser lançado uma vez só e aparecer nos 2 lados.",
        "Acabar com a dupla digitação em {alvo}.",
        "Cerca de {horas} h por {periodo} de digitação eliminadas e fim das divergências entre sistemas.",
        "Depende de acesso técnico aos 2 sistemas e de teste cuidadoso.",
        "API dos sistemas e uma rotina de sincronização.",
        "Divergências entre os sistemas em {alvo}.",
        "automacao",
        "misto",
        (8000, 28000),
    ),
    Tema(
        "Fila única de atendimento para {alvo}",
        "Não há ordem clara para tratar {alvo}: quem grita mais é atendido primeiro. A ideia é uma "
        "fila única, com prioridade combinada e posição visível a quem pediu.",
        "Dar ordem e transparência ao atendimento de {alvo}.",
        "Menos interrupção e cerca de {horas} h por {periodo} gastas perguntando em que pé está.",
        "Combinar o critério de prioridade com todas as áreas.",
        "Quadro de fila no sistema de chamados existente.",
        "Tempo médio de espera em {alvo}.",
        "app",
        "software",
        (2500, 8000),
    ),
    Tema(
        "Indicador semanal de {alvo}",
        "Ninguém sabe dizer, de bate-pronto, como anda {alvo}. A ideia é 1 número por semana, "
        "com a mesma definição, enviado toda segunda-feira.",
        "Ter uma medida simples e constante de {alvo}.",
        "Decisão baseada em número e cerca de {horas} h por {periodo} de levantamento sob demanda a menos.",
        "Escolher 1 indicador só, em vez de 10.",
        "Consulta agendada e e-mail.",
        "Dias de atraso para saber como anda {alvo}.",
        "relatorio",
        "sem_custo",
        None,
    ),
    Tema(
        "Revisão em dupla de {alvo}",
        "Os erros em {alvo} só aparecem depois, quando já custam caro. A ideia é uma revisão rápida "
        "por um colega antes da entrega, nos casos acima de um limite combinado.",
        "Achar o erro em {alvo} antes da entrega, não depois.",
        "Menos correção depois da entrega e cerca de {horas} h por {periodo} de retrabalho evitadas.",
        "Não virar gargalo: a revisão precisa caber em 15 minutos.",
        "Nenhuma ferramenta nova; só o combinado da equipe.",
        "Erros em {alvo} encontrados depois da entrega.",
        "processo",
        "sem_custo",
        None,
    ),
    Tema(
        "Treinamento rápido sobre {alvo}",
        "Boa parte dos erros em {alvo} vem de quem nunca foi treinado. A ideia é um treinamento de "
        "1 hora, gravado, obrigatório para quem entra.",
        "Nivelar o conhecimento da equipe sobre {alvo}.",
        "Menos erro de iniciante e cerca de {horas} h por {periodo} de supervisão liberadas.",
        "Gravar uma vez e manter atualizado.",
        "Gravação de tela e a plataforma de cursos da casa.",
        "Erros em {alvo} cometidos no primeiro mês de casa.",
        "processo",
        "servico",
        (1500, 6000),
    ),
    Tema(
        "Assistente de IA para {alvo}",
        "O primeiro rascunho de {alvo} é sempre parecido e toma tempo de quem deveria revisar. "
        "A ideia é um assistente de IA que produz o rascunho, sempre revisado por uma pessoa.",
        "Devolver à equipe o tempo gasto no primeiro rascunho de {alvo}.",
        "Cerca de {horas} h por {periodo} devolvidas e revisão mais atenta.",
        "Dado sensível tratado com cuidado; revisão humana obrigatória.",
        "Modelo de linguagem com base de exemplos da casa e fila de revisão.",
        "Tempo até o primeiro rascunho de {alvo}.",
        "app",
        "misto",
        (15000, 45000),
    ),
)

# Os alvos são a rotina de cada departamento. Os nomes dos departamentos têm de
# bater com a tabela inova.departamento.
ALVOS: dict[str, tuple[str, ...]] = {
    "Produto Jurídico": (
        "prazos processuais",
        "intimações",
        "petições iniciais",
        "pareceres jurídicos",
        "certidões de dívida ativa",
        "execuções fiscais",
        "recursos",
        "cálculos judiciais",
    ),
    "Tecnologia": (
        "chamados de suporte",
        "publicações em homologação",
        "cópias de segurança",
        "acessos de usuários",
        "incidentes de produção",
        "testes de regressão",
        "inventário de servidores",
        "documentação técnica",
    ),
    "Comercial": (
        "propostas comerciais",
        "renovações de contrato",
        "oportunidades de licitação",
        "visitas a clientes",
        "editais",
        "pedidos de demonstração",
        "comissões",
        "cadastros de clientes",
    ),
    "Atendimento e Operações": (
        "chamados de clientes",
        "dúvidas frequentes",
        "implantações",
        "treinamentos de clientes",
        "pesquisas de satisfação",
        "escalonamentos",
        "relatos de erro",
        "agendamentos",
    ),
    "Administrativo": (
        "reembolsos",
        "notas fiscais",
        "férias",
        "compras",
        "contratos de fornecedores",
        "patrimônio",
        "folha de ponto",
        "viagens",
    ),
}

# Quantos colaboradores cada departamento tem ao todo (os 5 analistas de
# demonstração inclusos): 170 pessoas na base.
COLABORADORES_POR_DEPARTAMENTO: dict[str, int] = {
    "Produto Jurídico": 38,
    "Tecnologia": 44,
    "Comercial": 30,
    "Atendimento e Operações": 36,
    "Administrativo": 22,
}

CARGOS: dict[str, tuple[str, ...]] = {
    "Produto Jurídico": ("Analista Jurídico", "Assistente Jurídico", "Analista de Produto Jurídico"),
    "Tecnologia": (
        "Analista de Sistemas",
        "Desenvolvedor",
        "Analista de Infraestrutura",
        "Analista de Dados",
    ),
    "Comercial": ("Analista Comercial", "Executivo de Contas", "Assistente Comercial"),
    "Atendimento e Operações": (
        "Analista de Atendimento",
        "Analista de Implantação",
        "Assistente de Suporte",
    ),
    "Administrativo": ("Analista Administrativo", "Assistente Financeiro", "Analista de Pessoas"),
}

PRIMEIROS_NOMES: tuple[str, ...] = (
    "Ana", "Bruno", "Camila", "Daniel", "Eduarda", "Fábio", "Gabriela", "Henrique", "Isabela", "Júlio",
    "Karina", "Leonardo", "Mariana", "Natan", "Olívia", "Paulo", "Queila", "Rafael", "Sabrina", "Tiago",
    "Úrsula", "Vinícius", "Wesley", "Yasmin", "Zeca", "Alice", "Bernardo", "Clara", "Diego", "Elisa",
    "Fernando", "Giovana", "Heitor", "Ingrid", "Jonas", "Larissa", "Marcelo", "Noemi", "Otávio", "Priscila",
    "Renato", "Simone", "Tomás", "Valéria", "Wagner", "Aline", "Caio", "Denise", "Estêvão", "Flávia",
)  # fmt: skip

SOBRENOMES: tuple[str, ...] = (
    "Almeida", "Barbosa", "Cardoso", "Dias", "Esteves", "Farias", "Gomes", "Henriques", "Inácio", "Jardim",
    "Lacerda", "Macedo", "Nogueira", "Oliveira", "Pacheco", "Queiroz", "Ramos", "Santana", "Teixeira", "Uchoa",
    "Vasconcelos", "Xavier", "Zanetti", "Araújo", "Bastos", "Campos", "Duarte", "Fonseca", "Guimarães", "Leite",
    "Monteiro", "Neves", "Paiva", "Rezende", "Siqueira", "Tavares", "Viana", "Antunes", "Brandão", "Coelho",
)  # fmt: skip

JUSTIFICATIVAS_ARQUIVAMENTO: tuple[str, ...] = (
    "A ideia é boa no espírito, mas duplicaria um canal que já existe e criaria registro sem rastro. "
    "Fica registrada para revisita se o cenário mudar.",
    "O ganho estimado não cobre o custo de manter a solução no ar. Vale reavaliar quando o volume crescer.",
    "Depende de acesso a um sistema de terceiro que não será liberado neste ano.",
    "O problema descrito foi resolvido por outra inovação já em implementação; não faz sentido correr em paralelo.",
    "Envolve dado sensível fora do ambiente controlado; o risco supera o benefício na forma proposta.",
    "A rotina que a ideia otimiza será descontinuada no próximo semestre.",
    "Proposta muito ampla para ser tratada como uma inovação só; o autor foi orientado a fatiar e reapresentar.",
    "Sem dono claro para manter a solução depois de pronta; arquivada até a área definir o responsável.",
)

PERGUNTAS_DO_AVALIADOR: tuple[str, ...] = (
    "Quantas pessoas fazem essa rotina hoje, e com que frequência?",
    "A origem dos dados já é única ou parte ainda vive em planilha?",
    "Isso cobre também os casos de exceção ou só o fluxo normal?",
    "Você já tem um exemplo do antes e do depois para mostrarmos à diretoria?",
    "Outra área usa a mesma rotina? Se sim, a solução pode servir para ela também.",
    "O que acontece hoje quando essa conferência falha?",
)

RESPOSTAS_DO_AUTOR: tuple[str, ...] = (
    "Hoje são 3 pessoas, todos os dias. Mandei a planilha com a medição da última semana.",
    "A maior parte já está no sistema; as exceções ainda vivem em planilha, e a ideia começa pelo que está no sistema.",
    "Cobre o fluxo normal, que é a grande maioria. As exceções continuam manuais nesta primeira versão.",
    "Tenho, sim: anexei o exemplo da semana passada, com o tempo gasto em cada etapa.",
    "A outra equipe faz parecido. Conversei com eles e a solução serviria com pouco ajuste.",
    "Quando falha, só descobrimos dias depois, com retrabalho. É exatamente a dor que a ideia ataca.",
)

MARCOS_MVP: tuple[str, ...] = (
    "MVP apresentado à diretoria.",
    "Protótipo validado com a equipe que vai usar.",
    "Documento do novo processo aprovado: fluxo, regras e atribuições.",
)

MARCOS_IMPLEMENTACAO: tuple[str, ...] = (
    "Aprovado para produção.",
    "MVP dispensado: melhoria simples, segue direto para a implementação.",
    "Desenvolvimento iniciado pela equipe responsável.",
)

MARCOS_IMPLEMENTADA: tuple[str, ...] = (
    "Em operação.",
    "Em uso pela equipe desde esta data; indicador de sucesso em acompanhamento.",
    "Entregue e adotada pela área.",
)

LOCAIS_BRAINSTORM: tuple[str, ...] = ("sala de reunião 1", "sala de reunião 2", "on-line")

ROTULOS_DESTINO: dict[str, str] = {
    "app": "Aplicativo",
    "automacao": "Automação",
    "relatorio": "Relatório",
    "processo": "Processo (sem TI)",
    "outro": "Outro",
}
