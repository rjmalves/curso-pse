from plunico.modelos.no import No

from typing import Dict, List


class Cenario:
    """
    Descreve um possível cenário de operação considerado
    dentro da árvore de possibilidades.
    """
    def __init__(self, nos: List[No]):
        self.n_uhes = len(nos[0].volumes_finais)
        self.n_utes = len(nos[0].geracao_termica)
        self.afluencias = self.organiza_afluencias(nos)
        print("AFLUENCIAS")
        print(self.afluencias)
        self.volumes_finais = self.organiza_vol_finais(nos)
        print("VOLUMES FINAIS")
        print(self.volumes_finais)
        self.volumes_turbinados = self.organiza_vol_turbin(nos)
        print("VOLUMES TURBINADOS")
        print(self.volumes_turbinados)
        self.volumes_vertidos = self.organiza_vol_vertid(nos)
        print("VOLUMES VERTIDOS")
        print(self.volumes_vertidos)
        self.custo_agua = self.organiza_custo_agua(nos)
        print("CUSTO AGUA")
        print(self.custo_agua)
        self.geracao_termica = self.organiza_ger_termica(nos)
        print("TERMICAS")
        print(self.geracao_termica)
        self.deficit: List[float] = [n.deficit for n in nos]
        print("DEFICIT")
        print(self.deficit)

    def organiza_afluencias(self,
                            nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai as afluências que ocorreram a partir de uma lista de nós
        que representam o cenário.
        """
        afluencias: Dict[int, List[float]] = {i: [] for i in
                                              range(self.n_uhes)}
        for n in nos:
            for i in range(self.n_uhes):
                afluencias[i].append(n.afluencias[i])
        return afluencias

    def organiza_vol_finais(self,
                            nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai os volumes finais a partir de uma lista de nós
        que representam o cenário.
        """
        vol_finais: Dict[int, List[float]] = {i: [] for i in
                                              range(self.n_uhes)}
        for n in nos:
            for i in range(self.n_uhes):
                vol_finais[i].append(n.volumes_finais[i])
        return vol_finais

    def organiza_vol_turbin(self,
                            nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai os volumes turbinados a partir de uma lista de nós
        que representam o cenário.
        """
        vol_turbin: Dict[int, List[float]] = {i: [] for i in
                                              range(self.n_uhes)}
        for n in nos:
            for i in range(self.n_uhes):
                vol_turbin[i].append(n.volumes_turbinados[i])
        return vol_turbin

    def organiza_vol_vertid(self,
                            nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai os volumes vertidos a partir de uma lista de nós
        que representam o cenário.
        """
        vol_vertid: Dict[int, List[float]] = {i: [] for i in
                                              range(self.n_uhes)}
        for n in nos:
            for i in range(self.n_uhes):
                vol_vertid[i].append(n.volumes_vertidos[i])
        return vol_vertid

    def organiza_custo_agua(self,
                            nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai os custos da água a partir de uma lista de nós
        que representam o cenário.
        """
        custo_agua: Dict[int, List[float]] = {i: [] for i in
                                              range(self.n_uhes)}
        for n in nos:
            for i in range(self.n_uhes):
                custo_agua[i].append(n.custo_agua[i])
        return custo_agua

    def organiza_ger_termica(self,
                             nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai as gerações de térmicas a partir de uma lista de nós
        que representam o cenário.
        """
        ger_termica: Dict[int, List[float]] = {i: [] for i in
                                               range(self.n_utes)}
        for n in nos:
            for i in range(self.n_utes):
                ger_termica[i].append(n.geracao_termica[i])
        return ger_termica
