from pdde.modelos.cortebenders import CorteBenders
from pdde.modelos.penteafluencias import PenteAfluencias
from pdde.modelos.cenario import Cenario
from utils.leituraentrada import LeituraEntrada

import logging
from typing import List
import numpy as np  # type: ignore
from statistics import pstdev, mean
from cvxopt.modeling import variable, op, solvers, _function  # type: ignore
solvers.options['glpk'] = {'msg_lev': 'GLP_MSG_OFF'}


class PDDE:
    """
    Coletânea de métodos para solução de um estudo de
    planejamento energético através de Programação
    Dinâmica Dual Estocástica.
    """
    def __init__(self, e: LeituraEntrada, log: logging.Logger):
        self.cfg = e.cfg
        self.uhes = e.uhes
        self.utes = e.utes
        self.demandas = e.demandas
        self.log = log
        self.pente = PenteAfluencias(e)
        self.pente.monta_pente_afluencias()
        # self.cenarios: List[Cenario] = []
        # self.z_sup: List[float] = []
        # self.z_inf: List[float] = []

    def __monta_pl(self,
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
                vi = float(self.pente.dentes[dente][periodo - 1]
                           .volumes_finais[i])
            # Se está executando a FORWARD, a afluência é a do nó
            # anterior no mesmo dente. Caso contrário, é da abertura
            # passada à função de montar o PL.
            if abertura == -1:
                afl = float(self.pente.dentes[dente][periodo - 1]
                            .afluencias[i])
            else:
                afl = float(self.pente
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
        no_futuro = self.pente.dentes[dente][periodo + 1]
        for corte in no_futuro.cortes:
            eq = 0.
            for i_uhe in range(num_uhes):
                eq += corte.custo_agua[i_uhe] * self.vf[i_uhe]
            eq += float(corte.offset)
            self.cons.append(self.alpha[0] >= eq)

    def resolve_pdde(self) -> bool:
        """
        Resolve um problema de planejamento energético através da
        PDDE.
        """
        # Erros e condição de parada
        it = 0
        self.z_sup = [np.inf]
        self.z_inf = [0.]
        while True:
            self.log.info("# Iteração {} #".format(it + 1))
            # Realiza, para cada dente, a parte FORWARD
            for d, dente in enumerate(self.pente.dentes):
                for p in range(self.cfg.n_periodos):
                    self.log.debug("Executando a FORWARD no período {}...".
                                   format(p + 1))
                    self.__monta_pl(d, p)
                    self.pl = op(self.func_objetivo, self.cons)
                    self.pl.solve("dense", "glpk")
                    # Armazena as saídas obtidas no PL no objeto nó
                    self.__armazena_saidas(d, p)
            # Condição de saída por convergência
            if self.__verifica_convergencia():
                self.log.info("CONVERGIU!")
                self.__organiza_cenarios()
                return True
            it += 1
            # Condição de saída por iterações
            if it >= 50:
                self.__organiza_cenarios()
                self.log.warning("LIMITE DE ITERAÇÕES ATINGIDO!")
                return False
            if it >= 10:
                erros = [self.z_sup[i] - self.z_inf[i]
                         for i in range(-5, 0)]
                if len(set(erros)) == 1:
                    self.__organiza_cenarios()
                    self.log.warning("NÃO CONVERGIU ABAIXO DA TOLERÂNCIA!")
                    return False
            # Realiza, para cada dente, a parte BACKWARD
            for d, dente in enumerate(self.pente.dentes):
                for p in range(self.cfg.n_periodos - 1, -1, -1):
                    self.log.debug("Executando a BACKWARD no período {}...".
                                   format(p + 1))
                    # A BACKWARD na PDDE, para obter um corte,
                    # na verdade é constituída de múltiplos problemas
                    # de despacho e o corte é o médio de todas.
                    cortes_no: List[CorteBenders] = []
                    for a in range(self.cfg.aberturas_periodo):
                        self.__monta_pl(d, p, a)
                        self.pl = op(self.func_objetivo, self.cons)
                        self.pl.solve("dense", "glpk")
                        # Armazena as saídas obtidas no nó
                        self.__armazena_saidas(d, p)
                        cortes_no.append(self.__obtem_corte(d, p))
                    # Cria o corte médio de fato para o nó em questão
                    self.__cria_corte(d, p, cortes_no)

    def __obtem_corte(self, d: int, p: int) -> CorteBenders:
        """
        Obtém o corte de Benders a partir do resultado de um PL
        backward da PDDE.
        """
        no = self.pente.dentes[d][p]
        custos_agua: List[float] = []
        offset = no.custo_total
        for i, uh in enumerate(self.uhes):
            custos_agua.append(-no.custo_agua[i])
            if p == 0:
                vi = uh.vol_inicial
            else:
                ant = self.pente.dentes[d][p - 1]
                vi = ant.volumes_finais[i]
            offset -= vi * custos_agua[i]
        corte = CorteBenders(custos_agua, offset)
        return corte

    def __cria_corte(self, d: int, p: int, cortes: List[CorteBenders]):
        """
        Armazena o corte de Benders médio para um nó.
        """
        # Calcula os cortes médios para cada corte existente nos nós futuros
        num_uhes = len(self.uhes)
        num_cortes = self.cfg.aberturas_periodo
        cma_medios = [0.] * num_uhes
        offset_medio = 0.
        for i, corte in enumerate(cortes):
            # Calcula o custo médio da água
            for i_uhe in range(num_uhes):
                cma_medios[i_uhe] += corte.custo_agua[i_uhe] / num_cortes
            # Calcula o offset médio
            offset_medio += corte.offset / num_cortes
        # Caso contrário, se não houver corte igual já no nó, adiciona
        corte_medio = CorteBenders(cma_medios, offset_medio)
        self.pente.dentes[d][p].adiciona_corte(corte_medio)

    def __verifica_convergencia(self) -> bool:
        """
        Verifica se houve a convergência para a PDDE, conferindo
        os limites inferior e superior, bem como o intervalo de
        confiança.
        """
        # Calcula o Z_inf
        z_inf = mean([d[0].custo_total for d in self.pente.dentes])
        self.z_inf.append(z_inf)
        # Obtém os custos imediatos para cada nó de cada dente
        custos_imediatos: List[List[float]] = []
        for dente in self.pente.dentes:
            custos_imediatos_dente = [n.custo_total - n.custo_futuro
                                      for n in dente]
            custos_imediatos.append(custos_imediatos_dente)
        # Calcula o Z_sup
        custos_dente = [sum(custo_dente)
                        for custo_dente in custos_imediatos]
        z_sup = mean(custos_dente)
        self.z_sup.append(z_sup)
        # Calcula o intervalo de confiança
        desvio = pstdev(custos_dente)
        limite_inf = max([1e-3, z_sup - 1.96 * desvio])
        limite_sup = z_sup + 1.96 * desvio
        self.log.debug("Z_SUP = {} - Z_INF = {}. INTERVALO = [{}, {}]".
                       format(z_sup, z_inf, limite_inf, limite_sup))
        if limite_inf <= z_inf <= limite_sup:
            self.log.info("{} <= {} <= {}".
                          format(limite_inf,
                                 z_inf,
                                 limite_sup))
            return True
        else:
            if z_inf < limite_inf:
                self.log.info("Ainda não convergiu: {} < {}".
                              format(z_inf,
                                     limite_inf))
            elif z_inf > limite_sup:
                self.log.info("Ainda não convergiu: {} > {}".
                              format(z_inf,
                                     limite_sup))
            return False

    def __armazena_saidas(self, d: int, p: int):
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
        self.pente.dentes[d][p].preenche_resultados(vol_finais,
                                                    vol_turbinados,
                                                    vol_vertidos,
                                                    custo_agua,
                                                    geracao_termica,
                                                    deficit,
                                                    cmo,
                                                    alpha,
                                                    f_obj)

    def __organiza_cenarios(self):
        """
        Para cada dente do pente, monta as séries históricas de cada
        variável de interesse no estudo realizado.
        """
        n_dentes = len(self.pente.dentes)
        cenarios: List[Cenario] = []
        for c in range(n_dentes):
            self.log.debug("##### CENARIO " + str(c + 1) + " #####")
            cen = Cenario(self.pente.dentes[c])
            self.log.debug(cen)
            self.log.debug("--------------------------------------")
            cenarios.append(cen)
        self.cenarios = cenarios
