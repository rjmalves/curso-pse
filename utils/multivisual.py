from modelos.cenario import Cenario
from modelos.resultado import Resultado
from modelos.uhe import UHE
from modelos.ute import UTE

import os
import csv
import logging
import coloredlogs  # type: ignore
import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from typing import List
logger = logging.getLogger(__name__)


class MultiVisual:
    """
    Coletânea de recursos para geração de gráficos comparativos
    entre vários métodos de solução para os problemas de otimização.
    """
    def __init__(self,
                 resultados: List[Resultado],
                 caminho: str,
                 LOG_LEVEL: str):

        self.uhes: List[UHE] = resultados[0].uhes
        self.utes: List[UTE] = resultados[0].utes
        self.resultados = resultados
        self.cenarios_medios = [Cenario.cenario_medio(r.cenarios)
                                for r in resultados]
        self.caminho = caminho
        self.log = logger
        coloredlogs.install(logger=logger, level=LOG_LEVEL)

    def visualiza(self):
        """
        Exporta os gráficos para comparação das saídas dos métodos.
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
        self.visualiza_alpha()
        self.visualiza_fobj()
        self.visualiza_convergencia()

    def visualiza_volume_final(self):
        """
        Gera as comparações dos volumes finais médios para cada método.
        """
        # Se o diretório para os volumes finais não existe, cria
        caminho = self.caminho + "volume_final/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
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
            dados_cen: List[List[float]] = []
            cabs_metodos: List[str] = []
            for j, resultado, cenario in zip(range(n_resultados),
                                             self.resultados,
                                             self.cenarios_medios):
                # Plota somente os cenários médios de cada método
                label = str(resultado.cfg.nome)
                cabs_metodos.append("VOLUME_FINAL_" + label)
                dados_cen.append(cenario.volumes_finais[i])
                plt.plot(x,
                         cenario.volumes_finais[i],
                         color=cmap(j / n_resultados),
                         marker="o",
                         linewidth=12,
                         alpha=0.5,
                         label=label)
            plt.legend()
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(uh.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", *cabs_metodos]
            dados = [x, *dados_cen]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_volume_turbinado(self):
        """
        Gera as comparações dos volumes turbinados médios para cada método.
        """
        # Se o diretório para os volumes turbinados não existe, cria
        caminho = self.caminho + "volume_turbinado/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
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
            dados_cen: List[List[float]] = []
            cabs_metodos: List[str] = []
            for j, resultado, cenario in zip(range(n_resultados),
                                             self.resultados,
                                             self.cenarios_medios):
                # Plota somente os cenários médios de cada método
                label = str(resultado.cfg.nome)
                cabs_metodos.append("VOLUME_TURBINADO_" + label)
                dados_cen.append(cenario.volumes_turbinados[i])
                plt.plot(x,
                         cenario.volumes_turbinados[i],
                         color=cmap(j / n_resultados),
                         marker="o",
                         linewidth=12,
                         alpha=0.5,
                         label=label)
            plt.legend()
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(uh.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", *cabs_metodos]
            dados = [x, *dados_cen]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_volume_vertido(self):
        """
        Gera as comparações dos volumes vertidos médios para cada método.
        """
        # Se o diretório para os volumes vertidos não existe, cria
        caminho = self.caminho + "volume_vertido/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
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
            dados_cen: List[List[float]] = []
            cabs_metodos: List[str] = []
            for j, resultado, cenario in zip(range(n_resultados),
                                             self.resultados,
                                             self.cenarios_medios):
                # Plota somente os cenários médios de cada método
                label = str(resultado.cfg.nome)
                cabs_metodos.append("VOLUME_VERTIDO_" + label)
                dados_cen.append(cenario.volumes_vertidos[i])
                plt.plot(x,
                         cenario.volumes_vertidos[i],
                         color=cmap(j / n_resultados),
                         marker="o",
                         linewidth=12,
                         alpha=0.5,
                         label=label)
            plt.legend()
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(uh.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", *cabs_metodos]
            dados = [x, *dados_cen]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_afluencias(self):
        """
        Gera as comparações das afluências médias para cada método.
        """
        # Se o diretório para as afluências não existe, cria
        caminho = self.caminho + "afluencias/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
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
            plt.ylabel("Afluência (hm3)")
            dados_cen: List[List[float]] = []
            cabs_metodos: List[str] = []
            for j, resultado, cenario in zip(range(n_resultados),
                                             self.resultados,
                                             self.cenarios_medios):
                # Plota somente os cenários médios de cada método
                label = str(resultado.cfg.nome)
                cabs_metodos.append("AFLUENCIA_" + label)
                dados_cen.append(cenario.afluencias[i])
                plt.plot(x,
                         cenario.afluencias[i],
                         color=cmap(j / n_resultados),
                         marker="o",
                         linewidth=12,
                         alpha=0.5,
                         label=label)
            plt.legend()
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(uh.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", *cabs_metodos]
            dados = [x, *dados_cen]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_custo_agua(self):
        """
        Gera as comparações dos CMA médios para cada método.
        """
        # Se o diretório para os CMA não existe, cria
        caminho = self.caminho + "CMA/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
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
            dados_cen: List[List[float]] = []
            cabs_metodos: List[str] = []
            for j, resultado, cenario in zip(range(n_resultados),
                                             self.resultados,
                                             self.cenarios_medios):
                # Plota somente os cenários médios de cada método
                label = str(resultado.cfg.nome)
                cabs_metodos.append("CMA_" + label)
                dados_cen.append(cenario.custo_agua[i])
                plt.plot(x,
                         cenario.custo_agua[i],
                         color=cmap(j / n_resultados),
                         marker="o",
                         linewidth=12,
                         alpha=0.5,
                         label=label)
            plt.legend()
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(uh.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", *cabs_metodos]
            dados = [x, *dados_cen]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_geracao_termica(self):
        """
        Gera as comparações das gerações médias
        das térmicas para cada método.
        """
        # Se o diretório para as térmicas não existe, cria
        caminho = self.caminho + "geracao_termica/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
        cmap = plt.get_cmap('viridis')
        for i, ut in enumerate(self.utes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("GERAÇÃO PARA {}".format(ut.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Energia gerada (MWmed)")
            dados_cen: List[List[float]] = []
            cabs_metodos: List[str] = []
            for j, resultado, cenario in zip(range(n_resultados),
                                             self.resultados,
                                             self.cenarios_medios):
                # Plota somente os cenários médios de cada método
                label = str(resultado.cfg.nome)
                cabs_metodos.append("GT_" + label)
                dados_cen.append(cenario.geracao_termica[i])
                plt.plot(x,
                         cenario.geracao_termica[i],
                         color=cmap(j / n_resultados),
                         marker="o",
                         linewidth=12,
                         alpha=0.5,
                         label=label)
            plt.legend()
            # Salva a imagem e exporta os dados
            caminho_saida = caminho + "{}".format(ut.nome)
            plt.savefig(caminho_saida + ".png")
            cabecalho = ["PERIODO", *cabs_metodos]
            dados = [x, *dados_cen]
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_deficit(self):
        """
        Gera as comparações dos déficits para cada método.
        """
        # Se o diretório para os déficits não existe, cria
        caminho = self.caminho + "deficits/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("DÉFICIT")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Déficit (MWmed)")
        dados_cen: List[List[float]] = []
        cabs_metodos: List[str] = []
        for j, resultado, cenario in zip(range(n_resultados),
                                         self.resultados,
                                         self.cenarios_medios):
            # Plota somente os cenários médios de cada método
            label = str(resultado.cfg.nome)
            cabs_metodos.append("DEF_" + label)
            dados_cen.append(cenario.deficit)
            plt.plot(x,
                     cenario.deficit,
                     color=cmap(j / n_resultados),
                     marker="o",
                     linewidth=12,
                     alpha=0.5,
                     label=label)
        plt.legend()
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "deficit"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", *cabs_metodos]
        dados = [x, *dados_cen]
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_cmo(self):
        """
        Gera as comparações do CMO para cada método.
        """
        # Se o diretório para o CMO não existe, cria
        caminho = self.caminho + "CMO/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("CMO")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Variação do custo ($/MWmed)")
        dados_cen: List[List[float]] = []
        cabs_metodos: List[str] = []
        for j, resultado, cenario in zip(range(n_resultados),
                                         self.resultados,
                                         self.cenarios_medios):
            # Plota somente os cenários médios de cada método
            label = str(resultado.cfg.nome)
            cabs_metodos.append("CMO_" + label)
            dados_cen.append(cenario.cmo)
            plt.plot(x,
                     cenario.cmo,
                     color=cmap(j / n_resultados),
                     marker="o",
                     linewidth=12,
                     alpha=0.5,
                     label=label)
        plt.legend()
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "cmo"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", *cabs_metodos]
        dados = [x, *dados_cen]
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_ci(self):
        """
        Gera as comparações dos custos imediatos para cada método.
        """
        # Se o diretório para os custos imediatos não existe, cria
        caminho = self.caminho + "custo_imediato/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("Custo Imediato")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Custo ($)")
        dados_cen: List[List[float]] = []
        cabs_metodos: List[str] = []
        for j, resultado, cenario in zip(range(n_resultados),
                                         self.resultados,
                                         self.cenarios_medios):
            # Plota somente os cenários médios de cada método
            label = str(resultado.cfg.nome)
            cabs_metodos.append("CI_" + label)
            dados_cen.append(cenario.ci)
            plt.plot(x,
                     cenario.ci,
                     color=cmap(j / n_resultados),
                     marker="o",
                     linewidth=12,
                     alpha=0.5,
                     label=label)
        plt.legend()
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "ci"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", *cabs_metodos]
        dados = [x, *dados_cen]
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_alpha(self):
        """
        Gera as comparações dos custos futuros para cada método.
        """
        # Se o diretório para os custos futuros não existe, cria
        caminho = self.caminho + "custo_futuro/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("Custo Futuro")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Custo ($)")
        dados_cen: List[List[float]] = []
        cabs_metodos: List[str] = []
        for j, resultado, cenario in zip(range(n_resultados),
                                         self.resultados,
                                         self.cenarios_medios):
            if resultado.cfg.metodo == "PL_UNICO":
                continue
            # Plota somente os cenários médios de cada método
            label = str(resultado.cfg.nome)
            cabs_metodos.append("CF_" + label)
            dados_cen.append(cenario.alpha)
            plt.plot(x,
                     cenario.alpha,
                     color=cmap(j / n_resultados),
                     marker="o",
                     linewidth=12,
                     alpha=0.5,
                     label=label)
        plt.legend()
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "alpha"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", *cabs_metodos]
        dados = [x, *dados_cen]
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_fobj(self):
        """
        Gera as comparações dos custos totais para cada método.
        """
        # Se o diretório para os custos totais não existe, cria
        caminho = self.caminho + "custo_total/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        n_periodos = self.resultados[0].cfg.n_periodos
        n_resultados = len(self.resultados)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("Custo total")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Custo ($)")
        dados_cen: List[List[float]] = []
        cabs_metodos: List[str] = []
        for j, resultado, cenario in zip(range(n_resultados),
                                         self.resultados,
                                         self.cenarios_medios):
            if resultado.cfg.metodo == "PL_UNICO":
                continue
            # Plota somente os cenários médios de cada método
            label = str(resultado.cfg.nome)
            cabs_metodos.append("FOBJ_" + label)
            dados_cen.append(cenario.fobj)
            plt.plot(x,
                     cenario.fobj,
                     color=cmap(j / n_resultados),
                     marker="o",
                     linewidth=12,
                     alpha=0.5,
                     label=label)
        plt.legend()
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "fobj"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", *cabs_metodos]
        dados = [x, *dados_cen]
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_convergencia(self):
        """
        Gera as comparações da convergência para cada método.
        """
        # Se o diretório para a convergência não existe, cria
        caminho = self.caminho
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        n_resultados = len(self.resultados)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("Convergência")
        # Eixo x:
        plt.xlabel("Iteração")
        # Eixo y:
        plt.ylabel("Limites do custo ($)")
        dados_cen: List[List[float]] = []
        cabs_metodos: List[str] = []
        eixos_x = [np.arange(1, len(r.z_sup), 1)
                   for r in self.resultados]
        iteracoes_x = [len(e) for e in eixos_x]
        ind_x_mais_longo = iteracoes_x.index(max(iteracoes_x))
        for j, resultado in enumerate(self.resultados):
            if resultado.cfg.metodo == "PL_UNICO":
                continue
            label = "ZSUP " + str(resultado.cfg.nome)
            cabs_metodos.append(label)
            dados_cen.append(resultado.z_sup)
            plt.plot(eixos_x[j],
                     resultado.z_sup[:len(resultado.z_sup)-1],
                     color=cmap(j / n_resultados + 0.1),
                     marker="o",
                     linewidth=12,
                     alpha=0.5,
                     label=label)

            label = "ZINF " + str(resultado.cfg.nome)
            cabs_metodos.append(label)
            dados_cen.append(resultado.z_inf)
            plt.plot(eixos_x[j],
                     resultado.z_inf[:len(resultado.z_inf)-1],
                     color=cmap(j / n_resultados + 0.15),
                     marker="o",
                     linewidth=12,
                     alpha=0.5,
                     label=label)
            if resultado.cfg.metodo == "PDDE":
                limite_inf = [conf[0] for conf
                              in resultado.intervalo_confianca]
                limite_sup = [conf[1] for conf
                              in resultado.intervalo_confianca]
                cabs_metodos.append("CONF_INF " + str(resultado.cfg.nome))
                cabs_metodos.append("CONF_SUP " + str(resultado.cfg.nome))
                dados_cen.append(limite_inf)
                dados_cen.append(limite_sup)
                label = "CONF " + str(resultado.cfg.nome)
                plt.fill_between(eixos_x[j],
                                 limite_inf,
                                 limite_sup,
                                 color=cmap(j / n_resultados + 0.2),
                                 alpha=0.2,
                                 label=label)
        plt.legend()
        plt.xticks(eixos_x[ind_x_mais_longo])
        # Salva a imagem e exporta os dados
        caminho_saida = caminho + "convergencia"
        plt.savefig(caminho_saida + ".png")
        cabecalho = ["PERIODO", *cabs_metodos]
        dados = [eixos_x[ind_x_mais_longo], *dados_cen]
        self.exporta_dados(caminho_saida, cabecalho, dados)
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
        n_dados = max([len(d) for d in dados])
        # Confere se a quantidade de entradas de cada dado é igual
        arq = caminho + ".csv"
        with open(arq, "w", newline="") as arqcsv:
            escritor = csv.writer(arqcsv,
                                  delimiter=",",
                                  quotechar="|",
                                  quoting=csv.QUOTE_MINIMAL)
            escritor.writerow(cabecalhos)
            for i in range(n_dados):
                a_escrever = []
                for d in dados:
                    if i < len(d):
                        a_escrever.append(d[i])
                    else:
                        a_escrever.append("")
                escritor.writerow(a_escrever)
