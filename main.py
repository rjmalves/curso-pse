# from modelos.configgeral import ConfigGeral
from modelos.metodo import Metodo
from utils.leituraentrada import LeituraEntrada

import time
import logging
import coloredlogs  # type: ignore

logger = logging.getLogger(__name__)
coloredlogs.install(logger=logger, level="DEBUG")


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
    metodo.resolve(e, logger)
    # Gera relatórios e gráficos de saída
    logger.critical("#### FIM DA EXECUÇÃO ####")


if __name__ == "__main__":
    ti = time.time()
    main()
    tf = time.time()
    logger.critical("Tempo total de execução: {} s".format(tf - ti))
