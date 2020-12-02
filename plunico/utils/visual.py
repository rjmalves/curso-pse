from plunico.modelos.cenario import Cenario
from modelos.uhe import UHE
from modelos.ute import UTE

import os
import numpy as np
from typing import List
import matplotlib.pyplot as plt


class Visual:
    """
    Coletânea de recursos para geração de gráficos relacionados
    às soluções dos problemas de otimização.
    """
    def __init__(self,
                 uhes: List[UHE],
                 utes: List[UTE],
                 caminho: str,
                 cenarios: List[Cenario]):
        self.uhes = uhes
        self.utes = utes
        # O caminho base já contém NOME_ESTUDO/MÉTODO/EPOCH/
        self.caminho = caminho
        self.cenarios = cenarios

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
            # Salva a imagem
            plt.savefig(caminho + "{}.png".format(uh.nome))
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
            # Salva a imagem
            plt.savefig(caminho + "{}.png".format(uh.nome))
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
            # Salva a imagem
            plt.savefig(caminho + "{}.png".format(uh.nome))
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
            # Salva a imagem
            plt.savefig(caminho + "{}.png".format(uh.nome))
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
            # Salva a imagem
            plt.savefig(caminho + "{}.png".format(uh.nome))
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
            # Salva a imagem
            plt.savefig(caminho + "{}.png".format(ut.nome))
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
        # Salva a imagem
        plt.savefig(caminho + "deficit.png")
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
        # Salva a imagem
        plt.savefig(caminho + "cmo.png")
        plt.close()
