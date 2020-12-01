from typing import List


class No:
    """
    Representação de um nó na árvore de afluências.
    """
    def __init__(self, afluencias: List[float]):
        self.afluencias = afluencias
