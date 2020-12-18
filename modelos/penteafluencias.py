from utils.leituraentrada import LeituraEntrada
from modelos.cenario import Cenario
from modelos.no import No

from itertools import product
from random import choice, sample, seed
from typing import List, Set, Tuple


class PenteAfluencias:
    """
    Pente organizado das afluências que definem os cenários
    existentes em um problema de PDDE a ser resolvido.
    """
    def __init__(self, e: LeituraEntrada):
        self.n_periodos = e.cfg.n_periodos
        self.aberturas_periodo = e.cfg.aberturas_periodo
        self.n_pos_estudo = e.cfg.n_pos_estudo
        self.n_sequencias = e.cfg.n_cenarios
        self.n_uhes = e.cfg.n_uhes
        self.semente = e.cfg.semente
        self.vis = [uh.vol_inicial for uh in e.uhes]
        self.afluencias = e.afluencias
        self.indices_nos_pente: List[List[int]] = []
        self.indices_sequencias: Set[Tuple[int]] = set()
        self.dentes: List[List[No]] = []
        # Fixa a semente na fornecida pelo usuário
        seed(self.semente)

    def monta_pente_afluencias(self):
        """
        Monta um pente de afluências a partir dos dados lidos
        do arquivo de configuração. O pente é um conjunto de séries
        de afluências extraídos a partir de uma árvore de possibilidades.
        """
        # 1º Sorteio: índices das afluências que irão existir em cada
        # período
        nos_por_periodo = LeituraEntrada.afluencias_por_periodo
        for p in range(self.n_periodos):
            self.indices_nos_pente.append(sample(range(nos_por_periodo),
                                          self.aberturas_periodo))
        # 2º Sorteio: sequências forward dentro das afluências escolhidas
        tentativas = 0
        while len(self.indices_sequencias) < self.n_sequencias:
            if tentativas >= 1e4:
                raise Exception("Não foi possível gerar {} cenarios"
                                .format(self.n_sequencias))
            tentativas += 1
            seq: List[int] = []
            for indices in self.indices_nos_pente:
                seq.append(choice(indices))
            self.indices_sequencias.add(tuple(seq))
        # Monta cada dente do pente de afluências baseado nos
        # índices que foram sorteados
        for seq in self.indices_sequencias:
            nos_seq: List[No] = []
            for p, indice_no in enumerate(seq):
                afls: List[float] = []
                for i in range(1, self.n_uhes + 1):
                    afls.append(self.afluencias[i][p][indice_no])
                nos_seq.append(No(afls))
            self.dentes.append(nos_seq)
        # Adiciona o período pós-estudo
        for p in range(self.n_pos_estudo):
            for d, dente in enumerate(self.dentes):
                self.dentes[d] += dente
        # Força os volumes iniciais nos nós do primeiro período
        for dente in self.dentes:
            dente[0].volumes_iniciais = self.vis

    def monta_simulacao_final(self, pente):
        """
        """
        pente_atual: PenteAfluencias = pente
        afl_periodo = LeituraEntrada.afluencias_por_periodo
        # Monta a árvore completa de cenários
        arvore_do_pente = [[0]] + [list(range(afl_periodo))
                                   for _ in range(self.n_periodos - 1)]
        combinacoes = product(*arvore_do_pente)
        self.indices_sequencias = set(combinacoes)
        # Monta todos os dentes possíveis
        for seq in self.indices_sequencias:
            nos_seq: List[No] = []
            for p, indice_no in enumerate(seq):
                afls: List[float] = []
                for i in range(1, self.n_uhes + 1):
                    afls.append(self.afluencias[i][p][indice_no])
                nos_seq.append(No(afls))
            self.dentes.append(nos_seq)
        # Força os volumes iniciais nos nós do primeiro período
        for dente in self.dentes:
            dente[0].volumes_iniciais = self.vis
        # Adiciona aos nós de cada período os cortes do pente existente
        for dente in self.dentes:
            for p in range(self.n_periodos):
                dente[p].cortes = pente_atual.dentes[0][p].cortes

    def afluencias_abertura(self,
                            periodo: int,
                            abertura: int) -> List[float]:
        """
        Retorna as afluências de uma dada abertura em um período.
        """
        afls: List[float] = []
        p = periodo % self.n_periodos
        for i in range(1, self.n_uhes + 1):
            afls.append(self.afluencias[i][p][abertura])
        return afls

    def reamostrar(self):
        """
        Para cada nó em cada período do pente, substitui a afluência
        anterior por alguma outras das possíveis de serem assumidas
        naquele mesmo período.
        """
        for dente in self.dentes:
            for p, no in enumerate(dente):
                for i in range(self.n_uhes):
                    s = choice(self.indices_nos_pente[p])
                    no.afluencias[i] = self.afluencias[i + 1][p][s]

    def organiza_cenarios(self) -> List[Cenario]:
        """
        Para cada dente do pente, monta as séries históricas de cada
        variável de interesse no estudo realizado.
        """
        return [Cenario.cenario_dos_nos(d) for d in self.dentes]
