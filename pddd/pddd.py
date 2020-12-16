from utils.leituraentrada import LeituraEntrada
from modelos.arvoreafluencias import ArvoreAfluencias
from modelos.penteafluencias import PenteAfluencias
from modelos.cenario import Cenario
from modelos.cortebenders import CorteBenders
from modelos.resultado import Resultado

import logging
import coloredlogs  # type: ignore
import numpy as np  # type: ignore
from statistics import mean
from typing import List
from cvxopt.modeling import variable, op, solvers, _function  # type: ignore
solvers.options['glpk'] = {'msg_lev': 'GLP_MSG_OFF'}
logger = logging.getLogger(__name__)


class PDDD:
    """
    Coletânea de métodos para solução de um estudo de
    planejamento energético através de Programação
    Dinâmica Dual Determinística.
    """
    def __init__(self, e: LeituraEntrada, LOG_LEVEL: str):
        self.cfg = e.cfg
        self.uhes = e.uhes
        self.utes = e.utes
        self.demandas = e.demandas
        coloredlogs.install(logger=logger, level=LOG_LEVEL)
        self.arvore = ArvoreAfluencias(e)
        self.arvore.monta_arvore_afluencias()
        self.sim_final = PenteAfluencias(e)
        self.cenarios: List[Cenario] = []
        self.z_sup: List[float] = []
        self.z_inf: List[float] = []

    def __monta_pl(self,
                   arvore: ArvoreAfluencias,
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
                ant = arvore.indice_no_anterior(periodo, indice_no)
                vi = float(arvore.arvore[periodo - 1][ant]
                           .volumes_finais[i])
            afl = float(arvore.arvore[periodo][indice_no]
                        .afluencias[i])
            self.cons.append(self.vf[i] == vi + afl - self.vt[i] - self.vv[i])

        # Atendimento à demanda
        gerado = 0
        for i, uh in enumerate(self.uhes):
            gerado += float(uh.produtividade) * self.vt[i]
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

        # Cortes de Benders - exceto se estiver no último período
        self.cons.append(self.alpha[0] >= 0)
        if periodo == self.cfg.n_periodos - 1:
            return
        num_uhes = len(self.uhes)
        # Obtém o corte médio dos prováveis nós futuros
        indices_futuros = arvore.indices_proximos_nos(periodo,
                                                      indice_no)
        n_futuros = len(indices_futuros)
        no_futuro = arvore.arvore[periodo + 1][indices_futuros[0]]
        num_cortes = len(no_futuro.cortes)

        # Calcula os cortes médios para cada corte existente nos nós futuros
        cortes_medios: List[CorteBenders] = []
        for i_corte in range(num_cortes):
            cma_medios = [0.] * num_uhes
            termo_indep_medio = 0.
            for i_futuro in indices_futuros:
                no_futuro = arvore.arvore[periodo + 1][i_futuro]
                corte = no_futuro.cortes[i_corte]
                # Calcula o PI médio
                for i_uhe in range(num_uhes):
                    cma_medios[i_uhe] += corte.coef_angular[i_uhe] / n_futuros
                # Calcula o termo independente médio
                termo_indep_medio += corte.termo_indep / n_futuros
            # Caso contrário, se não houver corte igual já no nó, adiciona
            corte_medio = CorteBenders(cma_medios, termo_indep_medio, 0.0)
            cortes_medios.append(corte_medio)

        # Armazena os cortes médios como restrições
        for corte in cortes_medios:
            eq = 0.
            for i_uhe in range(num_uhes):
                eq += corte.coef_angular[i_uhe] * self.vf[i_uhe]
            eq += float(corte.termo_indep)
            self.cons.append(self.alpha[0] >= eq)

    def __monta_pl_pente(self,
                         pente: PenteAfluencias,
                         dente: int,
                         periodo: int,
                         abertura: int = -1) -> op:
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
        self.func_objetivo = 0
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
                vi = float(pente.dentes[dente][periodo - 1]
                           .volumes_finais[i])
            # Se está executando a FORWARD, a afluência é a do nó
            # anterior no mesmo dente. Caso contrário, é da abertura
            # passada à função de montar o PL.
            if abertura == -1:
                afl = float(pente.dentes[dente][periodo]
                            .afluencias[i])
            else:
                afl = float(pente
                            .afluencias_abertura(periodo, abertura)[i])
            self.cons.append(self.vf[i] == vi + afl - self.vt[i] - self.vv[i])

        # Atendimento à demanda
        gerado = 0
        for i, uh in enumerate(self.uhes):
            gerado += float(uh.produtividade) * self.vt[i]
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

        # Cortes de Benders - exceto se estiver no último período
        self.cons.append(self.alpha[0] >= 0)
        if periodo == self.cfg.n_periodos - 1:
            return
        num_uhes = len(self.uhes)
        # Adiciona os cortes do próximo nó, no mesmo dente
        no_futuro = pente.dentes[dente][periodo + 1]
        for corte in no_futuro.cortes:
            eq = 0.
            for i_uhe in range(num_uhes):
                eq += float(corte.coef_angular[i_uhe]) * self.vf[i_uhe]
            eq += float(corte.termo_indep)
            self.cons.append(self.alpha[0] >= eq)

    def resolve_pddd(self) -> Resultado:
        """
        Resolve um problema de planejamento energético através da
        PDDD.
        """
        # Erros e condição de parada
        it = 0
        self.tol = 1e-3
        self.z_sup = []
        self.z_inf = []
        logger.info("# RESOLVENDO PROBLEMA DE PDDD #")
        logger.info("X----X-------------------X-------------------X")
        logger.info("  IT        Z_SUP                 Z_INF       ")
        while True:
            for j in range(self.cfg.n_periodos):
                nos_periodo = self.arvore.nos_por_periodo[j]
                for k in range(nos_periodo):
                    # Monta e resolve o PL do nó (exceto a partir da
                    # segunda iteração, no período 1 - pois a backward é igual)
                    if it == 0 or j > 0:
                        self.__monta_pl(self.arvore, j, k)
                        self.pl = op(self.func_objetivo, self.cons)
                        self.pl.solve("dense", "glpk")
                        # Armazena as saídas obtidas no PL no objeto nó
                        self.__armazena_saidas(self.arvore, j, k)
            # Condição de saída por convergência
            it += 1
            if self.__verifica_convergencia(it):
                break
            # Condição de saída por iterações
            if it >= self.cfg.max_iter:
                logger.warning("   LIMITE DE ITERAÇÕES ATINGIDO!")
                break
            # Executa a backward para cada nó
            for j in range(self.cfg.n_periodos - 1, -1, -1):
                for k in range(self.arvore.nos_por_periodo[j] - 1, -1, -1):
                    # Monta e resolve o PL do nó (não resolve o último período)
                    if j != self.cfg.n_periodos - 1:
                        self.__monta_pl(self.arvore, j, k)
                        self.pl = op(self.func_objetivo, self.cons)
                        self.pl.solve("dense", "glpk")
                        # Armazena as saídas obtidas no PL no objeto nó
                        self.__armazena_saidas(self.arvore, j, k)
                    # Gera um novo corte para o nó
                    self.__cria_corte(j, k)
        # Terminando o loop do método, organiza e retorna os resultados
        logger.info("X----X-------------------X-------------------X")
        self.__simulacao_final()
        logger.info("# FIM DA SOLUÇÃO #")
        logger.info("----------------------------------------")
        return Resultado(self.cfg,
                         self.uhes,
                         self.utes,
                         self.sim_final.organiza_cenarios(),
                         self.z_sup,
                         self.z_inf,
                         [],
                         self.__organiza_cortes())

    def __organiza_cortes(self) -> List[List[List[CorteBenders]]]:
        """
        """
        cortes: List[List[List[CorteBenders]]] = []
        for p in range(self.cfg.n_periodos):
            cortes.append([])
            for n in range(self.arvore.nos_por_periodo[p]):
                no = self.arvore.arvore[p][n]
                cortes[-1].append(no.cortes)
        return cortes

    def __cria_corte(self, j: int, k: int):
        """
        Cria um novo corte de Benders para um nó, tomando a média
        dos cortes dos nós futuros (exceto no último período).
        """
        no = self.arvore.arvore[j][k]
        coefs_angulares: List[float] = []
        termo_indep = no.custo_total
        for i, uh in enumerate(self.uhes):
            coefs_angulares.append(-no.custo_agua[i])
            if j == 0:
                vi = uh.vol_inicial
            else:
                indice_ant = self.arvore.indice_no_anterior(j, k)
                ant = self.arvore.arvore[j - 1][indice_ant]
                vi = ant.volumes_finais[i]
            termo_indep -= vi * coefs_angulares[i]
        corte = CorteBenders(coefs_angulares, termo_indep, no.custo_total)
        no.adiciona_corte(corte, True)

    def __verifica_convergencia(self, it: int) -> bool:
        """
        Verifica se houve a convergência para a PDDD, conferindo
        os limites inferior e superior e a tolerância.
        """
        z_sup = 0.0
        z_inf = 0.0
        for j in range(self.cfg.n_periodos):
            nos_periodo = self.arvore.nos_por_periodo[j]
            for k in range(nos_periodo):
                no = self.arvore.arvore[j][k]
                z_sup += (1. / nos_periodo) * no.custo_imediato
                if j == 0:
                    z_inf = no.custo_total
        self.z_sup.append(z_sup)
        self.z_inf.append(z_inf)

        logger.info(" {:4}    {:16.6f}    {:16.6f}".
                    format(it + 1, z_sup, z_inf))

        if np.abs(z_sup - z_inf) <= self.tol:
            n_it = len(self.z_inf)
            if n_it < self.cfg.min_iter:
                return False
            logger.info("   >> CONVERGIU <<: Z_SUP e Z_INF na tolerância!!")
            return True

        return False

    def __armazena_saidas(self, arvore: ArvoreAfluencias, j: int, k: int):
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
        arvore.arvore[j][k].preenche_resultados(vol_finais,
                                                vol_turbinados,
                                                vol_vertidos,
                                                custo_agua,
                                                geracao_termica,
                                                deficit,
                                                cmo,
                                                func_objetivo - alpha,
                                                alpha,
                                                func_objetivo)

    def __armazena_saidas_pente(self, pente: PenteAfluencias, d: int, p: int):
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
        f_obj = self.func_objetivo.value()[0]
        pente.dentes[d][p].preenche_resultados(vol_finais,
                                               vol_turbinados,
                                               vol_vertidos,
                                               custo_agua,
                                               geracao_termica,
                                               deficit,
                                               cmo,
                                               f_obj - alpha,
                                               alpha,
                                               f_obj)

    def __simulacao_final(self):
        """
        """
        logger.info("            # SIMULAÇÂO FINAL #")
        logger.info("X-------------------X-------------------X")
        logger.info("       Z_SUP                Z_INF       ")
        self.sim_final.monta_simulacao_final_de_arvore(self.arvore)
        # Realiza uma "forward"
        for p in range(self.cfg.n_periodos):
            for d, dente in enumerate(self.sim_final.dentes):
                self.__monta_pl_pente(self.sim_final, d, p)
                self.pl = op(self.func_objetivo, self.cons)
                self.pl.solve("dense", "glpk")
                # Armazena as saídas obtidas no PL no objeto nó
                self.__armazena_saidas_pente(self.sim_final, d, p)
        # Calcula o Z_inf
        z_inf = mean([d[0].custo_total for d in self.sim_final.dentes])
        self.z_inf.append(z_inf)
        # Obtém os custos imediatos para cada nó de cada dente
        custos_imediatos: List[List[float]] = []
        for dente in self.sim_final.dentes:
            custos_imediatos_dente = [n.custo_total - n.custo_futuro
                                      for n in dente]
            custos_imediatos.append(custos_imediatos_dente)
        # Calcula o Z_sup
        custos_dente = [sum(custo_dente)
                        for custo_dente in custos_imediatos]
        z_sup = mean(custos_dente)
        self.z_sup.append(z_sup)
        logger.info(" {:19.6f} {:19.6f}".format(z_sup, z_inf))
        logger.info("X-------------------X-------------------X")
