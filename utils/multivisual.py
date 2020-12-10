from modelos.cenario import Cenario
from modelos.resultado import Resultado
from modelos.uhe import UHE
from modelos.ute import UTE

import os
import csv
import logging
import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from typing import List


class MultiVisual:
    """
    Coletânea de recursos para geração de gráficos comparativos
    entre vários métodos de solução para os problemas de otimização.
    """
    def __init__(self,
                 resultados: List[Resultado],
                 caminho: str,
                 log: logging.Logger):

        self.uhes: List[UHE] = resultados[0].uhes
        self.utes: List[UTE] = resultados[0].utes
        self.resultados = resultados
        self.cenarios_medios = [Cenario.cenario_medio(r.cenarios)
                                for r in resultados]
        self.caminho = caminho
        self.log = log

    def visualiza(self):
        """
        Exporta os gráficos para comparação das saídas dos métodos.
        """
        self.visualiza_volume_final()

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
