from models.uhe import UHE
from models.ute import UTE
from models.general_configs import GeneralConfigs
from models.realization import UHEResult
from models.realization import UTEResult
from models.realization import Realization
from models.benders_cut import BendersCut
import numpy as np  # type: ignore
from typing import List, Dict
import itertools
import matplotlib.pyplot as plt  # type: ignore
# from matplotlib import cm  # type: ignore
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

    def assemble_scenario_tree(self):
        br = self.configs.branch_count
        # Affluence tree for each UHE
        # tree[i][j][k] -> i = uhe, j = branch, k = node
        self.affluence_tree: List[List[List[float]]] = []
        # Overwrites the affluences with only the chosen stages and
        # branches
        for i, u in enumerate(self.uhes):
            # Cuts the latter stages
            u.affluents = u.affluents[:self.configs.stage_count]
            # Makes the first stage deterministic
            u.affluents[0] = [u.affluents[0][0]]
            # Limits the number of nodes in the each stage
            for s in range(1, self.configs.stage_count):
                u.affluents[s] = u.affluents[s][:br]
            print(u.affluents)
            t = itertools.product(*[a for a in u.affluents])
            self.affluence_tree.append([list(c) for c in t])

        self.node_counts: List[int] = []
        for i, afls in enumerate(self.uhes[0].affluents):
            if i == 0:
                self.node_counts.append(1)
            else:
                nc = self.node_counts[i - 1] * len(afls)
                self.node_counts.append(nc)

    def setup_post_study(self):
        for ps in range(self.configs.post_study):
            self.configs.loads += self.configs.loads
            for i, uh in enumerate(self.uhes):
                self.uhes[i].affluents += uh.affluents

    def single_pl_config(self):
        # Variables
        # v[i][j][k] -> i = uhe, j = stage, k = node
        self.vf: List[List[variable]] = []
        self.vt: List[List[variable]] = []
        self.vv: List[List[variable]] = []
        for i, uh in enumerate(self.uhes):
            self.vf.append([])
            self.vt.append([])
            self.vv.append([])
            for j in range(self.configs.stage_count):
                self.vf[i].append(variable(self.node_counts[j],
                                           "Vf {}, stg {}"
                                           .format(uh.name, j)
                                           ))
                self.vt[i].append(variable(self.node_counts[j],
                                           "Vt {}, stg {}"
                                           .format(uh.name, j)
                                           ))
                self.vv[i].append(variable(self.node_counts[j],
                                           "Vv {}, stg {}"
                                           .format(uh.name, j)
                                           ))

        self.gt: List[List[variable]] = []
        # v[i][j][k] -> i = ute, j = stage, k = node
        for i, ut in enumerate(self.utes):
            self.gt.append([])
            for j in range(self.configs.stage_count):
                self.gt[i].append(variable(self.node_counts[j],
                                           "Gt {}, stg {}"
                                           .format(uh.name, j)
                                           ))

        self.deficit: List[variable] = []
        for j in range(self.configs.stage_count):
            self.deficit.append(variable(self.node_counts[j],
                                         "Déficit stg {}".format(j)))

        # Obj function
        self.obj_f: _function = 0
        for j in range(self.configs.stage_count):
            c = 1.0 / (self.configs.branch_count ** j)
            for k in range(self.node_counts[j]):
                for i, ut in enumerate(self.utes):
                    self.obj_f += c * ut.cost * self.gt[i][j][k]

                self.obj_f += (c * self.deficit[j][k] *
                               self.configs.deficit_cost)

                for i, uh in enumerate(self.uhes):
                    self.obj_f += c * 0.001 * self.vv[i][j][k]

        # -- Constraints --
        self.cons = []

        # Hydric balance
        for i, uh in enumerate(self.uhes):
            for j in range(self.configs.stage_count):
                for k in range(self.node_counts[j]):
                    if j == 0:
                        self.cons.append(
                            self.vf[i][j][k] == float(uh.initial_volume) +
                            float(uh.affluents[0][0]) -
                            self.vt[i][j][k] -
                            self.vv[i][j][k]
                        )
                    else:
                        prev_k = int(k / self.configs.branch_count)
                        br_idx = k % self.configs.branch_count
                        self.cons.append(
                            self.vf[i][j][k] == self.vf[i][j - 1][prev_k] +
                            float(uh.affluents[j][br_idx]) -
                            self.vt[i][j][k] -
                            self.vv[i][j][k]
                        )

        # Demand constraints
        for j in range(self.configs.stage_count):
            for k in range(self.node_counts[j]):
                balance = 0
                for i, uh in enumerate(self.uhes):
                    balance += uh.productivity * self.vt[i][j][k]
                for i, ut in enumerate(self.utes):
                    balance += self.gt[i][j][k]
                balance += self.deficit[j][k]

                self.cons.append(balance == self.configs.loads[j])

        # Operational constraints
        for i, uh in enumerate(self.uhes):
            for j in range(self.configs.stage_count):
                self.cons.append(self.vf[i][j] <= uh.max_volume)
                self.cons.append(self.vf[i][j] >= uh.min_volume)
                self.cons.append(self.vt[i][j] >= 0)
                self.cons.append(self.vt[i][j] <= uh.swallowing)
                self.cons.append(self.vv[i][j] >= 0)

        for i, ut in enumerate(self.utes):
            for j in range(self.configs.stage_count):
                self.cons.append(self.gt[i][j] >= 0)
                self.cons.append(self.gt[i][j] <= ut.capacity)

        for j in range(self.configs.stage_count):
            self.cons.append(self.deficit[j] >= 0)

    def single_pl_solve(self, log: bool = False):
        self.prob = op(self.obj_f, self.cons)
        print(self.prob)
        self.prob.solve('dense', 'glpk')
        # The results
        node_total = sum(self.node_counts)
        uhes: List[List[List[UHEResult]]] = []
        for j in range(self.configs.stage_count):
            node_partial = sum(self.node_counts[:j])
            uhe_stg: List[List[UHEResult]] = []
            for k in range(self.node_counts[j]):
                uhe_res: List[UHEResult] = []
                for i, uh in enumerate(self.uhes):
                    c = i * node_total + j * node_partial + k
                    r = UHEResult(self.vf[i][j][k].value()[0],
                                  self.vt[i][j][k].value()[0],
                                  self.vv[i][j][k].value()[0],
                                  self.cons[c].multiplier.value[0])
                    uhe_res.append(r)
                uhe_stg.append(uhe_res)
            uhes.append(uhe_stg)
        utes: List[List[List[UTEResult]]] = []
        for j in range(self.configs.stage_count):
            node_partial = sum(self.node_counts[:j])
            ute_stg: List[List[UTEResult]] = []
            for k in range(self.node_counts[j]):
                ute_res: List[UTEResult] = []
                for i, u in enumerate(self.utes):
                    ute_res.append(UTEResult(self.gt[i][j][k].value()[0]))
                ute_stg.append(ute_res)
            utes.append(ute_stg)
        deficits: List[List[float]] = []
        for j in range(self.configs.stage_count):
            deficits.append([])
            for k in range(self.node_counts[j]):
                deficits[-1].append(self.deficit[j][k].value()[0])
        res = Realization(self.obj_f.value()[0],
                          deficits,
                          uhes,
                          utes)
        if not log:
            return res
        # Report
        print("Custo total: ", self.obj_f.value())
        for j in range(self.configs.stage_count):
            for k in range(self.node_counts[j]):
                prev_k = int(k / self.configs.branch_count)
                br_idx = k % self.configs.branch_count
                for i, uh in enumerate(self.uhes):
                    if j == 0:
                        print("Vi " + uh.name + " " +
                              str(uh.initial_volume))
                    else:
                        print("Vi " + uh.name + " " +
                              str(self.vf[i][j - 1][prev_k].value()[0])
                              + "hm3")
                    print("Afl " + str(uh.affluents[j][br_idx]) + "hm3")
                    print(self.vf[i][j].name, i, "é",
                          self.vf[i][j][k].value()[0], "hm3")
                    print(self.vt[i][j].name, i, "é",
                          self.vt[i][j][k].value()[0], "hm3")
                    print(self.vv[i][j].name, i, "é",
                          self.vv[i][j][k].value()[0], "hm3")

                for i, ut in enumerate(self.utes):
                    print(self.gt[i][j].name, i, "é",
                          self.gt[i][j][k].value()[0], "MWmed")

                print(self.deficit[j].name, "é",
                      self.deficit[j][k].value()[0], "MWmed")

                # for i, u in enumerate(self.uhes):
                #     print("O valor da água na usina", i, "é",
                #         self.cons[i].multiplier.value[0])

                # print("O Custo Marginal de Operação é",
                #     self.cons[len(self.uhes)].multiplier.value[0])
                print("---------------- X ---------------")
        return res

    def forward_config(self,
                       stage: int,
                       scenario: int,
                       cuts: List[BendersCut]):
        # Variables
        self.vf = variable(len(self.uhes), "Volume final na usina")
        self.vt = variable(len(self.uhes), "Volume turbinado na usina")
        self.vv = variable(len(self.uhes), "Volume vertido na usina")
        self.gt = variable(len(self.utes), "Geração na usina térmica")
        self.deficit = variable(1, "Déficit de energia no sistema")
        self.alpha = variable(1, "Custo futuro")

        # Obj function
        self.obj_f: _function = 0
        for i, ut in enumerate(self.utes):
            self.obj_f += ut.cost * self.gt[i]

        self.obj_f += self.configs.deficit_cost * self.deficit[0]

        for i in range(len(self.uhes)):
            self.obj_f += 0.01 * self.vv[i]

        self.obj_f += 1.0 * self.alpha[0]

        # -- Constraints --
        self.cons = []

        # Hydric balance
        for i, uh in enumerate(self.uhes):
            if stage == 0:
                vi = float(uh.initial_volume)
            else:
                vi = float(uh.volume)
            afl = float(uh.affluents[stage][scenario])
            self.cons.append(
                self.vf[i] == vi + afl - self.vt[i] - self.vv[i])

        # Load balance
        balance = 0
        for i, uh in enumerate(self.uhes):
            balance += uh.productivity * self.vt[i]
        for i, ut in enumerate(self.utes):
            balance += self.gt[i]
        balance += self.deficit[0]
        self.cons.append(balance == self.configs.loads[stage])

        # Operational constraints
        for i, uh in enumerate(self.uhes):
            self.cons.append(self.vf[i] <= uh.max_volume)
            self.cons.append(self.vf[i] >= uh.min_volume)
            self.cons.append(self.vt[i] >= 0)
            self.cons.append(self.vt[i] <= uh.swallowing)
            self.cons.append(self.vv[i] >= 0)

        for i, ut in enumerate(self.utes):
            self.cons.append(self.gt[i] >= 0)
            self.cons.append(self.gt[i] <= ut.capacity)

        self.cons.append(self.deficit[0] >= 0)

        # Benders cuts
        self.cons.append(self.alpha[0] >= 0)
        for cut in cuts:
            eq = 0.
            for i in range(len(self.uhes)):
                eq += cut.wmc[i] * self.vf[i]
            eq += float(cut.offset)
            self.cons.append(self.alpha[0] >= eq)

    def backward_config(self,
                        stage: int,
                        scenario: int,
                        forward_realizations: List[Realization],
                        cuts: List[BendersCut]):

        # Variables
        self.vf = variable(len(self.uhes), "Volume final na usina")
        self.vt = variable(len(self.uhes), "Volume turbinado na usina")
        self.vv = variable(len(self.uhes), "Volume vertido na usina")
        self.gt = variable(len(self.utes), "Geração na usina térmica")
        self.deficit = variable(1, "Déficit de energia no sistema")
        self.alpha = variable(1, "Custo futuro")

        # Obj function
        self.obj_f: _function = 0
        for i, u in enumerate(self.utes):
            self.obj_f += u.cost * self.gt[i]

        self.obj_f += self.configs.deficit_cost * self.deficit[0]

        for i in range(len(self.uhes)):
            self.obj_f += 0.01 * self.vv[i]

        self.obj_f += 1.0 * self.alpha[0]

        # -- Constraints --
        self.cons = []

        # Hydric balance
        for i, uh in enumerate(self.uhes):
            if stage == 0:
                vi = float(uh.initial_volume)
            else:
                vi = float(forward_realizations[stage - 1].uhes[i].finalVolume)
            afl = float(uh.affluents[stage][scenario])
            self.cons.append(
                self.vf[i] == vi + afl - self.vt[i] - self.vv[i])

        # Load balance
        balance = 0
        for i, uh in enumerate(self.uhes):
            balance += uh.productivity * self.vt[i]
        for i, ut in enumerate(self.utes):
            balance += self.gt[i]
        balance += self.deficit[0]
        self.cons.append(balance == self.configs.loads[stage])

        # Operational constraints
        for i, uh in enumerate(self.uhes):
            self.cons.append(self.vf[i] >= uh.min_volume)
            self.cons.append(self.vf[i] <= uh.max_volume)
            self.cons.append(self.vt[i] >= 0)
            self.cons.append(self.vt[i] <= uh.swallowing)
            self.cons.append(self.vv[i] >= 0)

        for i, ut in enumerate(self.utes):
            self.cons.append(self.gt[i] >= 0)
            self.cons.append(self.gt[i] <= ut.capacity)

        self.cons.append(self.deficit[0] >= 0)

        # Benders cuts
        self.cons.append(self.alpha[0] >= 0)
        for cut in cuts:
            eq = 0.
            for i in range(len(self.uhes)):
                eq += cut.wmc[i] * self.vf[i]
            eq += float(cut.offset)
            self.cons.append(self.alpha[0] >= eq)

    def opt_solve(self, log: bool = True) -> Realization:
        self.prob = op(self.obj_f, self.cons)
        self.prob.solve('dense', 'glpk')
        # The results
        uhe_res: List[UHEResult] = []
        for i, u in enumerate(self.uhes):
            r = UHEResult(self.vf[i].value()[0],
                          self.vt[i].value()[0],
                          self.vv[i].value()[0],
                          self.cons[i].multiplier.value[0])
            uhe_res.append(r)
        ute_res: List[UTEResult] = []
        for i, u in enumerate(self.utes):
            ute_res.append(UTEResult(self.gt[i].value()[0]))
        res = Realization(self.obj_f.value()[0],
                          self.alpha[0].value()[0],
                          self.cons[len(self.uhes)].multiplier.value[0],
                          self.deficit[0].value()[0],
                          uhe_res,
                          ute_res)

        if not log:
            return res
        # Report
        print("Custo total: ", self.obj_f.value())
        for i, uh in enumerate(self.uhes):
            print(self.vf.name, i, "é", self.vt[i].value()[0], "hm3")
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

    def single_pl_dispatch(self):
        self.assemble_scenario_tree()
        self.single_pl_config()
        r = self.single_pl_solve(False)
        # Plotting
        vf: List[List[List[float]]] = []
        for i in range(len(self.uhes)):
            uhe_vf: List[List[float]] = []
            for j in range(self.configs.stage_count):
                stg_vf: List[float] = []
                for k in range(self.node_counts[j]):
                    stg_vf.append(r.uhes[j][k][i].finalVolume)
                uhe_vf.append(stg_vf)
            vf.append(uhe_vf)
        for i, uh in enumerate(self.uhes):
            fig = plt.figure()
            ax = fig.add_axes([0, 0, 1, 1])
            ax.boxplot(vf[i])
            plt.savefig("figures/volumes_{}.png".format(uh.name))

    def pddd_dispatch(self, scenario: int):
        # Benders cuts for each stage
        stages_post = (1 + self.configs.post_study) * self.configs.stage_count
        cuts: Dict[int, List[BendersCut]] = {}
        for s in range(stages_post + 1):
            cuts[s] = []
        # Cost estimated bounds
        it = 0
        tol = 1e-3
        z_sup = [np.inf]
        z_inf = [0.]
        # General loop
        while np.abs(z_sup[it] - z_inf[it]) > tol:
            # Forward loop
            z_sup[it] = 0.
            realizations: List[Realization] = []
            for s in range(stages_post):
                # Configures the forward problem
                self.forward_config(s, scenario, cuts[s + 1])
                # Solves and export results
                r = self.opt_solve(False)
                z_sup[it] += r.totalCost - r.futureCost
                if s == 0:
                    z_inf[it] = r.totalCost
                realizations.append(r)
                # Updates the UHE volumes
                for i, u in enumerate(self.uhes):
                    u.volume = r.uhes[i].finalVolume
            # Exit condition
            if np.abs(z_sup[it] - z_inf[it]) <= tol:
                break
            z_inf.append(z_inf[it])
            z_sup.append(z_sup[it])
            it += 1
            # Backward loop
            for s in np.arange(stages_post - 1, -1, -1):
                # Configures the backward problem
                self.backward_config(s, scenario, realizations, cuts[s + 1])
                # Solves and export results
                r = self.opt_solve(False)
                # Generates a new cut
                water_values: List[float] = []
                offset = r.totalCost
                for i, uhe_r in enumerate(r.uhes):
                    water_values.append(-uhe_r.waterValue)
                    if s == 0:
                        vi = self.uhes[i].initial_volume
                    else:
                        vi = realizations[s - 1].uhes[i].finalVolume
                    offset -= vi * water_values[i]
                bc = BendersCut(water_values, offset)
                cuts[s].append(bc)

        # -- Plotting --
        # Convergência
        x = np.arange(0, it + 1, 1)
        plt.figure()
        plt.plot(x + 1, z_inf, marker='o', linewidth=3.0, label='Zinf')
        plt.plot(x + 1, z_sup, marker='o', linewidth=3.0, label='Zsup')
        plt.legend()
        plt.title("Evolução dos erros inferior e superior")
        plt.xlabel("Iteração")
        plt.ylabel("Custo ($)")
        plt.xticks(x + 1)
        plt.grid()
        plt.tight_layout()
        plt.savefig('figures/convergencia.png')
        # Volumes
        x = np.arange(0, self.configs.stage_count, 1)
        for i, uh in enumerate(self.uhes):
            plt.figure()
            vfs = [r.uhes[i].finalVolume for r in realizations]
            vfs = vfs[:self.configs.stage_count]
            plt.plot(x + 1, vfs, marker='o', linewidth=2.0, label="Vf")
            vts = [r.uhes[i].turbinatedVolume for r in realizations]
            vts = vts[:self.configs.stage_count]
            plt.plot(x + 1, vts, marker='o', linewidth=2.0, label="Vt")
            vvs = [r.uhes[i].spilledVolume for r in realizations]
            vvs = vvs[:self.configs.stage_count]
            plt.plot(x + 1, vvs, marker='o', linewidth=2.0, label="Vv")
            plt.legend()
            plt.title("Volumes por estágio para {}".format(uh.name))
            plt.xlabel("Estágio")
            plt.ylabel("Volume (hm^3)")
            plt.xticks(x + 1)
            plt.grid()
            plt.tight_layout()
            plt.savefig('figures/volumes_{}.png'.format(uh.name))
        # CMA
        plt.figure()
        for i, uh in enumerate(self.uhes):
            wvals = [r.uhes[i].waterValue for r in realizations]
            wvals = wvals[:self.configs.stage_count]
            plt.plot(x + 1, wvals, marker='o', linewidth=2.0, label=uh.name)
        plt.legend()
        plt.title("Custo marginal da água por estágio")
        plt.xlabel("Estágio")
        plt.ylabel("Volume (hm^3)")
        plt.xticks(x + 1)
        plt.grid()
        plt.tight_layout()
        plt.savefig('figures/custo_agua.png')
        # UTES
        plt.figure()
        for i, ut in enumerate(self.utes):
            gts = [r.utes[i].generated for r in realizations]
            gts = gts[:self.configs.stage_count]
            plt.plot(x + 1, gts, marker='o', linewidth=2.0, label=ut.name)
        plt.legend()
        plt.title("Geração térmica por estágio")
        plt.xlabel("Estágio")
        plt.ylabel("Geração (MWmed)")
        plt.xticks(x + 1)
        plt.grid()
        plt.tight_layout()
        plt.savefig('figures/geracao_termicas.png')
