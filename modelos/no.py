from modelos.cortebenders import CorteBenders

from typing import List


class No:
    """
    Representação de um nó no pente de afluências.
    """
    def __init__(self, afluencias: List[float]):
        # Uma lista onde o ID da UHE é usada como índice
        # para obter a respectiva influência
        self.afluencias = afluencias
        self.volumes_iniciais: List[float] = []
        self.volumes_turbinados: List[float] = []
        self.volumes_vertidos: List[float] = []
        self.volumes_finais: List[float] = []
        self.custo_agua: List[float] = []
        self.geracao_termica: List[float] = []
        self.deficit = 0.0
        self.cmo = 0.0
        self.custo_imediato = 0.0
        self.custo_futuro = 0.0
        self.custo_total = 0.0
        self.cortes: List[CorteBenders] = []

    def adiciona_corte(self,
                       corte: CorteBenders,
                       repetidos: bool = False):
        """
        Adiciona um novo corte de Benders à lista de cortes
        do nó.
        """
        self.cortes.append(corte)
        if not repetidos:
            self.cortes = list(set(self.cortes))

    def preenche_resultados(self,
                            volumes_finais: List[float],
                            volumes_turbinados: List[float],
                            volumes_vertidos: List[float],
                            custo_agua: List[float],
                            geracao_termica: List[float],
                            deficit: float,
                            cmo: float,
                            ci: float,
                            alpha: float,
                            func_objetivo: float):
        """
        Adiciona ao nó os valores das variáveis após a solução
        do PL.
        """
        # Listas onde o índice é obtido através do ID da respectiva
        # UHE ou UTE
        volumes_iniciais: List[float] = []
        for i in range(len(volumes_finais)):
            volumes_iniciais.append(volumes_finais[i] +
                                    volumes_turbinados[i] +
                                    volumes_vertidos[i] -
                                    self.afluencias[i])
        self.volumes_iniciais = volumes_iniciais
        self.volumes_finais = volumes_finais
        self.volumes_turbinados = volumes_turbinados
        self.volumes_vertidos = volumes_vertidos
        self.custo_agua = custo_agua
        self.geracao_termica = geracao_termica
        self.deficit = deficit
        self.cmo = cmo
        self.custo_imediato = ci
        self.custo_futuro = alpha
        self.custo_total = func_objetivo

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {} - ".format(k, v)
        return to_str

    def resumo(self) -> str:
        str_resumo = ""
        str_resumo += "vi = {:4.2f} | ".format(self.volumes_iniciais[0])
        str_resumo += "af = {:4.2f} | ".format(self.afluencias[0])
        str_resumo += "vt = {:4.2f} | ".format(self.volumes_turbinados[0])
        str_resumo += "vv = {:4.2f} | ".format(self.volumes_vertidos[0])
        str_resumo += "vf = {:4.2f} | ".format(self.volumes_finais[0])
        str_resumo += "gt1 = {:4.2f} | ".format(self.geracao_termica[0])
        str_resumo += "gt2 = {:4.2f} | ".format(self.geracao_termica[1])
        str_resumo += "def = {:4.2f} | ".format(self.deficit)
        str_resumo += "cma = {:4.2f} | ".format(self.custo_agua[0])
        str_resumo += "cmo = {:4.2f} | ".format(self.cmo)
        str_resumo += "c. futuro = {:4.2f} | ".format(self.custo_futuro)
        str_resumo += "c. total = {:4.2f} | ".format(self.custo_total)
        return str_resumo

    def linhas_tabela_cortes_individuais(self) -> List[str]:
        """
        Retorna as linhas de um relatório de cortes individuais.
        """
        linhas: List[str] = []
        n_uhes = len(self.volumes_finais)
        for corte in self.cortes:
            linha = "               "
            linha += "{:19.8f}".format(corte.termo_indep) + " "
            for i in range(n_uhes):
                linha += "{:19.8f}".format(corte.coef_angular[i]) + " "
            linha += "\n"
            linhas.append(linha)
        return linhas
