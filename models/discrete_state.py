from typing import List
from models.scenario import Scenario, ScenarioResult


class DiscreteState:
    def __init__(self,
                 stage: int,
                 volumes: List[float],
                 affluences: List[List[float]]):
        self.stage = stage
        self.volumes = volumes
        self.scenarios: List[Scenario] = []
        for a in affluences:
            self.scenarios.append(Scenario(a))

    def __str__(self):
        to_str = "Stage: " + str(self.stage) + "\n"
        to_str += "Volumes: " + str(self.volumes) + "\n"
        to_str += "Scenarios: \n"
        for s in self.scenarios:
            to_str += str(s) + "\n"
        return to_str


class StateResult:
    def __init__(self,
                 state: DiscreteState,
                 scen_results: List[ScenarioResult]):

        self.state = state
        scenarioCount = len(scen_results)
        # Average total cost
        cost = 0.
        for s in scen_results:
            cost += s.totalCost
        self.averageCost = cost / scenarioCount
        # Average water values
        uheCount = len(scen_results[0].uhes)
        waterValues: List[float] = [0. for i in range(uheCount)]
        for s in scen_results:
            for i in range(uheCount):
                waterValues[i] -= s.uhes[i].waterValue
        for i in range(uheCount):
            waterValues[i] /= scenarioCount
        self.averageWaterValues = waterValues
        # Cost offset
        self.offset = self.averageCost
        for i in range(uheCount):
            self.offset -= self.averageWaterValues[i] * self.state.volumes[i]

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {}\n".format(k, v)
        return to_str
