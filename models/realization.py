from typing import List


class UHEResult:
    def __init__(self,
                 finalVolume: float,
                 turbinatedVolume: float,
                 spilledVolume: float,
                 waterValue: float):
        self.finalVolume = finalVolume
        self.turbinatedVolume = turbinatedVolume
        self.spilledVolume = spilledVolume
        self.waterValue = waterValue

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {}\n".format(k, v)
        return to_str


class UTEResult:
    def __init__(self,
                 generated: float):
        self.generated = generated


class Realization:
    def __init__(self,
                 totalCost: float,
                 deficit: float,
                 uhes: List[List[List[UHEResult]]],
                 utes: List[List[List[UTEResult]]]):
        self.totalCost = totalCost
        self.deficit = deficit
        self.uhes = uhes
        self.utes = utes

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {}\n".format(k, v)
        return to_str
