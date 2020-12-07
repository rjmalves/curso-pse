from typing import List


class No:
    """
    Representação de um nó na árvore de afluências.
    """
    def __init__(self, afluencias: List[float]):
        # Uma lista onde o ID da UHE é usada como índice
        # para obter a respectiva influência
        self.afluencias = afluencias
        self.volumes_finais: List[float] = []
        self.volumes_turbinados: List[float] = []
        self.volumes_vertidos: List[float] = []
        self.custo_agua: List[float] = []
        self.geracao_termica: List[float] = []
        self.deficit = 0.0
        self.cmo = 0.0

    def preenche_resultados(self,
                            volumes_finais: List[float],
                            volumes_turbinados: List[float],
                            volumes_vertidos: List[float],
                            custo_agua: List[float],
                            geracao_termica: List[float],
                            deficit: float,
                            cmo: float):
        """
        Adiciona ao nó os valores das variáveis após a solução
        do PL.
        """
        # Listas onde o índice é obtido através do ID da respectiva
        # UHE ou UTE
        self.volumes_finais = volumes_finais
        self.volumes_turbinados = volumes_turbinados
        self.volumes_vertidos = volumes_vertidos
        self.custo_agua = custo_agua
        self.geracao_termica = geracao_termica
        self.deficit = deficit
        self.cmo = cmo
