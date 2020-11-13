from typing import List


class GeneralData:
    def __init__(self,
                 deficitCost: float,
                 loads: List[float],
                 discretizationCount: int,
                 stageCount: int,
                 scenarioCount: int):
        self.deficitCost = deficitCost
        self.loads = loads
        self.discretizationCount = discretizationCount
        self.stageCount = stageCount
        self.scenarioCount = scenarioCount
