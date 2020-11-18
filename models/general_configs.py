from typing import List


class GeneralConfigs:
    def __init__(self,
                 deficit_cost: float,
                 loads: List[float],
                 stage_count: int,
                 scenario_count: int,
                 post_study: int):
        self.deficit_cost = deficit_cost
        self.loads = loads
        self.stage_count = stage_count
        self.scenario_count = scenario_count
        self.post_study = post_study

    @classmethod
    def from_json(cls, json_dict: dict):
        return cls(json_dict["deficitCost"],
                   json_dict["loads"],
                   json_dict["stageCount"],
                   json_dict["scenarioCount"],
                   json_dict["postStudy"])

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {}\n".format(k, v)
        return to_str
