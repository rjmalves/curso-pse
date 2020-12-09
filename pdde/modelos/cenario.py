from pdde.modelos.no import No

from typing import Dict, List
import numpy as np  # type: ignore


class Cenario:
    """
    Descreve um cenário de operação considerado
    dentro da árvore de possibilidades.
    """
    def __init__(self,
                 n_uhes: int,
                 n_utes: int,
                 afluencias: Dict[int, List[float]],
                 volumes_finais: Dict[int, List[float]],
                 volumes_turbinados: Dict[int, List[float]],
                 volumes_vertidos: Dict[int, List[float]],
                 custo_agua: Dict[int, List[float]],
                 geracao_termica: Dict[int, List[float]],
                 deficit: List[float],
                 cmo: List[float],
                 alpha: List[float],
                 fobj: List[float]):

        self.n_uhes = n_uhes
        self.n_utes = n_utes
        self.afluencias = afluencias
        self.volumes_finais = volumes_finais
        self.volumes_turbinados = volumes_turbinados
        self.volumes_vertidos = volumes_vertidos
        self.custo_agua = custo_agua
        self.geracao_termica = geracao_termica
        self.deficit: List[float] = deficit
        self.cmo: List[float] = cmo
        self.alpha: List[float] = alpha
        self.fobj = fobj
        self.ci = [f - a for f, a in zip(fobj, alpha)]

    @classmethod
    def cenario_dos_nos(cls, nos: List[No]):
        """
        Retorna um objeto cenário a partir de uma lista de cenários,
        calculando os valores médios para cada parâmetro.
        """
        n_uhes = len(nos[0].volumes_finais)
        n_utes = len(nos[0].geracao_termica)
        afluencias = Cenario.organiza_afluencias(nos)
        volumes_finais = Cenario.organiza_vol_finais(nos)
        volumes_turbinados = Cenario.organiza_vol_turbin(nos)
        volumes_vertidos = Cenario.organiza_vol_vertid(nos)
        custo_agua = Cenario.organiza_custo_agua(nos)
        geracao_termica = Cenario.organiza_ger_termica(nos)
        deficit: List[float] = [n.deficit for n in nos]
        cmo: List[float] = [n.cmo for n in nos]
        alpha: List[float] = [n.custo_futuro for n in nos]
        fobj: List[float] = [n.custo_total for n in nos]

        return cls(n_uhes,
                   n_utes,
                   afluencias,
                   volumes_finais,
                   volumes_turbinados,
                   volumes_vertidos,
                   custo_agua,
                   geracao_termica,
                   deficit,
                   cmo,
                   alpha,
                   fobj)

    @classmethod
    def cenario_medio(cls, cens):
        """
        Calcula um cenário médio a partir de uma lista de cenários.
        """
        cenarios: List[Cenario] = cens
        n_uhes = cenarios[0].n_uhes
        n_utes = cenarios[0].n_utes
        afluencias_medias: Dict[int, List[float]] = {i: [] for i in
                                                     range(n_uhes)}
        vol_finais_medios: Dict[int, List[float]] = {i: [] for i in
                                                     range(n_uhes)}
        vol_turbin_medios: Dict[int, List[float]] = {i: [] for i in
                                                     range(n_uhes)}
        vol_vertid_medios: Dict[int, List[float]] = {i: [] for i in
                                                     range(n_uhes)}
        custo_agua_medios: Dict[int, List[float]] = {i: [] for i in
                                                     range(n_uhes)}
        gera_termi_medios: Dict[int, List[float]] = {i: [] for i in
                                                     range(n_utes)}
        n_cenarios = len(cenarios)
        # Calcula os atributos médios das UHEs
        for i in range(n_uhes):
            afl_cen = [np.array(c.afluencias[i]) for c in cenarios]
            vf_cen = [np.array(c.volumes_finais[i]) for c in cenarios]
            vt_cen = [np.array(c.volumes_turbinados[i]) for c in cenarios]
            vv_cen = [np.array(c.volumes_vertidos[i]) for c in cenarios]
            cma_cen = [np.array(c.custo_agua[i]) for c in cenarios]
            afl_med = sum(afl_cen) / n_cenarios
            vf_med = sum(vf_cen) / n_cenarios
            vt_med = sum(vt_cen) / n_cenarios
            vv_med = sum(vv_cen) / n_cenarios
            cma_med = sum(cma_cen) / n_cenarios
            afluencias_medias[i] = list(afl_med)
            vol_finais_medios[i] = list(vf_med)
            vol_turbin_medios[i] = list(vt_med)
            vol_vertid_medios[i] = list(vv_med)
            custo_agua_medios[i] = list(cma_med)
        # Calcula os atributos médios das UTEs
        for i in range(n_utes):
            ger_cen = [np.array(c.geracao_termica[i]) for c in cenarios]
            ger_med = sum(ger_cen) / n_cenarios
            gera_termi_medios[i] = list(ger_med)
        # Calcula o deficit, cmo, fobj e fcf médios
        deficit_cen = [np.array(c.deficit) for c in cenarios]
        cmo_cen = [np.array(c.cmo) for c in cenarios]
        alpha_cen = [np.array(c.alpha) for c in cenarios]
        fobj_cen = [np.array(c.fobj) for c in cenarios]
        deficit_medio = list(sum(deficit_cen) / n_cenarios)
        cmo_medio = list(sum(cmo_cen) / n_cenarios)
        alpha_medio = list(sum(alpha_cen) / n_cenarios)
        fobj_medio = list(sum(fobj_cen) / n_cenarios)
        # Constroi o cenário e retorna
        return cls(n_uhes,
                   n_utes,
                   afluencias_medias,
                   vol_finais_medios,
                   vol_turbin_medios,
                   vol_vertid_medios,
                   custo_agua_medios,
                   gera_termi_medios,
                   deficit_medio,
                   cmo_medio,
                   alpha_medio,
                   fobj_medio)

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {} - ".format(k, v)
        return to_str

    @classmethod
    def organiza_afluencias(cls,
                            nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai as afluências que ocorreram a partir de uma lista de nós
        que representam o cenário.
        """
        n_uhes = len(nos[0].volumes_finais)
        afluencias: Dict[int, List[float]] = {i: [] for i in
                                              range(n_uhes)}
        for n in nos:
            for i in range(n_uhes):
                afluencias[i].append(n.afluencias[i])
        return afluencias

    @classmethod
    def organiza_vol_finais(cls,
                            nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai os volumes finais a partir de uma lista de nós
        que representam o cenário.
        """
        n_uhes = len(nos[0].volumes_finais)
        vol_finais: Dict[int, List[float]] = {i: [] for i in
                                              range(n_uhes)}
        for n in nos:
            for i in range(n_uhes):
                vol_finais[i].append(n.volumes_finais[i])
        return vol_finais

    @classmethod
    def organiza_vol_turbin(cls,
                            nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai os volumes turbinados a partir de uma lista de nós
        que representam o cenário.
        """
        n_uhes = len(nos[0].volumes_finais)
        vol_turbin: Dict[int, List[float]] = {i: [] for i in
                                              range(n_uhes)}
        for n in nos:
            for i in range(n_uhes):
                vol_turbin[i].append(n.volumes_turbinados[i])
        return vol_turbin

    @classmethod
    def organiza_vol_vertid(cls,
                            nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai os volumes vertidos a partir de uma lista de nós
        que representam o cenário.
        """
        n_uhes = len(nos[0].volumes_finais)
        vol_vertid: Dict[int, List[float]] = {i: [] for i in
                                              range(n_uhes)}
        for n in nos:
            for i in range(n_uhes):
                vol_vertid[i].append(n.volumes_vertidos[i])
        return vol_vertid

    @classmethod
    def organiza_custo_agua(cls,
                            nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai os custos da água a partir de uma lista de nós
        que representam o cenário.
        """
        n_uhes = len(nos[0].volumes_finais)
        custo_agua: Dict[int, List[float]] = {i: [] for i in
                                              range(n_uhes)}
        for n in nos:
            for i in range(n_uhes):
                custo_agua[i].append(n.custo_agua[i])
        return custo_agua

    @classmethod
    def organiza_ger_termica(cls,
                             nos: List[No]) -> Dict[int, List[float]]:
        """
        Extrai as gerações de térmicas a partir de uma lista de nós
        que representam o cenário.
        """
        n_utes = len(nos[0].geracao_termica)
        ger_termica: Dict[int, List[float]] = {i: [] for i in
                                               range(n_utes)}
        for n in nos:
            for i in range(n_utes):
                ger_termica[i].append(n.geracao_termica[i])
        return ger_termica

    def linhas_tabela(self) -> List[str]:
        """
        Retorna as linhas formatadas, relativas ao cenário para
        serem escritas na tabela de saída.
        """
        n_periodos = len(self.volumes_finais[0])
        linhas: List[str] = []
        for i in range(n_periodos):
            linha = " "
            ind_periodo = str(i + 1).rjust(13)
            linha += ind_periodo + " "
            for j in range(self.n_uhes):
                linha += "{:19.4f}".format(self.afluencias[j][i]) + " "
                linha += "{:19.4f}".format(self.volumes_finais[j][i]) + " "
                linha += "{:19.4f}".format(self.volumes_turbinados[j][i]) + " "
                linha += "{:19.4f}".format(self.volumes_vertidos[j][i]) + " "
                linha += "{:19.4f}".format(self.custo_agua[j][i]) + " "
            for j in range(self.n_utes):
                linha += "{:19.4f}".format(self.geracao_termica[j][i]) + " "
            linha += "{:19.4f}".format(self.deficit[i]) + " "
            linha += "{:19.4f}".format(self.cmo[i]) + " "
            linha += "{:19.4f}".format(self.ci[i]) + " "
            linha += "{:19.4f}".format(self.alpha[i]) + " "
            linha += "{:19.4f}".format(self.fobj[i]) + " "
            linha += "\n"
            linhas.append(linha)
        return linhas
