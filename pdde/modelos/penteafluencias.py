from utils.leituraentrada import LeituraEntrada
from pdde.modelos.no import No

from random import choice, sample
from typing import List


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
        self.vis = [uh.vol_inicial for uh in e.uhes]
        self.afluencias = e.afluencias
        self.indices_nos_pente: List[List[int]] = []
        self.indices_sequencias: List[List[int]] = []
        self.dentes: List[List[No]] = []

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
        for s in range(self.n_sequencias):
            seq: List[int] = []
            for indices in self.indices_nos_pente:
                seq.append(choice(indices))
            self.indices_sequencias.append(seq)
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
        # Força os volumes iniciais nos nós do primeiro período
        for dente in self.dentes:
            dente[0].volumes_iniciais = self.vis

    def afluencias_abertura(self,
                            periodo: int,
                            abertura: int) -> List[float]:
        """
        Retorna as afluências de uma dada abertura em um período.
        """
        afls: List[float] = []
        for i in range(1, self.n_uhes + 1):
            afls.append(self.afluencias[i][periodo][abertura])
        return afls
