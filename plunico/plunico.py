from utils.leituraentrada import LeituraEntrada
from plunico.modelos.arvoreafluencias import ArvoreAfluencias

from typing import List
from cvxopt.modeling import variable, op, solvers, _function  # type: ignore
solvers.options['glpk'] = {'msg_lev': 'GLP_MSG_OFF'}


class PLUnico:
    """
    Coletânea de métodos para solução de um estudo de
    planejamento energético através de PL Único.
    """
    def __init__(self, e: LeituraEntrada):
        self.cfg = e.cfg
        self.uhes = e.uhes
        self.utes = e.utes
        self.demandas = e.demandas
        self.arvore = ArvoreAfluencias(e)
        self.arvore.monta_arvore_afluencias()

    def monta_pl(self) -> op:
        """
        Realiza a configuração das variáveis e restrições
        do PL Único a ser resolvido.
        """
        # ----- Variáveis -----
        # Volume final
        self.vf: List[List[variable]] = []
        # Volume turbinado
        self.vt: List[List[variable]] = []
        # Volume vertido
        self.vv: List[List[variable]] = []
        for i, uh in enumerate(self.uhes):
            self.vf.append([])
            self.vt.append([])
            self.vv.append([])
            for j in range(self.cfg.n_periodos):
                nos_periodo = self.arvore.nos_por_periodo[j]
                self.vf[i].append(variable(nos_periodo,
                                           "Vf {}, per {}"
                                           .format(uh.nome, j)
                                           ))
                self.vt[i].append(variable(nos_periodo,
                                           "Vt {}, per {}"
                                           .format(uh.nome, j)
                                           ))
                self.vv[i].append(variable(nos_periodo,
                                           "Vv {}, per {}"
                                           .format(uh.nome, j)
                                           ))

        # Geração térmica
        self.gt: List[List[variable]] = []
        for i, ut in enumerate(self.utes):
            self.gt.append([])
            for j in range(self.cfg.n_periodos):
                nos_periodo = self.arvore.nos_por_periodo[j]
                self.gt[i].append(variable(nos_periodo,
                                           "Gt {}, per {}"
                                           .format(ut.nome, j)
                                           ))

        # Déficit
        self.deficit: List[variable] = []
        for j in range(self.cfg.n_periodos):
            nos_periodo = self.arvore.nos_por_periodo[j]
            self.deficit.append(variable(nos_periodo,
                                         "Deficit per {}"
                                         .format(j)))

        # ----- Função objetivo -----
        self.func_objetivo: _function = 0
        for j in range(self.cfg.n_periodos):
            # Constante para média entre os nós
            nos_periodo = self.arvore.nos_por_periodo[j]
            c = 1.0 / nos_periodo
            for k in range(nos_periodo):
                # Custo proveniente das térmicas
                for i, ut in enumerate(self.utes):
                    self.func_objetivo += c * ut.custo * self.gt[i][j][k]
                # Custo pelo déficit
                self.func_objetivo += (c * self.deficit[j][k] *
                                       self.cfg.custo_deficit)
                # Custo pela energia não turbinada
                for i, uh in enumerate(self.uhes):
                    self.func_objetivo += c * 0.001 * self.vv[i][j][k]

        # ----- Restrições -----
        self.cons = []
        # Balanço hídrico
        for i, uh in enumerate(self.uhes):
            for j in range(self.cfg.n_periodos):
                for k in range(self.arvore.nos_por_periodo[j]):
                    if j == 0:
                        self.cons.append(
                            self.vf[i][j][k] == float(uh.vol_inicial) +
                            float(self.arvore.arvore[0][0].afluencias[i]) -
                            self.vt[i][j][k] -
                            self.vv[i][j][k]
                        )
                    else:
                        ant = self.arvore.indice_no_anterior(j, k)
                        no = self.arvore.arvore[j][k]
                        self.cons.append(
                            self.vf[i][j][k] == self.vf[i][j - 1][ant] +
                            float(no.afluencias[i]) -
                            self.vt[i][j][k] -
                            self.vv[i][j][k]
                        )
        # Atendimento à demanda
        for j in range(self.cfg.n_periodos):
            for k in range(self.arvore.nos_por_periodo[j]):
                gerado = 0
                for i, uh in enumerate(self.uhes):
                    gerado += float(uh.produtividade) * self.vt[i][j][k]
                for i, ut in enumerate(self.utes):
                    gerado += self.gt[i][j][k]
                gerado += self.deficit[j][k]

            self.cons.append(gerado == float(self.demandas[j].demanda))

        # Restrições operacionais
        for i, uh in enumerate(self.uhes):
            for j in range(self.cfg.n_periodos):
                # Volume útil do reservatório
                self.cons.append(self.vf[i][j] <= uh.vol_maximo)
                self.cons.append(self.vf[i][j] >= uh.vol_minimo)
                # Engolimento máximo
                self.cons.append(self.vt[i][j] <= uh.engolimento)
                # Factibilidade do problema
                self.cons.append(self.vt[i][j] >= 0)
                self.cons.append(self.vv[i][j] >= 0)
        for i, ut in enumerate(self.utes):
            for j in range(self.cfg.n_periodos):
                # Geração mínima e máxima da térmica
                self.cons.append(self.gt[i][j] >= 0)
                self.cons.append(self.gt[i][j] <= ut.capacidade)
        for j in range(self.cfg.n_periodos):
            # Factibilidade do problema
            self.cons.append(self.deficit[j] >= 0)

        return op(self.func_objetivo, self.cons)
