from utils.leituraentrada import LeituraEntrada
from pddd.modelos.arvoreafluencias import ArvoreAfluencias
from modelos.no import No
from modelos.cenario import Cenario
from modelos.cortebenders import CorteBenders
from modelos.resultado import Resultado

import logging
import coloredlogs  # type: ignore
import numpy as np  # type: ignore
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
        self.log = logger
        coloredlogs.install(logger=logger, level=LOG_LEVEL)
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
            corte_medio = CorteBenders(cma_medios, offset_medio, 0.0)
            cortes_medios.append(corte_medio)

        # Armazena os cortes médios como restrições
        for corte in cortes_medios:
            eq = 0.
            for i_uhe in range(num_uhes):
                eq += corte.custo_agua[i_uhe] * self.vf[i_uhe]
            eq += float(corte.offset)
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
        while True:
            self.log.info("# Iteração {} #".format(it + 1))
            for j in range(self.cfg.n_periodos):
                nos_periodo = self.arvore.nos_por_periodo[j]
                for k in range(nos_periodo):
                    # Monta e resolve o PL do nó (exceto a partir da
                    # segunda iteração, no período 1 - pois a backward é igual)
                    if it == 0 or j > 0:
                        self.__monta_pl(j, k)
                        self.pl = op(self.func_objetivo, self.cons)
                        self.pl.solve("dense", "glpk")
                        # Armazena as saídas obtidas no PL no objeto nó
                        self.__armazena_saidas(j, k)
            # Condição de saída por convergência
            it += 1
            if self.__verifica_convergencia():
                break
            # Condição de saída por iterações
            if it >= self.cfg.max_iter:
                self.log.warning("LIMITE DE ITERAÇÕES ATINGIDO!")
                break
            # Executa a backward para cada nó
            for j in range(self.cfg.n_periodos - 1, -1, -1):
                for k in range(self.arvore.nos_por_periodo[j] - 1, -1, -1):
                    # Monta e resolve o PL do nó (não resolve o último período)
                    if j != self.cfg.n_periodos - 1:
                        self.__monta_pl(j, k)
                        self.pl = op(self.func_objetivo, self.cons)
                        self.pl.solve("dense", "glpk")
                        # Armazena as saídas obtidas no PL no objeto nó
                        self.__armazena_saidas(j, k)
                    # Gera um novo corte para o nó
                    self.__cria_corte(j, k)
        # Terminando o loop do método, organiza e retorna os resultados
        self.__organiza_cenarios()
        return Resultado(self.cfg,
                         self.uhes,
                         self.utes,
                         self.cenarios,
                         self.z_sup,
                         self.z_inf,
                         [])

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
        corte = CorteBenders(custos_agua, offset, no.custo_total)
        no.adiciona_corte(corte, True)

    def __verifica_convergencia(self) -> bool:
        """
        Verifica se houve a convergência para a PDDD, conferindo
        os limites inferior e superior e a tolerância.
        """
        z_sup = 0.0
        z_inf = 0.0
        print(self.arvore.nos_por_periodo)
        for j in range(self.cfg.n_periodos):
            nos_periodo = self.arvore.nos_por_periodo[j]
            for k in range(nos_periodo):
                no = self.arvore.arvore[j][k]
                z_sup += (1. / nos_periodo) * no.ci
                if j == 0:
                    z_inf = no.custo_total
        self.z_sup.append(z_sup)
        self.z_inf.append(z_inf)

        if np.abs(z_sup - z_inf) <= self.tol:
            self.log.info("Sup= {:12.6f} | Inf= {:12.6f} | {:12.6f} <= {}".
                          format(z_sup,
                                 z_inf,
                                 np.abs(z_sup - z_inf),
                                 self.tol))
            n_it = len(self.z_inf)
            if n_it < self.cfg.min_iter:
                return False
            self.log.info("CONVERGIU!")
            return True

        self.log.info("Sup= {:12.6f} | Inf= {:12.6f} | {:12.6f} > {}".
                      format(z_sup,
                             z_inf,
                             np.abs(z_sup - z_inf),
                             self.tol))
        return False

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
            nos_cenario: List[No] = []
            indice_no = c
            for p in range(self.cfg.n_periodos - 1, -1, -1):
                no = self.arvore.arvore[p][indice_no]
                nos_cenario.insert(0, no)
                indice_no = self.arvore.indice_no_anterior(p, indice_no)
            cen = Cenario.cenario_dos_nos(nos_cenario)
            cenarios.append(cen)
        self.cenarios = cenarios
