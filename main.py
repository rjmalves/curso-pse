# from modelos.configgeral import ConfigGeral
from modelos.metodo import Metodo
from utils.leituraentrada import LeituraEntrada

import time
import json
import logging
import coloredlogs  # type: ignore

logger = logging.getLogger(__name__)
coloredlogs.install(logger=logger, level="INFO")


def main():
    logger.critical("#### ESTUDO DE MODELOS DE PLANEJAMENTO ENERGÉTICO ####")
    # Lê as configurações do JSON
    arq = open("./config.json")
    configs = json.load(arq)
    arq.close()
    entrada = configs["arquivoEntrada"]
    metodo = Metodo.obtem_metodo_pelo_valor(configs["metodo"])
    logger.critical("Arquivo de entrada selecionado: {}".format(entrada))
    logger.critical("Método de solução escolhido: {}".format(metodo.value))
    # Lê o arquivo de configuração de entrada
    e = LeituraEntrada(entrada, logger)
    e.le_arquivo()
    # Resolve o problema de otimização
    metodo.resolve(e, logger)
    # Gera relatórios e gráficos de saída
    logger.critical("#### FIM DA EXECUÇÃO ####")


if __name__ == "__main__":
    ti = time.time()
    main()
    tf = time.time()
    logger.critical("Tempo total de execução: {} s".format(tf - ti))
