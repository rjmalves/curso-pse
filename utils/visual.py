from modelos.resultado import Resultado
from modelos.cenario import Cenario
from modelos.uhe import UHE
from modelos.ute import UTE

import os
import csv
import logging
import coloredlogs  # type: ignore
import numpy as np  # type: ignore
from typing import List
import matplotlib.pyplot as plt  # type: ignore
logger = logging.getLogger(__name__)


class Visual:
    """
    Coletânea de recursos para geração de gráficos relacionados
    às soluções dos problemas de otimização.
    """
    def __init__(self,
                 resultado: Resultado,
                 caminho: str,
                 LOG_LEVEL: str):

        self.metodo = resultado.cfg.metodo
        self.uhes: List[UHE] = resultado.uhes
        self.utes: List[UTE] = resultado.utes
        # O caminho base já contém NOME_ESTUDO/MÉTODO/EPOCH/
        self.caminho = caminho
        self.cenarios = resultado.cenarios
        self.z_sup = resultado.z_sup
        self.z_inf = resultado.z_inf
        self.intervalo_conf = resultado.intervalo_confianca
        self.cortes = resultado.cortes
        self.log = logger
        coloredlogs.install(logger=logger, level=LOG_LEVEL)

    def visualiza(self):
        """
        Exporta os gráficos para visualização das saídas do problema
        de otimização.
        """
        self.visualiza_volume_final()
        self.visualiza_volume_turbinado()
        self.visualiza_volume_vertido()
        self.visualiza_afluencias()
        self.visualiza_custo_agua()
        self.visualiza_geracao_termica()
        self.visualiza_deficit()
        self.visualiza_cmo()
        self.visualiza_ci()
        if self.metodo == "PL_UNICO":
            return
        self.visualiza_alpha()
        self.visualiza_fobj()
        self.visualiza_convergencia()
        self.visualiza_cortes()

    def visualiza_volume_final(self):
        """
        Gera os gráficos para acompanhamento dos volumes finais.
        """
        # Se o diretório para os volumes finais não existe, cria
        caminho = self.caminho + "volume_final/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, uh in enumerate(self.uhes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("VOLUME FINAL PARA {}".format(uh.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Volume final (hm3)")
            for j, cen in enumerate(self.cenarios):
                plt.plot(x,
                         cen.volumes_finais[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Plota o cenário médio
            cenario_medio = Cenario.cenario_medio(self.cenarios)
            plt.plot(x,
                     cenario_medio.volumes_finais[i],
                     color=cmap(1),
                     marker="o",
                     linewidth=16,
                     alpha=0.2,
                     label="Cenário médio")
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(uh.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", "VOLUME_FINAL"]
            dados = [x, cenario_medio.volumes_finais[i]]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_volume_turbinado(self):
        """
        Gera os gráficos para acompanhamento dos volumes turbinados.
        """
        # Se o diretório para os volumes turbinados não existe, cria
        caminho = self.caminho + "volume_turbinado/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, uh in enumerate(self.uhes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("VOLUME TURBINADO PARA {}".format(uh.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Volume turbinado (hm3)")
            for j, cen in enumerate(self.cenarios):
                plt.plot(x,
                         cen.volumes_turbinados[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Plota o cenário médio
            cenario_medio = Cenario.cenario_medio(self.cenarios)
            plt.plot(x,
                     cenario_medio.volumes_turbinados[i],
                     color=cmap(1),
                     marker="o",
                     linewidth=16,
                     alpha=0.2,
                     label="Cenário médio")
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(uh.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", "VOLUME_TURBINADO"]
            dados = [x, cenario_medio.volumes_turbinados[i]]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_volume_vertido(self):
        """
        Gera os gráficos para acompanhamento dos volumes vertidos.
        """
        # Se o diretório para os volumes vertidos não existe, cria
        caminho = self.caminho + "volume_vertido/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, uh in enumerate(self.uhes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("VOLUME VERTIDO PARA {}".format(uh.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Volume vertido (hm3)")
            for j, cen in enumerate(self.cenarios):
                plt.plot(x,
                         cen.volumes_vertidos[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Plota o cenário médio
            cenario_medio = Cenario.cenario_medio(self.cenarios)
            plt.plot(x,
                     cenario_medio.volumes_vertidos[i],
                     color=cmap(1),
                     marker="o",
                     linewidth=16,
                     alpha=0.2,
                     label="Cenário médio")
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(uh.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", "VOLUME_VERTIDO"]
            dados = [x, cenario_medio.volumes_vertidos[i]]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_afluencias(self):
        """
        Gera os gráficos para acompanhamento das afluências.
        """
        # Se o diretório para as afluências não existe, cria
        caminho = self.caminho + "afluencias/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, uh in enumerate(self.uhes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("AFLUÊNCIAS PARA {}".format(uh.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Volume (hm3)")
            for j, cen in enumerate(self.cenarios):
                plt.plot(x,
                         cen.afluencias[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Plota o cenário médio
            cenario_medio = Cenario.cenario_medio(self.cenarios)
            plt.plot(x,
                     cenario_medio.afluencias[i],
                     color=cmap(1),
                     marker="o",
                     linewidth=16,
                     alpha=0.2,
                     label="Cenário médio")
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(uh.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", "AFLUENCIA"]
            dados = [x, cenario_medio.afluencias[i]]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_custo_agua(self):
        """
        Gera os gráficos para acompanhamento do CMA.
        """
        # Se o diretório para o CMA não existe, cria
        caminho = self.caminho + "CMA/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, uh in enumerate(self.uhes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("CMA PARA {}".format(uh.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Variação do custo ($/hm3)")
            for j, cen in enumerate(self.cenarios):
                plt.plot(x,
                         cen.custo_agua[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Plota o cenário médio
            cenario_medio = Cenario.cenario_medio(self.cenarios)
            plt.plot(x,
                     cenario_medio.custo_agua[i],
                     color=cmap(1),
                     marker="o",
                     linewidth=16,
                     alpha=0.2,
                     label="Cenário médio")
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(uh.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", "CUSTO_AGUA"]
            dados = [x, cenario_medio.custo_agua[i]]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_geracao_termica(self):
        """
        Gera os gráficos para acompanhamento da geração das térmicas.
        """
        # Se o diretório para as térmicas não existe, cria
        caminho = self.caminho + "geracao_termica/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UTE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, ut in enumerate(self.utes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("GERAÇÂO TÉRMICA PARA {}".format(ut.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Geração (MWmed)")
            for j, cen in enumerate(self.cenarios):
                plt.plot(x,
                         cen.geracao_termica[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Plota o cenário médio
            cenario_medio = Cenario.cenario_medio(self.cenarios)
            plt.plot(x,
                     cenario_medio.geracao_termica[i],
                     color=cmap(1),
                     marker="o",
                     linewidth=16,
                     alpha=0.2,
                     label="Cenário médio")
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(ut.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", "GERACAO"]
            dados = [x, cenario_medio.geracao_termica[i]]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_deficit(self):
        """
        Gera os gráficos para acompanhamento do déficit.
        """
        # Se o diretório para os déficits não existe, cria
        caminho = self.caminho + "deficit/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UTE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("DÉFICITS")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Geração (MWmed)")
        for j, cen in enumerate(self.cenarios):
            plt.plot(x,
                     cen.deficit,
                     color=cmap(j / n_cenarios),
                     marker="o",
                     linewidth=4,
                     alpha=0.2,
                     label="Cenário {}".format(j + 1))
        # Plota o cenário médio
        cenario_medio = Cenario.cenario_medio(self.cenarios)
        plt.plot(x,
                 cenario_medio.deficit,
                 color=cmap(1),
                 marker="o",
                 linewidth=16,
                 alpha=0.2,
                 label="Cenário médio")
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "deficit"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", "DEFICIT"]
        dados = [x, cenario_medio.deficit]
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_cmo(self):
        """
        Gera os gráficos para acompanhamento do CMO.
        """
        # Se o diretório para o CMO não existe, cria
        caminho = self.caminho + "CMO/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UTE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("CUSTO MARGINAL DE OPERAÇÂO")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Variação do Custo ($/MWmed)")
        for j, cen in enumerate(self.cenarios):
            plt.plot(x,
                     cen.cmo,
                     color=cmap(j / n_cenarios),
                     marker="o",
                     linewidth=4,
                     alpha=0.2,
                     label="Cenário {}".format(j + 1))
        # Plota o cenário médio
        cenario_medio = Cenario.cenario_medio(self.cenarios)
        plt.plot(x,
                 cenario_medio.cmo,
                 color=cmap(1),
                 marker="o",
                 linewidth=16,
                 alpha=0.2,
                 label="Cenário médio")
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "cmo"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", "CMO"]
        dados = [x, cenario_medio.cmo]
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_ci(self):
        """
        Gera os gráficos para acompanhamento do Custo Imediato.
        """
        # Se o diretório para o CMO não existe, cria
        caminho = self.caminho + "custo_imediato/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UTE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("CUSTO IMEDIATO DE OPERAÇÃO")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Custo ($/MWmed)")
        for j, cen in enumerate(self.cenarios):
            plt.plot(x,
                     cen.ci,
                     color=cmap(j / n_cenarios),
                     marker="o",
                     linewidth=4,
                     alpha=0.2,
                     label="Cenário {}".format(j + 1))
        # Plota o cenário médio
        cenario_medio = Cenario.cenario_medio(self.cenarios)
        plt.plot(x,
                 cenario_medio.ci,
                 color=cmap(1),
                 marker="o",
                 linewidth=16,
                 alpha=0.2,
                 label="Cenário médio")
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "ci"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", "CUSTO_IMEDIATO"]
        dados = [x, cenario_medio.ci]
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_alpha(self):
        """
        Gera os gráficos para acompanhamento do Custo Futuro.
        """
        # Se o diretório para o CMO não existe, cria
        caminho = self.caminho + "custo_futuro/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UTE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("CUSTO FUTURO DE OPERAÇÃO")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Custo ($/MWmed)")
        for j, cen in enumerate(self.cenarios):
            plt.plot(x,
                     cen.alpha,
                     color=cmap(j / n_cenarios),
                     marker="o",
                     linewidth=4,
                     alpha=0.2,
                     label="Cenário {}".format(j + 1))
        # Plota o cenário médio
        cenario_medio = Cenario.cenario_medio(self.cenarios)
        plt.plot(x,
                 cenario_medio.alpha,
                 color=cmap(1),
                 marker="o",
                 linewidth=16,
                 alpha=0.2,
                 label="Cenário médio")
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "alpha"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", "CUSTO_FUTURO"]
        dados = [x, cenario_medio.alpha]
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_fobj(self):
        """
        Gera os gráficos para acompanhamento do Custo Total.
        """
        # Se o diretório para o CMO não existe, cria
        caminho = self.caminho + "custo_total/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UTE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("CUSTO TOTAL DE OPERAÇÃO")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Custo ($/MWmed)")
        for j, cen in enumerate(self.cenarios):
            plt.plot(x,
                     cen.fobj,
                     color=cmap(j / n_cenarios),
                     marker="o",
                     linewidth=4,
                     alpha=0.2,
                     label="Cenário {}".format(j + 1))
        # Plota o cenário médio
        cenario_medio = Cenario.cenario_medio(self.cenarios)
        plt.plot(x,
                 cenario_medio.fobj,
                 color=cmap(1),
                 marker="o",
                 linewidth=16,
                 alpha=0.2,
                 label="Cenário médio")
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "fobj"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", "CUSTO_TOTAL"]
        dados = [x, cenario_medio.fobj]
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_convergencia(self):
        """
        Gera gráficos para visualização da convergência do método.
        """
        n_iters = len(self.z_sup)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("CONVERGÊNCIA DA {}".format(self.metodo))
        # Eixo x:
        plt.xlabel("Iteração")
        x = np.arange(1, n_iters, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Limites do custo ($)")
        plt.plot(x,
                 self.z_sup[:n_iters-1],
                 color=cmap(0.6),
                 marker="o",
                 linewidth=4,
                 alpha=0.8,
                 label="Z_sup")
        plt.plot(x,
                 self.z_inf[:n_iters-1],
                 color=cmap(0.3),
                 marker="o",
                 linewidth=4,
                 alpha=0.8,
                 label="Z_inf")
        if self.metodo == "PDDE":
            # Plota o intervalo de confiança
            limite_inf = [i[0] for i in self.intervalo_conf]
            limite_sup = [i[1] for i in self.intervalo_conf]
            plt.fill_between(x,
                             limite_inf,
                             limite_sup,
                             color=cmap(0.6),
                             alpha=0.2,
                             label="Área de confiança")
        plt.legend()
        # Salva a imagem
        plt.savefig(self.caminho + "convergencia.png")
        plt.close()

    def visualiza_cortes(self):
        """
        """
        caminho = self.caminho + "cortes/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        for p, cortes_p in enumerate(self.cortes):
            if self.metodo == "PDDE":
                plt.figure(figsize=(12, 6))
                plt.title("CORTES PARA O PERÍODO {}".format(p + 1))
                # Calcula sempre para a UHE 1
                x = np.arange(self.uhes[0].vol_minimo,
                              self.uhes[0].vol_maximo,
                              1000)
                max_y = 0
                cortes = cortes_p[0]
                for c in cortes:
                    y = c.coef_angular[0] * x + c.termo_indep
                    max_y = max([max_y, np.max(y)])
                    plt.plot(x, y)
                plt.ylim(0, max_y)
                plt.savefig(caminho + "p{}.png".format(p + 1))
                plt.close()
            if self.metodo == "PDDD":
                plt.figure(figsize=(12, 6))
                plt.title("CORTES PARA O PERÍODO {}".format(p + 1))
                # Calcula sempre para a UHE 1
                x = np.arange(self.uhes[0].vol_minimo,
                              self.uhes[0].vol_maximo,
                              1000)
                max_y = 0
                for cortes in cortes_p:
                    for c in cortes:
                        y = c.coef_angular[0] * x + c.termo_indep
                        max_y = max([max_y, np.max(y)])
                        plt.plot(x, y)
                plt.ylim(0, max_y)
                plt.savefig(caminho + "p{}.png".format(p + 1))
                plt.close()

    def exporta_dados(self,
                      caminho: str,
                      cabecalhos: List[str],
                      dados: List[list]):
        """
        Exporta um conjunto de dados de uma determinada visualização
        para um formato CSV.
        """
        # Confere se o número de cabeçalhos é igual ao de dados
        n_dados = len(dados[0])
        # Confere se a quantidade de entradas de cada dado é igual
        arq = caminho + ".csv"
        with open(arq, "w", newline="") as arqcsv:
            escritor = csv.writer(arqcsv,
                                  delimiter=",",
                                  quotechar="|",
                                  quoting=csv.QUOTE_MINIMAL)
            escritor.writerow(cabecalhos)
            for i in range(n_dados):
                escritor.writerow([d[i] for d in dados])
