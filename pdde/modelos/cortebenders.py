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
        tol = 1e-15
        for c1, c2 in zip(self.custo_agua, obj.custo_agua):
            if abs(c1 - c2) > tol:
                return False
        offset_igual = abs(self.offset - obj.offset) < tol
        return offset_igual

    def __lt__(self, obj):
        if not isinstance(obj, CorteBenders):
            return False
        return self.offset < obj.offset
