from typing import List


class CorteBenders:
    """
    Representação do hiperplano definido por um corte de
    Benders nos métodos de PDDx.
    """
    def __init__(self,
                 coef_angular: List[float],
                 termo_indep: float,
                 fobj: float):
        self.coef_angular = coef_angular
        self.termo_indep = termo_indep
        self.fobj = fobj

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {} - ".format(k, v)
        return to_str

    def __hash__(self):
        custos = tuple(self.coef_angular)
        return hash((custos, self.termo_indep))

    def __eq__(self, obj):
        if not isinstance(obj, CorteBenders):
            return False
        tol = 1e-18
        for c1, c2 in zip(self.coef_angular, obj.coef_angular):
            if abs(c1 - c2) > tol:
                return False
        termo_indep_igual = abs(self.termo_indep - obj.termo_indep) < tol
        return termo_indep_igual

    def __lt__(self, obj):
        if not isinstance(obj, CorteBenders):
            return False
        return self.fobj < obj.fobj
