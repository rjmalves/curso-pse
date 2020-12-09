from modelos.cenario import Cenario
from modelos.uhe import UHE
from modelos.ute import UTE
from modelos.configgeral import ConfigGeral

import os
import logging
from traceback import print_exc
from typing import List, IO


class EscreveSaida:
    """
    """
    def __init__(self,
                 cfg: ConfigGeral,
                 uhes: List[UHE],
                 utes: List[UTE],
                 caminho: str,
                 cenarios: List[Cenario],
                 log: logging.Logger):
        self.cfg = cfg
        self.uhes = uhes
        self.utes = utes
        self.caminho = caminho
        self.cenarios = cenarios
        self.log = log

    def escreve_relatorio(self, custo: float):
        """
        Gera o relatório de saída em formato de arquivo de texto.
        """
        # Se o diretório para o relatório não existe, cria
        if not os.path.exists(self.caminho):
            os.makedirs(self.caminho)
        try:
            with open(self.caminho + "saida.txt", "w") as arquivo:
                titulo = "RELATÓRIO DE ESTUDO DE PLANEJAMENTO ENERGÉTICO"
                arquivo.write(titulo + "\n\n")
                self.__escreve_configs(arquivo)
                metodo = "PL ÚNICO".rjust(18)
                arquivo.write("MÉTODO UTILIZADO: {}\n".format(metodo))
                arquivo.write("FUNÇÃO OBJETIVO: {:19.4f}\n\n".format(custo))
                # Escreve o relatório detalhado por cenário
                for i, cen in enumerate(self.cenarios):
                    str_cen = str(i + 1).rjust(4)
                    arquivo.write("CENÁRIO " + str_cen + "\n")
                    self.__escreve_cenario(arquivo, cen)
                pass
        except Exception as e:
            self.log.error("Falha na escrita do arquivo: {}".format(e))
            print_exc()

    def __escreve_configs(self, arquivo: IO):
        """
        Escreve informações sobre um cenário no relatório de saída.
        """
        titulo = "CONFIGURAÇÕES UTILIZADAS NO ESTUDO"
        arquivo.write(titulo + "\n")
        self.__escreve_borda_tabela(arquivo, [27, 15])
        self.__escreve_linha_config(arquivo,
                                    "NOME DO ESTUDO",
                                    self.cfg.nome)
        self.__escreve_linha_config(arquivo,
                                    "NÚMERO DE PERÍODOS",
                                    str(self.cfg.n_periodos))
        self.__escreve_linha_config(arquivo,
                                    "ABERTURAS POR PERÍODO",
                                    str(self.cfg.aberturas_periodo))
        self.__escreve_linha_config(arquivo,
                                    "PERÍODOS PÓS ESTUDO",
                                    str(self.cfg.n_pos_estudo))
        self.__escreve_linha_config(arquivo,
                                    "CUSTO DE DÉFICIT ($/MWmed)",
                                    str(self.cfg.custo_deficit))
        self.__escreve_linha_config(arquivo,
                                    "NÚMERO DE HIDRELÉTRICAS",
                                    str(self.cfg.n_uhes))
        self.__escreve_linha_config(arquivo,
                                    "NÚMERO DE TERMELÉTRICAS",
                                    str(self.cfg.n_utes))
        self.__escreve_borda_tabela(arquivo, [27, 15])
        arquivo.write("\n")
        pass

    def __escreve_linha_config(self,
                               arquivo: IO,
                               str_atributo: str,
                               atributo: str):
        """
        Escreve uma linha de atributo na tabela de configurações gerais,
        justificando adequadamente.
        """
        chave = " " + str_atributo.ljust(27)
        valor = atributo.rjust(15)
        arquivo.write(chave + " " + valor + "\n")

    def __escreve_cenario(self, arquivo: IO, cenario: Cenario):
        """
        Escreve informações sobre um cenário no relatório de saída.
        """
        # Calcula os campos existentes com base no número de UHE e UTE
        campos = [13] + [19] * (5 * len(self.uhes) + len(self.utes) + 2)
        self.__escreve_borda_tabela(arquivo, campos)
        # Escreve o cabeçalho da tabela
        cab_tabela = "    PERÍODO    "
        for i in range(len(self.uhes)):
            ind_uhe = str(i + 1).ljust(2)
            cab_tabela += "      AFL({})       ".format(ind_uhe)
            cab_tabela += "      VF({})        ".format(ind_uhe)
            cab_tabela += "      VT({})        ".format(ind_uhe)
            cab_tabela += "      VV({})        ".format(ind_uhe)
            cab_tabela += "      CMA({})       ".format(ind_uhe)
        for i in range(len(self.utes)):
            ind_ute = str(i + 1).ljust(2)
            cab_tabela += "      GT({})        ".format(ind_ute)
        cab_tabela += "      DEFICIT       "
        cab_tabela += "        CMO         "
        arquivo.write(cab_tabela + "\n")
        # Escreve as linhas com dados numéricos
        linhas_cenario = cenario.linhas_tabela()
        for linha in linhas_cenario:
            arquivo.write(linha)
        self.__escreve_borda_tabela(arquivo, campos)

    def __escreve_borda_tabela(self, arquivo: IO, campos: List[int]):
        """
        Escreve uma linha que significa borda de tabela no arquivo, com
        campos cujos números de caracteres são fornecidos.
        """
        str_linha = "X"
        for c in campos:
            str_linha += "-" * c + "X"
        arquivo.write(str_linha + "\n")
