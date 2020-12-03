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

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {} - ".format(k, v)
        return to_str

    def __eq__(self, obj):
        if not isinstance(obj, CorteBenders):
            return False
        return (self.custo_agua == obj.custo_agua
                and self.offset == obj.offset)
