from typing import List


class UHEResult:
    def __init__(self,
                 turbinatedVolume: float,
                 spilledVolume: float,
                 waterValue: float):
        self.turbinatedVolume = turbinatedVolume
        self.spilledVolume = spilledVolume
        self.waterValue = waterValue


class UTEResult:
    def __init__(self,
                 generated: float):
        self.generated = generated


class Realization:
    def __init__(self,
                 totalCost: float,
                 cmo: float,
                 deficit: float,
                 uhes: List[UHEResult],
                 utes: List[UTEResult]):
        self.totalCost = totalCost
        self.cmo = cmo
        self.deficit = deficit
        self.uhes = uhes
        self.utes = utes

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {}\n".format(k, v)
        return to_str
