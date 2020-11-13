from typing import List


class Scenario:
    def __init__(self, affluences: List[float]):
        self.affluences = affluences

    def __str__(self):
        return "" + str(self.affluences)


class ScenarioUHEResult:
    def __init__(self,
                 finalVolume: float,
                 turbinatedVolume: float,
                 spilledVolume: float,
                 waterValue: float):
        self.finalVolume = finalVolume
        self.turbinatedVolume = turbinatedVolume
        self.spilledVolume = spilledVolume
        self.waterValue = waterValue


class ScenarioUTEResult:
    def __init__(self,
                 generated: float):
        self.generated = generated


class ScenarioResult:
    def __init__(self,
                 totalCost: float,
                 cmo: float,
                 deficit: float,
                 futureCost: float,
                 uhes: List[ScenarioUHEResult],
                 utes: List[ScenarioUTEResult]):
        self.totalCost = totalCost
        self.cmo = cmo
        self.deficit = deficit
        self.uhes = uhes
        self.utes = utes
