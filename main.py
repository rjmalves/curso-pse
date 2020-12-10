# from modelos.configgeral import ConfigGeral
from modelos.metodo import Metodo
from modelos.resultado import Resultado
from utils.leituraentrada import LeituraEntrada
from utils.visual import Visual
from utils.multivisual import MultiVisual
from utils.escrevesaida import EscreveSaida

import time
import logging
from typing import List
import coloredlogs  # type: ignore

logger = logging.getLogger(__name__)
coloredlogs.install(logger=logger, level="INFO")


def main():
    logger.critical("#### ESTUDO DE MODELOS DE PLANEJAMENTO ENERGÉTICO ####")
    # Lê o arquivo de configuração de entrada
    entrada = "./tests/entrada.txt"
    e = LeituraEntrada(entrada, logger)
    logger.critical("Arquivo de entrada selecionado: {}".format(entrada))
    e.le_arquivo()
    # Determina o método de solução
    metodo = Metodo.obtem_metodo_pelo_valor(e.cfg.metodo)
    logger.critical("Método de solução escolhido: {}".format(metodo.value))
    # Resolve o problema de otimização
    cenarios = metodo.resolve(e, logger)
    # Gera relatórios e gráficos de saída
    caminho_saida = "results/{}/{}/{}/".format(e.cfg.nome,
                                               metodo.value,
                                               int(time.time()))
    relator = EscreveSaida(metodo,
                           cenarios,
                           caminho_saida,
                           logger)
    relator.escreve_relatorio()
    visualizador = Visual(metodo,
                          cenarios,
                          caminho_saida,
                          logger)
    visualizador.visualiza()

    logger.critical("#### FIM DA EXECUÇÃO ####")


def main_multi():
    logger.critical("#### ESTUDO DE MODELOS DE PLANEJAMENTO ENERGÉTICO ####")
    # Lê os arquivos de configuração de entrada
    entradas = ["./tests/entrada_multi_pl.txt",
                "./tests/entrada_multi_pdde.txt",
                "./tests/entrada_multi_pdde_cvar.txt"]
    resultados: List[Resultado] = []

    for entrada in entradas:
        logger.critical("Arquivo de entrada selecionado: {}".format(entrada))
        e = LeituraEntrada(entrada, logger)
        e.le_arquivo()

        # Determina os método de solução
        metodo = Metodo.obtem_metodo_pelo_valor(e.cfg.metodo)
        resultados.append(metodo.resolve(e, logger))

    for r in resultados:
        print(r.cfg.nome)

    # Gera relatórios e gráficos de saída
    caminho_saida = "results/multi/{}/".format(int(time.time()))
    visualizador = MultiVisual(resultados,
                               caminho_saida,
                               logger)
    visualizador.visualiza()
    logger.critical("#### FIM DA EXECUÇÃO ####")


if __name__ == "__main__":
    ti = time.time()
    main_multi()
    tf = time.time()
    logger.critical("Tempo total de execução: {} s".format(tf - ti))
