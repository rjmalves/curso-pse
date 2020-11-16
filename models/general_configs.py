from typing import List


class GeneralConfigs:
    def __init__(self,
                 deficit_cost: float,
                 loads: List[float],
                 discretization_count: int,
                 stage_count: int,
                 scenario_count: int):
        self.deficit_cost = deficit_cost
        self.loads = loads
        self.discretization_count = discretization_count
        self.stage_count = stage_count
        self.scenario_count = scenario_count

    @classmethod
    def from_json(cls, json_dict: dict):
        return cls(json_dict["deficitCost"],
                   json_dict["loads"],
                   json_dict["discretizationCount"],
                   json_dict["stageCount"],
                   json_dict["scenarioCount"])
