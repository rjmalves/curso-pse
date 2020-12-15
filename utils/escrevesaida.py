from modelos.cenario import Cenario
from modelos.resultado import Resultado
from modelos.uhe import UHE
from modelos.ute import UTE

import os
import logging
import coloredlogs  # type: ignore
from traceback import print_exc
from typing import List, IO
logger = logging.getLogger(__name__)


class EscreveSaida:
    """
    """
    def __init__(self,
                 resultado: Resultado,
                 caminho: str,
                 LOG_LEVEL: str):
        self.cfg = resultado.cfg
        self.uhes: List[UHE] = resultado.uhes
        self.utes: List[UTE] = resultado.utes
        self.metodo: str = resultado.cfg.metodo
        self.caminho = caminho
        self.cenarios = resultado.cenarios
        self.z_sup = resultado.z_sup
        self.z_inf = resultado.z_inf
        self.intervalo_conf = resultado.intervalo_confianca
        self.log = logger
        coloredlogs.install(logger=logger, level=LOG_LEVEL)

    def escreve_relatorio(self):
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
                metodo = "{}".format(self.metodo).rjust(18)
                arquivo.write("MÉTODO UTILIZADO: {}\n\n".format(metodo))
                if self.metodo == "PL_UNICO":
                    arquivo.write("VALOR DA FUNC. OBJ:      {:12.4f}\n\n"
                                  .format(self.cenarios[0].fobj[0]))
                if self.metodo == "PDDD" or self.metodo == "PDDE":
                    # Escreve o relatório de convegência
                    self.__escreve_convergencia(arquivo)
                # Escreve o relatório do cenário médio avaliado
                self.__escreve_cenario_medio(arquivo)
                # Escreve o relatório detalhado por cenário
                arquivo.write("RELATÓRIO DE CENÁRIOS DETALHADOS\n\n")
                for i, cen in enumerate(self.cenarios):
                    str_cen = str(i + 1).rjust(4)
                    arquivo.write("CENÁRIO " + str_cen + "\n")
                    self.__escreve_cenario(arquivo, cen)
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
                                    "NÚMERO DE CENÁRIOS",
                                    str(self.cfg.n_cenarios))
        self.__escreve_linha_config(arquivo,
                                    "% ABERTURAS CAUDA (ALFA)",
                                    str(self.cfg.aberturas_cauda))
        self.__escreve_linha_config(arquivo,
                                    "PESO CAUDA (LAMBDA)",
                                    str(self.cfg.peso_cauda))
        self.__escreve_linha_config(arquivo,
                                    "INTERVALO CONF (Nº DESVIOS)",
                                    str(self.cfg.intervalo_conf))
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

    def __escreve_convergencia(self, arquivo: IO):
        """
        Escreve os valores assumidos pelos Z_sup e Z_inf a cada iteração,
        bem como o erro (diferença).
        """
        arquivo.write("RELATÓRIO DE CONVERGÊNCIA\n\n")
        campos = [13, 19, 19]
        # Escreve o cabeçalho
        cab_tabela = "     ITER.     "
        cab_tabela += "       Z_SUP        "
        cab_tabela += "       Z_INF        "
        if self.metodo == "PDDE":
            campos += [19, 19]
            cab_tabela += " LIMITE INF. CONF.  "
            cab_tabela += " LIMITE SUP. CONF.  "
        self.__escreve_borda_tabela(arquivo, campos)
        arquivo.write(cab_tabela + "\n")
        # Escreve as linhas com as entradas para cada iteração
        n_iters = len(self.z_sup)
        for i in range(n_iters):
            linha = " "
            ind_iter = str(i + 1).rjust(13)
            linha += ind_iter + " "
            linha += "{:19.8f}".format(self.z_sup[i]) + " "
            linha += "{:19.8f}".format(self.z_inf[i]) + " "
            if i == n_iters - 1:
                linha += "    # RESULTADO DA SIMULAÇÃO FINAL"
            linha += "\n"
            arquivo.write(linha)
        self.__escreve_borda_tabela(arquivo, campos)
        arquivo.write("\n")

    def __escreve_cenario(self, arquivo: IO, cenario: Cenario):
        """
        Escreve informações sobre um cenário no relatório de saída.
        """
        # Calcula os campos existentes com base no número de UHE e UTE
        campos = [13] + [19] * (5 * len(self.uhes) + len(self.utes) + 5)
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
        cab_tabela += "   CUSTO IMEDIATO   "
        cab_tabela += "    CUSTO FUTURO    "
        cab_tabela += "    CUSTO TOTAL     "
        arquivo.write(cab_tabela + "\n")
        # Escreve as linhas com dados numéricos
        linhas_cenario = cenario.linhas_tabela()
        for linha in linhas_cenario:
            arquivo.write(linha)
        self.__escreve_borda_tabela(arquivo, campos)

    def __escreve_cenario_medio(self, arquivo: IO):
        """
        Escreve informações sobre os cenários médios no relatório de saída.
        """
        arquivo.write("RELATÓRIO DE CENÁRIOS MÉDIOS\n\n")
        # Calcula os campos existentes com base no número de UHE e UTE
        campos = [13] + [19] * (5 * len(self.uhes) + len(self.utes) + 5)
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
        cab_tabela += "   CUSTO IMEDIATO   "
        cab_tabela += "    CUSTO FUTURO    "
        cab_tabela += "    CUSTO TOTAL     "
        arquivo.write(cab_tabela + "\n")
        # Constroi o cenário médio
        cenario_medio = Cenario.cenario_medio(self.cenarios)
        # Escreve as linhas com dados numéricos
        linhas_cenario = cenario_medio.linhas_tabela()
        for linha in linhas_cenario:
            arquivo.write(linha)
        self.__escreve_borda_tabela(arquivo, campos)
        arquivo.write("\n")

    def __escreve_borda_tabela(self, arquivo: IO, campos: List[int]):
        """
        Escreve uma linha que significa borda de tabela no arquivo, com
        campos cujos números de caracteres são fornecidos.
        """
        str_linha = "X"
        for c in campos:
            str_linha += "-" * c + "X"
        arquivo.write(str_linha + "\n")
