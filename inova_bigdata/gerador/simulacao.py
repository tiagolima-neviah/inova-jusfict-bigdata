"""Simulação determinística de quase 3 anos de uso da plataforma.

Funções puras: recebem a semente e devolvem pessoas, inovações, eventos de
histórico e mensagens, sem tocar banco. A mesma semente produz sempre a mesma
base. A simulação segue as regras da plataforma (doc 02 do inova-jusfict-app):

- quem trata uma inovação está sempre ACIMA do autor;
- o arquivamento é uma cadeia que só se consuma na presidência;
- nenhum evento acontece depois da data de corte: o que "ainda não deu tempo"
  fica no status em que estava, e é isso que enche as caixas de trabalho.
"""

from __future__ import annotations

import random
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from inova_bigdata.gerador import catalogo as cat

SEMENTE = 20261120
DATA_INICIO = date(2024, 1, 2)  # a plataforma "entrou no ar" aqui
DATA_CORTE = date(2026, 11, 20)  # nada acontece depois deste dia

DIRETOR = "davi.alencar"
PRESIDENTE = "abraao.almeida"

# Média de inovações por mês em cada ano (a adesão cresce) e o peso de cada
# mês: pico nas campanhas internas de maio e setembro/outubro, vale em
# dezembro e janeiro.
MEDIA_MENSAL = {2024: 14.0, 2025: 17.5, 2026: 20.0}
SAZONALIDADE = {
    1: 0.75, 2: 0.90, 3: 1.10, 4: 1.10, 5: 1.20, 6: 1.00,
    7: 0.80, 8: 1.10, 9: 1.20, 10: 1.20, 11: 1.05, 12: 0.40,
}  # fmt: skip
PROPENSAO = {
    "Produto Jurídico": 1.00,
    "Tecnologia": 1.25,
    "Comercial": 0.85,
    "Atendimento e Operações": 1.05,
    "Administrativo": 0.80,
}
NASCIMENTO_NA_DIRECAO = {
    2: "Inovação de supervisor: segue direto para o diretor.",
    3: "Inovação do diretor: segue para a presidência.",
}


@dataclass(frozen=True)
class Pessoa:
    login: str
    nome: str
    cargo: str
    nivel: int  # 1 colaborador, 2 supervisor, 3 diretor, 4 presidência
    departamentos: tuple[str, ...]
    demonstracao: bool  # True para os 12 que já existem na plataforma


@dataclass(frozen=True)
class Evento:
    status_de: str | None
    status_para: str
    ator: str  # login
    quando: datetime
    observacao: str | None


@dataclass(frozen=True)
class Mensagem:
    autor: str  # login
    texto: str
    quando: datetime


@dataclass
class InovacaoSintetica:
    titulo: str
    descricao: str
    objetivo: str
    beneficios: str
    desafios: str
    ferramentas: str
    indicador: str
    prazo_desejado: date | None
    custo_tipo: str
    custo_valor: int | None
    autor: str  # login
    departamento: str
    criada_em: datetime
    destino: str | None = None
    brainstorm_em: datetime | None = None
    brainstorm_local: str | None = None
    departamento_responsavel: str | None = None
    eventos: list[Evento] = field(default_factory=list)
    mensagens: list[Mensagem] = field(default_factory=list)

    @property
    def status(self) -> str:
        return self.eventos[-1].status_para

    @property
    def atualizada_em(self) -> datetime:
        return self.eventos[-1].quando


@dataclass(frozen=True)
class Base:
    pessoas: list[Pessoa]
    inovacoes: list[InovacaoSintetica]


# As 12 pessoas de demonstração, exatamente como no seed do inova-jusfict-app.
DEMONSTRACAO: tuple[Pessoa, ...] = (
    Pessoa("joao.silva", "João Silva", "Analista Jurídico", 1, ("Produto Jurídico",), True),
    Pessoa("pedro.lima", "Pedro Lima", "Analista de Sistemas", 1, ("Tecnologia",), True),
    Pessoa("felipe.pereira", "Felipe Pereira", "Analista Comercial", 1, ("Comercial",), True),
    Pessoa("ester.rocha", "Ester Rocha", "Analista de Atendimento", 1, ("Atendimento e Operações",), True),
    Pessoa("rute.moraes", "Rute Moraes", "Analista Administrativo", 1, ("Administrativo",), True),
    Pessoa(
        "ezequiel.amorim",
        "Ezequiel Amorim",
        "Coordenador de Produto Jurídico",
        2,
        ("Produto Jurídico",),
        True,
    ),
    Pessoa("elias.pereira", "Elias Pereira", "Coordenador de Tecnologia", 2, ("Tecnologia",), True),
    Pessoa("maria.madalena", "Maria Madalena", "Coordenadora Comercial", 2, ("Comercial",), True),
    Pessoa(
        "debora.martins",
        "Débora Martins",
        "Coordenadora de Atendimento e Administrativo",
        2,
        ("Atendimento e Operações", "Administrativo"),
        True,
    ),
    Pessoa("sara.goncalves", "Sara Gonçalves", "Coordenadora Administrativa", 2, ("Administrativo",), True),
    Pessoa(DIRETOR, "Davi Alencar", "Diretor Geral", 3, (), True),
    Pessoa(PRESIDENTE, "Abraão Almeida", "Presidente", 4, (), True),
)


def _login(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return sem_acento.lower().replace(" ", ".")


def gerar_pessoas(rng: random.Random) -> list[Pessoa]:
    """As 12 de demonstração mais os colaboradores sintéticos, até 170 na base."""
    pessoas = list(DEMONSTRACAO)
    usados = {pessoa.login for pessoa in pessoas}
    combinacoes = [
        f"{primeiro} {sobrenome}" for primeiro in cat.PRIMEIROS_NOMES for sobrenome in cat.SOBRENOMES
    ]
    rng.shuffle(combinacoes)
    fila = iter(combinacoes)
    for departamento, total in cat.COLABORADORES_POR_DEPARTAMENTO.items():
        ja_tem = sum(1 for p in DEMONSTRACAO if p.nivel == 1 and departamento in p.departamentos)
        for _ in range(total - ja_tem):
            nome = next(n for n in fila if _login(n) not in usados)
            usados.add(_login(nome))
            cargo = rng.choice(cat.CARGOS[departamento])
            pessoas.append(Pessoa(_login(nome), nome, cargo, 1, (departamento,), False))
    return pessoas


def _dias_uteis_do_mes(ano: int, mes: int) -> list[date]:
    dia = date(ano, mes, 1)
    dias = []
    while dia.month == mes:
        if dia.weekday() < 5 and DATA_INICIO <= dia <= DATA_CORTE:
            dias.append(dia)
        dia += timedelta(days=1)
    return dias


def _somar_dias_uteis(rng: random.Random, inicio: datetime, dias: int) -> datetime:
    """`dias` dias úteis depois de `inicio`, em horário comercial. Sempre no futuro."""
    dia = inicio.date()
    restantes = max(dias, 1)
    while restantes > 0:
        dia += timedelta(days=1)
        if dia.weekday() < 5:
            restantes -= 1
    return datetime.combine(dia, time(rng.randint(8, 17), rng.choice((0, 10, 15, 20, 30, 40, 45, 50))))


class _Trilha:
    """Anda com a inovação pelo ciclo de vida, respeitando a data de corte."""

    def __init__(self, rng: random.Random, inovacao: InovacaoSintetica) -> None:
        self.rng = rng
        self.inovacao = inovacao
        self.agora = inovacao.criada_em

    def instante(self, dias: tuple[int, int]) -> datetime | None:
        """Quando seria o próximo passo; None se cairia depois do corte."""
        quando = _somar_dias_uteis(self.rng, self.agora, self.rng.randint(*dias))
        return quando if quando.date() <= DATA_CORTE else None

    def registrar(self, para: str, ator: str, quando: datetime, observacao: str | None) -> None:
        de = self.inovacao.eventos[-1].status_para
        self.inovacao.eventos.append(Evento(de, para, ator, quando, observacao))
        self.agora = quando

    def passo(self, para: str, ator: str, dias: tuple[int, int], observacao: str | None = None) -> bool:
        quando = self.instante(dias)
        if quando is None:
            return False
        self.registrar(para, ator, quando, observacao)
        return True

    def marco(self, ator: str, dias: tuple[int, int], observacao: str) -> bool:
        """Marco fino: registro no histórico sem mudar de status."""
        return self.passo(self.inovacao.status, ator, dias, observacao)


def _conversar(rng: random.Random, inovacao: InovacaoSintetica, avaliador: str, inicio: datetime) -> None:
    """Perguntas de quem avalia e respostas do autor, alternadas."""
    quando = inicio
    for _ in range(rng.choice((0, 0, 1, 1, 2, 2, 3))):
        indice = rng.randrange(len(cat.PERGUNTAS_DO_AVALIADOR))
        quando += timedelta(hours=rng.randint(1, 20), minutes=rng.randint(0, 59))
        if quando.date() > DATA_CORTE:
            return
        inovacao.mensagens.append(Mensagem(avaliador, cat.PERGUNTAS_DO_AVALIADOR[indice], quando))
        quando += timedelta(hours=rng.randint(1, 26), minutes=rng.randint(0, 59))
        if quando.date() > DATA_CORTE:
            return
        inovacao.mensagens.append(Mensagem(inovacao.autor, cat.RESPOSTAS_DO_AUTOR[indice], quando))


def _agendar_brainstorm(trilha: _Trilha, ator: str, dias: tuple[int, int], *, recusando: bool) -> bool:
    quando = trilha.instante(dias)
    if quando is None:
        return False
    rng = trilha.rng
    reuniao = _somar_dias_uteis(rng, quando, rng.randint(4, 12)).replace(
        hour=rng.randint(9, 16), minute=rng.choice((0, 30))
    )
    local = rng.choice(cat.LOCAIS_BRAINSTORM)
    prefixo = "Arquivamento recusado. " if recusando else ""
    trilha.registrar(
        "brainstorm",
        ator,
        quando,
        f"{prefixo}Reunião agendada: {reuniao:%d/%m/%Y}, {reuniao:%Hh%M}, {local}.",
    )
    trilha.inovacao.brainstorm_em = reuniao
    trilha.inovacao.brainstorm_local = local
    return True


def _responsavel(rng: random.Random, inovacao: InovacaoSintetica, tema: cat.Tema) -> str:
    if tema.destino in ("app", "automacao", "relatorio") and rng.random() < 0.75:
        return "Tecnologia"
    return inovacao.departamento


def _executar(trilha: _Trilha, condutor: str) -> None:
    """Do escopo até a entrada em operação."""
    rng = trilha.rng
    if rng.random() < 0.6:
        if not trilha.passo("mvp", condutor, (10, 35), rng.choice(cat.MARCOS_MVP)):
            return
        if not trilha.passo("em_implementacao", condutor, (8, 30), cat.MARCOS_IMPLEMENTACAO[0]):
            return
    elif not trilha.passo("em_implementacao", condutor, (10, 35), rng.choice(cat.MARCOS_IMPLEMENTACAO[1:])):
        return
    trilha.passo("implementada", condutor, (20, 80), rng.choice(cat.MARCOS_IMPLEMENTADA))


def _decidir_brainstorm(trilha: _Trilha, condutor: str, tema: cat.Tema) -> None:
    rng = trilha.rng
    inovacao = trilha.inovacao
    reuniao = inovacao.brainstorm_em
    assert reuniao is not None
    quando = reuniao + timedelta(hours=rng.randint(1, 3))
    if rng.random() < 0.5:
        quando = _somar_dias_uteis(rng, reuniao, rng.randint(1, 3))
    if quando.date() > DATA_CORTE:
        return  # a reunião ainda não aconteceu, ou a decisão ainda não foi registrada
    sorteio = rng.random()
    if sorteio < 0.50:
        responsavel = _responsavel(rng, inovacao, tema)
        trilha.registrar(
            "em_escopo",
            condutor,
            quando,
            f"Decisão do brainstorm: viável, segue para o escopo. Departamento responsável: {responsavel}.",
        )
        inovacao.departamento_responsavel = responsavel
        _executar(trilha, condutor)
    elif sorteio < 0.80:
        trilha.registrar(
            "em_espera",
            condutor,
            quando,
            "Decisão do brainstorm: boa e viável, mas não agora; revisitar na próxima janela.",
        )
        if rng.random() < 0.25 and trilha.passo(
            "com_diretor", condutor, (40, 150), "Revisitada: volta ao diretor."
        ):
            responsavel = _responsavel(rng, inovacao, tema)
            if trilha.passo(
                "em_escopo",
                condutor,
                (3, 12),
                f"Segue direto para o escopo. Departamento responsável: {responsavel}.",
            ):
                inovacao.departamento_responsavel = responsavel
                _executar(trilha, condutor)
    else:
        trilha.registrar(
            "ja_existe",
            condutor,
            quando,
            "Decisão do brainstorm: a solução já existe na casa; apontada ao autor, com reconhecimento.",
        )


def _dirigir(trilha: _Trilha, condutor: str, tema: cat.Tema) -> None:
    """O trecho da direção, a partir de 'com_diretor'."""
    rng = trilha.rng
    inovacao = trilha.inovacao
    sorteio = rng.random()
    if sorteio < 0.05:
        return  # segue com a direção, sem decisão ainda
    if sorteio < 0.29:
        justificativa = rng.choice(cat.JUSTIFICATIVAS_ARQUIVAMENTO)
        if condutor == PRESIDENTE:  # a presidência é a última instância: arquiva direto
            trilha.passo("arquivo_morto", PRESIDENTE, (3, 12), justificativa)
            return
        if not trilha.passo("arquivo_morto_proposto", DIRETOR, (3, 12), justificativa):
            return
        if rng.random() < 0.78:
            trilha.passo("arquivo_morto", PRESIDENTE, (2, 10), "Arquivamento confirmado pela presidência.")
            return
        if _agendar_brainstorm(trilha, PRESIDENTE, (2, 10), recusando=True):
            _decidir_brainstorm(trilha, condutor, tema)
        return
    if sorteio < 0.43:
        responsavel = _responsavel(rng, inovacao, tema)
        if trilha.passo(
            "em_escopo",
            condutor,
            (3, 12),
            f"Segue direto para o escopo. Departamento responsável: {responsavel}.",
        ):
            inovacao.departamento_responsavel = responsavel
            _executar(trilha, condutor)
        return
    if _agendar_brainstorm(trilha, condutor, (3, 12), recusando=False):
        _decidir_brainstorm(trilha, condutor, tema)


def _simular_ciclo(
    rng: random.Random,
    inovacao: InovacaoSintetica,
    autor: Pessoa,
    supervisores: list[str],
    tema: cat.Tema,
) -> None:
    trilha = _Trilha(rng, inovacao)
    rotulo_destino = cat.ROTULOS_DESTINO[tema.destino]

    if autor.nivel >= 2:
        # Regra de 23/11: nasce na caixa de quem está acima do autor.
        condutor = DIRETOR if autor.nivel == 2 else PRESIDENTE
        inovacao.eventos.append(
            Evento(None, "com_diretor", autor.login, inovacao.criada_em, NASCIMENTO_NA_DIRECAO[autor.nivel])
        )
        if not trilha.marco(condutor, (1, 5), f"Destino definido: {rotulo_destino}."):
            return
        inovacao.destino = tema.destino
        _dirigir(trilha, condutor, tema)
        return

    inovacao.eventos.append(Evento(None, "na_fila", autor.login, inovacao.criada_em, None))
    supervisor = rng.choice(supervisores)
    espera = (8, 22) if rng.random() < 0.12 else (1, 6)  # às vezes a fila anda devagar
    if not trilha.passo("em_avaliacao", supervisor, espera):
        return
    _conversar(rng, inovacao, supervisor, trilha.agora)

    if rng.random() < 0.15:
        # O supervisor sugere arquivar; a sugestão sobe, nunca se consuma ali.
        justificativa = rng.choice(cat.JUSTIFICATIVAS_ARQUIVAMENTO)
        if not trilha.passo("arquivo_morto_sugerido", supervisor, (2, 8), justificativa):
            return
        if rng.random() < 0.65:
            concorda = "A diretoria concorda com o arquivamento; segue para a presidência."
            if not trilha.passo("arquivo_morto_proposto", DIRETOR, (2, 8), concorda):
                return
            if rng.random() < 0.80:
                trilha.passo(
                    "arquivo_morto", PRESIDENTE, (2, 10), "Arquivamento confirmado pela presidência."
                )
                return
            if _agendar_brainstorm(trilha, PRESIDENTE, (2, 10), recusando=True):
                _decidir_brainstorm(trilha, DIRETOR, tema)
            return
        if _agendar_brainstorm(trilha, DIRETOR, (2, 8), recusando=True):
            _decidir_brainstorm(trilha, DIRETOR, tema)
        return

    if not trilha.marco(supervisor, (1, 5), f"Destino definido: {rotulo_destino}."):
        return
    inovacao.destino = tema.destino
    if not trilha.passo("com_diretor", supervisor, (1, 4), "Avaliação do supervisor concluída."):
        return
    _dirigir(trilha, DIRETOR, tema)


def _criar_inovacao(
    rng: random.Random, autor: Pessoa, departamento: str, criada_em: datetime
) -> tuple[InovacaoSintetica, cat.Tema]:
    pesos = [1.4 if tema.custo is None else 1.0 for tema in cat.TEMAS]
    tema = rng.choices(cat.TEMAS, weights=pesos)[0]
    alvo = rng.choice(cat.ALVOS[departamento])
    horas = rng.choice((1, 2, 2, 3, 4, 6))
    periodo = rng.choice(("dia", "semana", "semana"))
    custo_valor = None
    if tema.custo is not None:
        custo_valor = round(rng.randint(*tema.custo) / 500) * 500
    prazo = criada_em.date() + timedelta(days=rng.randint(30, 180)) if rng.random() < 0.6 else None
    inovacao = InovacaoSintetica(
        titulo=tema.titulo.format(alvo=alvo),
        descricao=tema.descricao.format(alvo=alvo),
        objetivo=tema.objetivo.format(alvo=alvo),
        beneficios=tema.beneficios.format(horas=horas, periodo=periodo),
        desafios=tema.desafios,
        ferramentas=tema.ferramentas,
        indicador=tema.indicador.format(alvo=alvo),
        prazo_desejado=prazo,
        custo_tipo=tema.custo_tipo,
        custo_valor=custo_valor,
        autor=autor.login,
        departamento=departamento,
        criada_em=criada_em,
    )
    return inovacao, tema


def gerar(semente: int = SEMENTE) -> Base:
    """A base sintética inteira, determinística para uma dada semente."""
    rng = random.Random(semente)
    pessoas = gerar_pessoas(rng)
    departamentos = list(cat.COLABORADORES_POR_DEPARTAMENTO)

    colaboradores = {
        dep: [p for p in pessoas if p.nivel == 1 and dep in p.departamentos] for dep in departamentos
    }
    supervisores = {
        dep: [p for p in pessoas if p.nivel == 2 and dep in p.departamentos] for dep in departamentos
    }
    diretor = next(p for p in pessoas if p.login == DIRETOR)
    # Nem todo mundo participa: cerca de 60% propõem algo, e poucos propõem muito.
    engajamento = {
        dep: [rng.paretovariate(1.6) if rng.random() < 0.6 else 0.0 for _ in colaboradores[dep]]
        for dep in departamentos
    }
    peso_departamento = [cat.COLABORADORES_POR_DEPARTAMENTO[dep] * PROPENSAO[dep] for dep in departamentos]

    inovacoes: list[InovacaoSintetica] = []
    for ano in sorted(MEDIA_MENSAL):
        for mes in range(1, 13):
            dias = _dias_uteis_do_mes(ano, mes)
            if not dias:
                continue
            proporcao_do_mes = len(dias) / 21  # mês cortado (novembro de 2026) rende menos
            quantidade = round(
                MEDIA_MENSAL[ano] * SAZONALIDADE[mes] * min(proporcao_do_mes, 1.0) * rng.uniform(0.85, 1.15)
            )
            for _ in range(quantidade):
                departamento = rng.choices(departamentos, weights=peso_departamento)[0]
                sorteio = rng.random()
                if sorteio < 0.01:
                    autor = diretor
                elif sorteio < 0.06:
                    autor = rng.choice(supervisores[departamento])
                else:
                    autor = rng.choices(colaboradores[departamento], weights=engajamento[departamento])[0]
                criada_em = datetime.combine(rng.choice(dias), time(rng.randint(8, 17), rng.randint(0, 59)))
                inovacao, tema = _criar_inovacao(rng, autor, departamento, criada_em)
                _simular_ciclo(rng, inovacao, autor, [s.login for s in supervisores[departamento]], tema)
                inovacoes.append(inovacao)

    inovacoes.sort(key=lambda item: item.criada_em)
    return Base(pessoas=pessoas, inovacoes=inovacoes)
