from utils.leituraentrada import LeituraEntrada
from pddd.modelos.arvoreafluencias import ArvoreAfluencias
from pddd.modelos.cenario import Cenario
from pddd.modelos.cortebenders import CorteBenders
from plunico.utils.visual import Visual
from plunico.utils.escrevesaida import EscreveSaida

import logging
import numpy as np
from typing import List
from cvxopt.modeling import variable, op, solvers, _function  # type: ignore
solvers.options['glpk'] = {'msg_lev': 'GLP_MSG_OFF'}


class PDDD:
    """
    Coletânea de métodos para solução de um estudo de
    planejamento energético através de Programação
    Dinâmica Dual Determinística.
    """
    def __init__(self, e: LeituraEntrada, log: logging.Logger):
        self.cfg = e.cfg
        self.uhes = e.uhes
        self.utes = e.utes
        self.demandas = e.demandas
        self.log = log
        self.arvore = ArvoreAfluencias(e)
        self.arvore.monta_arvore_afluencias()
        self.cenarios: List[Cenario] = []
        self.z_sup: List[float] = []
        self.z_inf: List[float] = []

    def __monta_pl_forward(self,
                           periodo: int,
                           indice_no: int) -> op:
        """
        Realiza a configuração das variáveis e restrições de um
        problema de otimização a ser realizado na iteração
        forward do problema de PDDD.
        """
        # ----- Variáveis -----
        self.vf = variable(len(self.uhes), "Volume final (hm3)")
        self.vt = variable(len(self.uhes), "Volume turbinado (hm3)")
        self.vv = variable(len(self.uhes), "Volume vertido (hm3)")
        self.gt = variable(len(self.utes), "Geração térmica (MWmed)")
        self.deficit = variable(1, "Déficit (MWmed)")
        self.alpha = variable(1, "Custo futuro ($)")

        # ----- Função objetivo -----
        self.func_objetivo: _function = 0
        for i, ut in enumerate(self.utes):
            self.func_objetivo += ut.custo * self.gt[i]

        self.func_objetivo += self.cfg.custo_deficit * self.deficit[0]

        for i in range(len(self.uhes)):
            self.func_objetivo += 0.01 * self.vv[i]

        self.func_objetivo += 1.0 * self.alpha[0]

        # ----- Restrições -----
        self.cons = []
        # Balanço hídrico
        for i, uh in enumerate(self.uhes):
            if periodo == 0:
                # O volume inicial é dado no problema
                vi = float(uh.vol_inicial)
            else:
                # O volume inicial é o final do nó anterior
                ant = self.arvore.indice_no_anterior(periodo, indice_no)
                vi = float(self.arvore.arvore[periodo - 1][ant]
                           .volumes_finais[i])
            afl = float(self.arvore.arvore[periodo][indice_no]
                        .afluencias[i])
            self.cons.append(self.vf[i] == vi + afl - self.vt[i] - self.vv[i])

        # Atendimento à demanda
        gerado = 0
        for i, uh in enumerate(self.uhes):
            gerado += float(uh.produtividade) + self.vt[i]
        for i, ut in enumerate(self.utes):
            gerado += self.gt[i]
        gerado += self.deficit[0]
        self.cons.append(gerado == float(self.demandas[periodo].demanda))

        # Restrições operacionais
        for i, uh in enumerate(self.uhes):
            # Volume útil do reservatório
            self.cons.append(self.vf[i] <= uh.vol_maximo)
            self.cons.append(self.vf[i] >= uh.vol_minimo)
            # Engolimento máximo
            self.cons.append(self.vt[i] <= uh.engolimento)
            # Factibilidade do problema
            self.cons.append(self.vt[i] >= 0)
            self.cons.append(self.vv[i] >= 0)
        for i, ut in enumerate(self.utes):
            # Geração mínima e máxima de térmica
            self.cons.append(self.gt[i] >= 0)
            self.cons.append(self.gt[i] <= ut.capacidade)
        # Factibilidade do problema
        self.cons.append(self.deficit[0] >= 0)

        # Cortes de Benders
        self.cons.append(self.alpha[0] >= 0)
        # Obtém o corte médio dos prováveis nós futuros
        indices_futuros = self.arvore.indices_proximos_nos(periodo,
                                                           indice_no)
        # Se não existem nós futuros, termina
        num_futuros = len(indices_futuros)
        if num_futuros == 0:
            return
        # Caso contrário, calcula o corte médio de cada iteração
        no_futuro = self.arvore.arvore[periodo + 1][indices_futuros[0]]
        num_cortes = len(no_futuro.cortes)
        num_uhes = len(self.uhes)
        # Para cada corte médio a ser calculado
        for i_corte in range(num_cortes):
            cma_medios = [0.] * num_uhes
            offset_medio = 0.
            # Para cada corte de possível nó futuro
            for i_futuro in indices_futuros:
                no_futuro = self.arvore.arvore[periodo + 1][i_futuro]
                corte = no_futuro.cortes[i_corte]
                # Calcula o custo médio da água
                for i_uhe in range(num_uhes):
                    cma_medios[i_uhe] += corte.custo_agua[i_uhe] / num_futuros
                # Calcula o offset médio
                offset_medio += corte.offset / num_futuros
            # Armazena o corte como restrição
            eq = 0.
            for i_uhe in range(num_uhes):
                eq += cma_medios[i_uhe] * self.vf[i_uhe]
            eq += float(offset_medio)
            self.cons.append(self.alpha[0] >= eq)

    def __monta_pl_backward(self,
                            periodo: int,
                            indice_no: int) -> op:
        """
        Realiza a configuração das variáveis e restrições de um
        problema de otimização a ser realizado na iteração
        backward do problema de PDDD.
        """
        # ----- Variáveis -----
        self.vf = variable(len(self.uhes), "Volume final (hm3)")
        self.vt = variable(len(self.uhes), "Volume turbinado (hm3)")
        self.vv = variable(len(self.uhes), "Volume vertido (hm3)")
        self.gt = variable(len(self.utes), "Geração térmica (MWmed)")
        self.deficit = variable(1, "Déficit (MWmed)")
        self.alpha = variable(1, "Custo futuro ($)")

        # ----- Função objetivo -----
        self.func_objetivo: _function = 0
        for i, ut in enumerate(self.utes):
            self.func_objetivo += ut.custo * self.gt[i]

        self.func_objetivo += self.cfg.custo_deficit * self.deficit[0]

        for i in range(len(self.uhes)):
            self.func_objetivo += 0.01 * self.vv[i]

        self.func_objetivo += 1.0 * self.alpha[0]

        # ----- Restrições -----
        self.cons = []
        # Balanço hídrico
        for i, uh in enumerate(self.uhes):
            if periodo == 0:
                # O volume inicial é dado no problema
                vi = float(uh.vol_inicial)
            else:
                # O volume inicial é o final do nó anterior na forward
                ant = self.arvore.indice_no_anterior(periodo, indice_no)
                vi = float(self.arvore.arvore[periodo - 1][ant]
                           .volumes_finais[i])
            afl = float(self.arvore.arvore[periodo][indice_no]
                        .afluencias[i])
            self.cons.append(self.vf[i] == vi + afl - self.vt[i] - self.vv[i])

        # Atendimento à demanda
        gerado = 0
        for i, uh in enumerate(self.uhes):
            gerado += float(uh.produtividade) + self.vt[i]
        for i, ut in enumerate(self.utes):
            gerado += self.gt[i]
        gerado += self.deficit[0]
        self.cons.append(gerado == float(self.demandas[periodo].demanda))

        # Restrições operacionais
        for i, uh in enumerate(self.uhes):
            # Volume útil do reservatório
            self.cons.append(self.vf[i] <= uh.vol_maximo)
            self.cons.append(self.vf[i] >= uh.vol_minimo)
            # Engolimento máximo
            self.cons.append(self.vt[i] <= uh.engolimento)
            # Factibilidade do problema
            self.cons.append(self.vt[i] >= 0)
            self.cons.append(self.vv[i] >= 0)
        for i, ut in enumerate(self.utes):
            # Geração mínima e máxima de térmica
            self.cons.append(self.gt[i] >= 0)
            self.cons.append(self.gt[i] <= ut.capacidade)
        # Factibilidade do problema
        self.cons.append(self.deficit[0] >= 0)

        # Cortes de Benders
        self.cons.append(self.alpha[0] >= 0)
        # Obtém o corte médio dos prováveis nós futuros
        indices_futuros = self.arvore.indices_proximos_nos(periodo,
                                                           indice_no)
        # Se não existem nós futuros, termina
        num_futuros = len(indices_futuros)
        if num_futuros == 0:
            return
        # Caso contrário, calcula o corte médio de cada iteração
        no_futuro = self.arvore.arvore[periodo + 1][indices_futuros[0]]
        num_cortes = len(no_futuro.cortes)
        num_uhes = len(self.uhes)
        # Para cada corte médio a ser calculado
        for i_corte in range(num_cortes):
            cma_medios = [0.] * num_uhes
            offset_medio = 0.
            # Para cada corte de possível nó futuro
            for i_futuro in indices_futuros:
                no_futuro = self.arvore.arvore[periodo + 1][i_futuro]
                corte = no_futuro.cortes[i_corte]
                # Calcula o custo médio da água
                for i_uhe in range(num_uhes):
                    cma_medios[i_uhe] += corte.custo_agua[i_uhe] / num_futuros
                # Calcula o offset médio
                offset_medio += corte.offset / num_futuros
            # Armazena o corte como restrição
            eq = 0.
            for i_uhe in range(num_uhes):
                eq += cma_medios[i_uhe] * self.vf[i_uhe]
            eq += float(offset_medio)
            self.cons.append(self.alpha[0] >= eq)

    def __monta_pl(self,
                   periodo: int,
                   indice_no: int) -> op:
        """
        Realiza a configuração das variáveis e restrições de um
        problema de otimização a ser realizado no problema de PDDD.
        """
        # ----- Variáveis -----
        self.vf = variable(len(self.uhes), "Volume final (hm3)")
        self.vt = variable(len(self.uhes), "Volume turbinado (hm3)")
        self.vv = variable(len(self.uhes), "Volume vertido (hm3)")
        self.gt = variable(len(self.utes), "Geração térmica (MWmed)")
        self.deficit = variable(1, "Déficit (MWmed)")
        self.alpha = variable(1, "Custo futuro ($)")

        # ----- Função objetivo -----
        self.func_objetivo: _function = 0
        for i, ut in enumerate(self.utes):
            self.func_objetivo += ut.custo * self.gt[i]

        self.func_objetivo += self.cfg.custo_deficit * self.deficit[0]

        for i in range(len(self.uhes)):
            self.func_objetivo += 0.01 * self.vv[i]

        self.func_objetivo += 1.0 * self.alpha[0]

        # ----- Restrições -----
        self.cons = []
        # Balanço hídrico
        for i, uh in enumerate(self.uhes):
            if periodo == 0:
                # O volume inicial é dado no problema
                vi = float(uh.vol_inicial)
            else:
                # O volume inicial é o final do nó anterior
                ant = self.arvore.indice_no_anterior(periodo, indice_no)
                vi = float(self.arvore.arvore[periodo - 1][ant]
                           .volumes_finais[i])
            afl = float(self.arvore.arvore[periodo][indice_no]
                        .afluencias[i])
            self.cons.append(self.vf[i] == vi + afl - self.vt[i] - self.vv[i])

        # Atendimento à demanda
        gerado = 0
        for i, uh in enumerate(self.uhes):
            gerado += float(uh.produtividade) + self.vt[i]
        for i, ut in enumerate(self.utes):
            gerado += self.gt[i]
        gerado += self.deficit[0]
        self.cons.append(gerado == float(self.demandas[periodo].demanda))

        # Restrições operacionais
        for i, uh in enumerate(self.uhes):
            # Volume útil do reservatório
            self.cons.append(self.vf[i] <= uh.vol_maximo)
            self.cons.append(self.vf[i] >= uh.vol_minimo)
            # Engolimento máximo
            self.cons.append(self.vt[i] <= uh.engolimento)
            # Factibilidade do problema
            self.cons.append(self.vt[i] >= 0)
            self.cons.append(self.vv[i] >= 0)
        for i, ut in enumerate(self.utes):
            # Geração mínima e máxima de térmica
            self.cons.append(self.gt[i] >= 0)
            self.cons.append(self.gt[i] <= ut.capacidade)
        # Factibilidade do problema
        self.cons.append(self.deficit[0] >= 0)

        # Cortes de Benders
        self.cons.append(self.alpha[0] >= 0)
        # Obtém o corte médio dos prováveis nós futuros
        indices_futuros = self.arvore.indices_proximos_nos(periodo,
                                                           indice_no)
        # Se não existem nós futuros, termina
        num_futuros = len(indices_futuros)
        if num_futuros == 0:
            return
        # Caso contrário, calcula o corte médio de cada iteração
        no_futuro = self.arvore.arvore[periodo + 1][indices_futuros[0]]
        num_cortes = len(no_futuro.cortes)
        num_uhes = len(self.uhes)
        # Para cada corte médio a ser calculado
        for i_corte in range(num_cortes):
            cma_medios = [0.] * num_uhes
            offset_medio = 0.
            # Para cada corte de possível nó futuro
            for i_futuro in indices_futuros:
                no_futuro = self.arvore.arvore[periodo + 1][i_futuro]
                corte = no_futuro.cortes[i_corte]
                # Calcula o custo médio da água
                for i_uhe in range(num_uhes):
                    cma_medios[i_uhe] += corte.custo_agua[i_uhe] / num_futuros
                # Calcula o offset médio
                offset_medio += corte.offset / num_futuros
            # Armazena o corte como restrição
            eq = 0.
            for i_uhe in range(num_uhes):
                eq += cma_medios[i_uhe] * self.vf[i_uhe]
            eq += float(offset_medio)
            self.cons.append(self.alpha[0] >= eq)

    def resolve_pddd(self) -> bool:
        """
        Resolve um problema de planejamento energético através da
        PDDD.
        """
        # Erros e condição de parada
        it = 0
        tol = 1e-3
        self.z_sup = [np.inf]
        self.z_inf = [0.]
        while np.abs(self.z_sup[it] - self.z_inf[it]) > tol:
            # Executa a forward para cada nó
            self.z_sup[it] = 0.
            for j in range(self.cfg.n_periodos):
                nos_periodo = self.arvore.nos_por_periodo[j]
                for k in range(nos_periodo):
                    # Monta e resolve o PL do nó
                    self.__monta_pl(j, k)
                    self.pl = op(self.func_objetivo, self.cons)
                    self.pl.solve("dense", "glpk")
                    # Armazena as saídas obtidas no PL no objeto nó
                    self.__armazena_saidas(j, k)
                    # Atualiza o z_sup e o z_inf
                    no = self.arvore.arvore[j][k]
                    self.z_sup[it] += (1. / nos_periodo) * (no.custo_total -
                                                            no.custo_futuro)
                    if j == 0:
                        self.z_inf[it] = no.custo_total
            # Condição de saída por convergência
            if np.abs(self.z_sup[it] - self.z_inf[it]) <= tol:
                return True
            self.z_inf.append(self.z_inf[it])
            self.z_sup.append(self.z_sup[it])
            it += 1
            # Condição de saída por iterações
            if it > 1000:
                return False
            # Executa a backward para cada nó
            for j in range(self.cfg.n_periodos - 1, -1, -1):
                for k in range(self.arvore.nos_por_periodo[j] - 1, -1, -1):
                    # Monta e resolve o PL do nó
                    self.__monta_pl(j, k)
                    self.pl = op(self.func_objetivo, self.cons)
                    self.pl.solve("dense", "glpk")
                    # Armazena as saídas obtidas no PL no objeto nó
                    self.__armazena_saidas(j, k)
                    # Gera um novo corte para o nó
                    no = self.arvore.arvore[j][k]
                    custos_agua: List[float] = []
                    offset = no.custo_total
                    for i, uh in enumerate(self.uhes):
                        custos_agua.append(-no.custo_agua[i])
                        if j == 0:
                            vi = uh.vol_inicial
                        else:
                            indice_ant = self.arvore.indice_no_anterior(j, k)
                            ant = self.arvore.arvore[j - 1][indice_ant]
                            vi = ant.volumes_finais[i]
                        offset -= vi * custos_agua[i]
                    no.adiciona_corte(CorteBenders(custos_agua, offset))

    def __armazena_saidas(self, j: int, k: int):
        """
        Processa as saídas do problema e armazena nos nós.
        """
        vol_finais: List[float] = []
        vol_turbinados: List[float] = []
        vol_vertidos: List[float] = []
        custo_agua: List[float] = []
        geracao_termica: List[float] = []
        for i, uh in enumerate(self.uhes):
            vol_finais.append(self.vf[i].value()[0])
            vol_turbinados.append(self.vt[i].value()[0])
            vol_vertidos.append(self.vv[i].value()[0])
            custo_agua.append(self.cons[i].multiplier.value[0])
        for i, ut in enumerate(self.utes):
            geracao_termica.append(self.gt[i].value()[0])
        deficit = self.deficit[0].value()[0]
        c_cmo = len(self.uhes)
        cmo = abs(self.cons[c_cmo].multiplier.value[0])
        alpha = self.alpha[0].value()[0]
        func_objetivo = self.func_objetivo.value()[0]
        self.arvore.arvore[j][k].preenche_resultados(vol_finais,
                                                     vol_turbinados,
                                                     vol_vertidos,
                                                     custo_agua,
                                                     geracao_termica,
                                                     deficit,
                                                     cmo,
                                                     alpha,
                                                     func_objetivo)
