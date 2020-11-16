from models.uhe import UHE
from models.ute import UTE
from models.general_configs import GeneralConfigs
from models.discrete_state import DiscreteState
from models.discrete_state import StateResult
from models.realization import UHEResult
from models.realization import UTEResult
from models.realization import Realization
from itertools import product
import numpy as np  # type: ignore
from typing import List, Dict
import matplotlib.pyplot as plt  # type: ignore
from matplotlib import cm  # type: ignore
from cvxopt.modeling import variable, op, solvers, _function  # type: ignore
solvers.options['glpk'] = {'msg_lev': 'GLP_MSG_OFF'}


class System:
    def __init__(self,
                 configs: GeneralConfigs,
                 uhes: List[UHE],
                 utes: List[UTE]):
        self.configs = configs
        self.uhes = uhes
        self.utes = utes

    @classmethod
    def from_json(cls, json_dict: dict):
        configs = GeneralConfigs.from_json(json_dict["generalConfigs"])
        uhes: List[UHE] = []
        for d in json_dict["UHES"]:
            uhes.append(UHE.from_json(d))
        utes: List[UTE] = []
        for d in json_dict["UTES"]:
            utes.append(UTE.from_json(d))
        return cls(configs, uhes, utes)

    def generateStates(self, scenario: int):
        step = 100 / (self.configs.discretization_count - 1)
        uhe_volumes = np.arange(0, 100 + step, step)
        discs = list(product(uhe_volumes, repeat=len(self.uhes)))
        self.states: List[DiscreteState] = []
        for s in np.arange(self.configs.stage_count, 0, -1):
            for d in discs:
                vis: List[float] = []
                for i, u in enumerate(self.uhes):
                    vi = (u.min_volume +
                          (u.max_volume - u.min_volume) * d[i] / 100)
                    vis.append(vi)
                afls: List[float] = []
                for i, u in enumerate(self.uhes):
                    afl = u.affluents[s-1][scenario]
                    afls.append(afl)
                self.states.append(DiscreteState(s, vis, afls))

    def optConfig(self,
                  state: DiscreteState,
                  future_state: DiscreteState):

        # Variables
        self.vt = variable(len(self.uhes), "Volume turbinado na usina")
        self.vv = variable(len(self.uhes), "Volume vertido na usina")
        self.gt = variable(len(self.utes), "Geração na usina térmica")
        self.deficit = variable(1, "Déficit de energia no sistema")

        # Obj function
        self.obj_f: _function = 0
        for i, u in enumerate(self.utes):
            self.obj_f += u.cost * self.gt[i]

        self.obj_f += self.configs.deficit_cost * self.deficit[0]

        for i in range(len(self.uhes)):
            self.obj_f += 0.01 * self.vv[i]

        # Constraints
        self.cons = []

        for i, uh in enumerate(self.uhes):
            vi = float(state.volumes[i])
            afl = float(state.affluences[i])
            vf = float(future_state.volumes[i])
            self.cons.append(
                vf == vi + afl - self.vt[i] - self.vv[i])

        balance = 0
        for i, uh in enumerate(self.uhes):
            balance += uh.productivity * self.vt[i]
        for i, ut in enumerate(self.utes):
            balance += self.gt[i]
        balance += self.deficit[0]
        self.cons.append(balance == self.configs.loads[state.stage-1])

        for i, uh in enumerate(self.uhes):
            self.cons.append(self.vt[i] >= 0)
            self.cons.append(self.vt[i] <= uh.swallowing)
            self.cons.append(self.vv[i] >= 0)

        for i, ut in enumerate(self.utes):
            self.cons.append(self.gt[i] >= 0)
            self.cons.append(self.gt[i] <= ut.capacity)

        self.cons.append(self.deficit[0] >= 0)

    def optSolve(self, log: bool = True) -> Realization:
        self.prob = op(self.obj_f, self.cons)
        self.prob.solve('dense', 'glpk')
        # The results
        if self.prob.status == 'optimal':
            uhe_res: List[UHEResult] = []
            for i, u in enumerate(self.uhes):
                r = UHEResult(self.vt[i].value()[0],
                              self.vv[i].value()[0],
                              self.cons[i].multiplier.value[0])
                uhe_res.append(r)
            ute_res: List[UTEResult] = []
            for i, u in enumerate(self.uhes):
                ute_res.append(UTEResult(self.gt[i].value()[0]))
            res = Realization(self.obj_f.value()[0],
                              self.cons[len(self.uhes)].multiplier.value[0],
                              self.deficit[0].value()[0],
                              uhe_res,
                              ute_res)
        else:
            res = Realization(np.inf,
                              np.inf,
                              0,
                              [],
                              [])

        if (not log) or self.prob.status != 'optimal':
            return res
        # Report
        print("Custo total: ", self.obj_f.value())
        for i, uh in enumerate(self.uhes):
            print(self.vt.name, i, "é", self.vt[i].value()[0], "hm3")
            print(self.vv.name, i, "é", self.vv[i].value()[0], "hm3")

        for i, ut in enumerate(self.utes):
            print(self.gt.name, i, "é", self.gt[i].value()[0], "MWmed")

        print(self.deficit.name, "é", self.deficit[0].value()[0], "MWmed")

        for i, u in enumerate(self.uhes):
            print("O valor da água na usina", i, "é",
                  self.cons[i].multiplier.value[0])

        print("O Custo Marginal de Operação é",
              self.cons[len(self.uhes)].multiplier.value[0])
        print("---------------- X ---------------")
        return res

    def dispatch(self):
        state_results: Dict[int, List[StateResult]] = {}
        # Virtual end-of-world state
        eow_state = DiscreteState(self.configs.stage_count + 1,
                                  [0] * 10,
                                  [0] * 10)
        # Backward loop
        for i, state in enumerate(self.states):
            results: List[Realization] = []
            future_states: List[DiscreteState] = []
            for j, s in enumerate(self.states):
                if s.stage == state.stage + 1:
                    future_states.append(s)
            if len(future_states) == 0:
                future_states.append(eow_state)
            for s in future_states:
                self.optConfig(state, s)
                results.append(self.optSolve(False))
            state_res = StateResult(state, future_states, results)
            if state.stage not in state_results:
                state_results[state.stage] = []
            state_results[state.stage].append(state_res)

        # Plotting
        if len(self.uhes) == 1:
            for i, s in state_results.items():
                plt.figure()
                plt.title("Função de Custo Futuro - Estágio {}".format(i))
                plt.xlabel("Volume Inicial (hm^3)")
                plt.ylabel("Custo Total ($)")
                costs = []
                vols = []
                for r in s:
                    costs.append(r.totalCost)
                    vols.append(r.state.volumes[0])
                plt.plot(vols, costs, marker='o')
                plt.savefig('figures/custo_est{}.png'.format(i))
        elif len(self.uhes) == 2:
            uhe0_vol_set = set()
            uhe1_vol_set = set()
            for state in self.states:
                uhe0_vol_set.add(state.volumes[0])
                uhe1_vol_set.add(state.volumes[1])
            uhe0_vols = sorted(list(uhe0_vol_set))
            uhe1_vols = sorted(list(uhe1_vol_set))
            uhe0_mesh, uhe1_mesh = np.meshgrid(uhe0_vols, uhe1_vols)
            for i, s in state_results.items():
                fig = plt.figure()
                ax = fig.gca(projection='3d')
                ax.set_title("Função de Custo Futuro - Estágio {}".format(i))
                ax.set_xlabel("Volume Inicial UHE 1 (hm^3)")
                ax.set_ylabel("Volume Inicial UHE 2 (hm^3)")
                ax.set_zlabel("FCF ($)")
                costs = np.zeros((self.configs.discretization_count,
                                  self.configs.discretization_count))
                for r in s:
                    uhe0_v = r.state.volumes[0]
                    uhe1_v = r.state.volumes[1]
                    for lin, v0 in enumerate(uhe0_vols):
                        for col, v1 in enumerate(uhe1_vols):
                            if v0 == uhe0_v and v1 == uhe1_v:
                                costs[lin][col] = r.averageCost
                ax.plot_surface(uhe0_mesh,
                                uhe1_mesh,
                                costs,
                                cmap=cm.coolwarm)
                plt.savefig('figures/custo_est{}.png'.format(i))
