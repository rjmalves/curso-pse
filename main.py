# from modelos.configgeral import ConfigGeral
from modelos.metodo import Metodo
from modelos.resultado import Resultado
from utils.leituraentrada import LeituraEntrada
from utils.visual import Visual
from utils.multivisual import MultiVisual
from utils.escrevesaida import EscreveSaida

import os
import time
import logging
import argparse
from typing import List
import coloredlogs  # type: ignore

logger = logging.getLogger(__name__)
LOG_LEVEL = "CRITICAL"


def main():
    # Configura a interface de chamada do programa via linha de
    # comando (CLI)
    str_descrip = ("Realiza um estudo de Planejamento Energético " +
                   "a partir de arquivos de entrada tabulares.\n")
    parser = argparse.ArgumentParser(description=str_descrip)
    parser.add_argument("entradas",
                        type=str,
                        nargs="+",
                        help="lista de caminhos relativos das entradas")
    parser.add_argument("-l", "--log",
                        dest="l",
                        type=str,
                        default="INFO",
                        help="nível de logging desejado ao executar")
    parser.add_argument("-s", "--saida",
                        dest="s",
                        type=str,
                        default="results/",
                        help="diretorio raiz dos arquivos de saída")
    # Extrai os parâmetros fornecidos para a execução do programa
    args = parser.parse_args()
    if args.l not in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]:
        raise Exception("Nível de LOG fornecido inválido")

    # Atualiza o nível de LOG desejado
    global LOG_LEVEL
    LOG_LEVEL = args.l
    coloredlogs.install(logger=logger, level=args.l)

    # Inicia a execução
    logger.info("#### ESTUDO DE MODELOS DE PLANEJAMENTO ENERGÉTICO ####")
    resultados: List[Resultado] = []
    for entrada in args.entradas:

        e = LeituraEntrada(entrada, LOG_LEVEL)
        e.le_arquivo()
        # Determina o método de solução
        metodo = Metodo.obtem_metodo_pelo_nome(e.cfg.metodo)
        resultados.append(metodo.resolve(e, LOG_LEVEL))

    # Gera relatórios e gráficos de saída
    for resultado in resultados:
        caminho_saida = os.path.join(args.s,
                                     "{}/{}/".format(resultado.cfg.nome,
                                                     int(time.time())))
        relator = EscreveSaida(resultado,
                               caminho_saida,
                               LOG_LEVEL)
        relator.escreve_relatorio()
        visualizador = Visual(resultado,
                              caminho_saida,
                              LOG_LEVEL)
        visualizador.visualiza()
    caminho_saida = os.path.join(args.s,
                                 "multi/{}/".format(int(time.time())))
    visualizador = MultiVisual(resultados,
                               caminho_saida,
                               LOG_LEVEL)
    visualizador.visualiza()
    logger.info("#### FIM DA EXECUÇÃO ####")


if __name__ == "__main__":
    ti = time.time()
    main()
    tf = time.time()
    logger.critical("Tempo total de execução: {} s".format(tf - ti))
