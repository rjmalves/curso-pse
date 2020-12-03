from typing import List


class CorteBenders:
    """
    Representação do hiperplano definido por um corte de
    Benders nos métodos de PDDx.
    """
    def __init__(self,
                 custo_agua: List[float],
                 offset: float):
        self.custo_agua = custo_agua
        self.offset = offset
