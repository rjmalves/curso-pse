from utils.leituraentrada import LeituraEntrada
from modelos.no import No

from typing import List
from itertools import product


class ArvoreAfluencias:
    """
    Árvore organizada das afluências que definem os cenários
    existentes em um problema de PDDD a ser resolvido.
    """
    def __init__(self, e: LeituraEntrada):
        self.n_periodos = e.cfg.n_periodos
        self.aberturas_periodo = e.cfg.aberturas_periodo
        self.n_pos_estudo = e.cfg.n_pos_estudo
        self.n_uhes = e.cfg.n_uhes
        self.vis = [uh.vol_inicial for uh in e.uhes]
        self.afluencias = e.afluencias
        self.nos_por_periodo: List[int] = []
        self.arvore: List[List[No]] = []

    def monta_arvore_afluencias(self):
        """
        Monta uma árvore de afluências a partir dos dados lidos
        do arquivo de configuração. A árvore é uma lista composta,
        onde acessar o índice [i][j][k] significa:

        i: ID da UHE

        j: ramo da árvore da UHE i

        k: nó do ramo j
        """
        na = self.aberturas_periodo
        # Limite as afluências de cada UHE para o número de aberturas
        for i in range(1, self.n_uhes + 1):
            # O primeiro período tem apenas uma possível afluência
            self.afluencias[i][0] = [self.afluencias[i][0][0]]
            for e in range(1, self.n_periodos):
                self.afluencias[i][e] = self.afluencias[i][e][:na]

        # Para cada período de estudo, lista as combinações de afluências
        combs_periodo: List[List[float]] = []
        for p in range(self.n_periodos):
            # Varre as afluências de cada UHE
            afls_periodo: List[float] = []
            for i in range(1, self.n_uhes + 1):
                afls_periodo.append(self.afluencias[i][p])
            # Faz o produto para extrair as combinações
            combinacoes = product(*[a for a in afls_periodo])
            combs_periodo.append([list(c) for c in combinacoes])
        # Constroi a árvore a partir das combinações de cada período
        # O primeiro período tem apenas 1 nó:
        l_no: List[No] = [No(combs_periodo[0][0])]
        self.arvore.append(l_no)
        # Cada período seguinte multiplica o número de nós do período
        # anterior pelo número de combinações do próprio
        for p in range(1, self.n_periodos):
            nos_periodo: List[No] = []
            for nos_periodo_anterior in range(len(self.arvore[p - 1])):
                for comb_periodo in combs_periodo[p]:
                    nos_periodo.append(No(comb_periodo))
            self.arvore.append(nos_periodo)
        # Faz a contagem de nós por período
        for a in self.arvore:
            self.nos_por_periodo.append(len(a))
        # Força os volumes iniciais do nó do primeiro período
        self.arvore[0][0].volumes_iniciais = self.vis

    def indice_no_anterior(self, periodo: int, indice_no: int) -> int:
        """
        Retorna o índice do nó do período anterior na árvore de afluências
        a partir de um certo nó de um período.
        """
        return int(indice_no / self.aberturas_periodo)

    def indices_proximos_nos(self, periodo: int, indice_no: int) -> List[int]:
        """
        Retorna os índices dos possíveis nós após
        """
        if periodo == self.n_periodos - 1:
            return []
        else:
            indice_inicial = self.aberturas_periodo * indice_no
            indice_final = indice_inicial + self.aberturas_periodo
            return list(range(indice_inicial, indice_final))
