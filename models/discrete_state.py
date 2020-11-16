from typing import List
import numpy as np  # type: ignore
from models.realization import Realization, UHEResult, UTEResult


class DiscreteState:
    def __init__(self,
                 stage: int,
                 volumes: List[float],
                 affluences: List[float]):
        self.stage = stage
        self.volumes = volumes
        self.affluences = affluences

    def __str__(self):
        to_str = "Stage: " + str(self.stage) + "\n"
        to_str += "Volumes: " + str(self.volumes) + "\n"
        to_str += "Affluences: " + str(self.affluences) + "\n"
        return to_str


class StateResult:
    def __init__(self,
                 state: DiscreteState,
                 possible_next_states: List[DiscreteState],
                 realizations: List[Realization]):
        self.state = state
        # If it is the end-of-world case
        if len(realizations) == 0:
            self.init_eow()
        else:
            # Choose next state
            best_cost = np.inf
            real = 0
            for i, r in enumerate(realizations):
                if r.totalCost < best_cost:
                    best_cost = r.totalCost
                    real = i
            self.nextState = possible_next_states[real]
            self.totalCost = best_cost
            self.cmo = realizations[real].cmo
            self.deficit = realizations[real].deficit
            self.uhes = realizations[real].uhes
            self.utes = realizations[real].utes

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {}\n".format(k, v)
        return to_str

    def init_eow(self):
        uhe_res = [UHEResult(0, 0, 0)] * 10
        ute_res = [UTEResult(0)] * 10
        r = Realization(0, 0, 0, uhe_res, ute_res)
        self.nextState = DiscreteState(self.state.stage + 1,
                                       [0] * 10,
                                       [0] * 10)
        self.totalCost = 0
        self.cmo = 0
        self.deficit = 0
        self.uhes = r.uhes
        self.utes = r.utes
