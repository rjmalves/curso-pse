from utils.leituraentrada import LeituraEntrada
from pddd.modelos.arvoreafluencias import ArvoreAfluencias
from modelos.no import No
from modelos.cenario import Cenario
from modelos.cortebenders import CorteBenders
from pddd.utils.visual import Visual
from pddd.utils.escrevesaida import EscreveSaida

import logging
import numpy as np  # type: ignore
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
        indices_futuros = self.arvore.indices_proximos_nos(periodo,
                                                           indice_no)
        num_futuros = len(indices_futuros)
        no_futuro = self.arvore.arvore[periodo + 1][indices_futuros[0]]
        num_cortes = len(no_futuro.cortes)
        self.log.debug("Cortes de benders para o nó {} do período {}: {}".
                       format(indice_no + 1, periodo + 1, num_cortes))

        # Calcula os cortes médios para cada corte existente nos nós futuros
        cortes_medios: List[CorteBenders] = []
        for i_corte in range(num_cortes):
            cma_medios = [0.] * num_uhes
            offset_medio = 0.
            for i_futuro in indices_futuros:
                no_futuro = self.arvore.arvore[periodo + 1][i_futuro]
                corte = no_futuro.cortes[i_corte]
                # Calcula o custo médio da água
                for i_uhe in range(num_uhes):
                    cma_medios[i_uhe] += corte.custo_agua[i_uhe] / num_futuros
                # Calcula o offset médio
                offset_medio += corte.offset / num_futuros
            # Caso contrário, se não houver corte igual já no nó, adiciona
            corte_medio = CorteBenders(cma_medios, offset_medio)
            cortes_medios.append(corte_medio)

        # Armazena os cortes médios como restrições
        for corte in cortes_medios:
            eq = 0.
            self.log.debug("CORTE = {}".format(corte))
            for i_uhe in range(num_uhes):
                eq += corte.custo_agua[i_uhe] * self.vf[i_uhe]
            eq += float(corte.offset)
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
            self.log.info("# Iteração {} #".format(it + 1))
            self.z_sup[it] = 0.
            for j in range(self.cfg.n_periodos):
                self.log.debug("Executando a FORWARD para o período {}...".
                               format(j + 1))
                nos_periodo = self.arvore.nos_por_periodo[j]
                for k in range(nos_periodo):
                    # Monta e resolve o PL do nó (exceto a partir da
                    # segunda iteração, no período 1 - pois a backward é igual)
                    if it == 0 or j > 0:
                        self.log.debug("Resolvendo o PL do nó {}...".
                                       format(k + 1))
                        self.__monta_pl(j, k)
                        self.pl = op(self.func_objetivo, self.cons)
                        self.pl.solve("dense", "glpk")
                        # Armazena as saídas obtidas no PL no objeto nó
                        self.__armazena_saidas(j, k)
                    # Atualiza o z_sup e o z_inf
                    no = self.arvore.arvore[j][k]
                    self.log.debug(no.resumo())
                    self.z_sup[it] += (1. / nos_periodo) * (no.custo_total -
                                                            no.custo_futuro)
                    if j == 0:
                        self.z_inf[it] = no.custo_total
                    self.log.debug("Z_sup = {}".format(self.z_sup[it]))
                    self.log.debug("Z_inf = {}".format(self.z_inf[it]))
            # Condição de saída por convergência
            if np.abs(self.z_sup[it] - self.z_inf[it]) <= tol:
                self.log.info("Sup= {:12.6f} | Inf= {:12.6f} | {:12.6f} <= {}".
                              format(self.z_sup[it],
                                     self.z_inf[it],
                                     np.abs(self.z_sup[it] - self.z_inf[it]),
                                     tol))
                self.log.info("CONVERGIU!")
                self.__organiza_cenarios()
                return True
            self.log.info("Sup= {:12.6f} | Inf= {:12.6f} | {:12.6f} > {}".
                          format(self.z_sup[it],
                                 self.z_inf[it],
                                 np.abs(self.z_sup[it] - self.z_inf[it]),
                                 tol))
            self.z_inf.append(self.z_inf[it])
            self.z_sup.append(self.z_sup[it])
            it += 1
            # Condição de saída por iterações
            if it >= 50:
                self.__organiza_cenarios()
                self.log.warning("LIMITE DE ITERAÇÕES ATINGIDO!")
                return False
            if it >= 5:
                erros = [self.z_sup[i] - self.z_inf[i]
                         for i in range(-5, 0)]
                if len(set(erros)) == 1:
                    self.__organiza_cenarios()
                    self.log.warning("NÃO CONVERGIU ABAIXO DA TOLERÂNCIA!")
                    return False
            # Executa a backward para cada nó
            for j in range(self.cfg.n_periodos - 1, -1, -1):
                self.log.debug("Executando a BACKWARD para o período {}...".
                               format(j + 1))
                for k in range(self.arvore.nos_por_periodo[j] - 1, -1, -1):
                    # Monta e resolve o PL do nó (não resolve o último período)
                    if j != self.cfg.n_periodos - 1:
                        self.log.debug("Resolvendo o PL do nó {}...".
                                       format(k + 1))
                        no = self.arvore.arvore[j][k]
                        self.__monta_pl(j, k)
                        self.pl = op(self.func_objetivo, self.cons)
                        self.pl.solve("dense", "glpk")
                        # Armazena as saídas obtidas no PL no objeto nó
                        self.__armazena_saidas(j, k)
                        self.log.debug(no.resumo())
                    # Gera um novo corte para o nó
                    self.__cria_corte(j, k)
        return False

    def __cria_corte(self, j: int, k: int):
        """
        Cria um novo corte de Benders para um nó, tomando a média
        dos cortes dos nós futuros (exceto no último período).
        """
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
        corte = CorteBenders(custos_agua, offset)
        self.log.debug("NOVO CORTE {} - {} : {}".format(j + 1, k + 1, corte))
        no.adiciona_corte(corte, True)

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
                                                     func_objetivo - alpha,
                                                     alpha,
                                                     func_objetivo)

    def __organiza_cenarios(self):
        """
        Parte das folhas e reconstroi as séries históricas de cada variável de
        interesse para cada cenário que aconteceu no estudo realizado.
        """
        n_cenarios = self.arvore.nos_por_periodo[-1]
        cenarios: List[Cenario] = []
        for c in range(n_cenarios):
            self.log.debug("##### CENARIO " + str(c + 1) + " #####")
            nos_cenario: List[No] = []
            indice_no = c
            for p in range(self.cfg.n_periodos - 1, -1, -1):
                no = self.arvore.arvore[p][indice_no]
                nos_cenario.insert(0, no)
                indice_no = self.arvore.indice_no_anterior(p, indice_no)
            cen = Cenario.cenario_dos_nos(nos_cenario)
            self.log.debug(cen)
            self.log.debug("--------------------------------------")
            cenarios.append(cen)
        self.cenarios = cenarios

    def __escreve_relatorio_estudo(self, caminho: str):
        """
        """
        saida = EscreveSaida(self.cfg,
                             self.uhes,
                             self.utes,
                             caminho,
                             self.cenarios,
                             self.arvore,
                             self.z_sup,
                             self.z_inf,
                             self.log)
        saida.escreve_relatorio()

    def __gera_graficos(self, caminho: str):
        """
        """
        vis = Visual(self.uhes, self.utes, caminho, self.cenarios)
        vis.visualiza()

    def escreve_saidas(self, caminho: str):
        """
        """
        self.__escreve_relatorio_estudo(caminho)
        self.__gera_graficos(caminho)
