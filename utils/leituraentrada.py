from modelos.configgeral import ConfigGeral
from modelos.demanda import Demanda
from modelos.uhe import UHE
from modelos.ute import UTE

from typing import IO, List, Dict
from traceback import print_exc
import logging
import coloredlogs  # type: ignore
logger = logging.getLogger(__name__)


class LeituraEntrada:
    """
    Conjunto de utilidades para leitura dos dados de entrada a serem
    utilizados na execução de um estudo de PL único.
    """
    inicio_cfg_gerais = "CONFIGURAÇÕES GERAIS DE EXECUÇÃO"
    inicio_demanda = "VALORES DE DEMANDA ESPERADAS NOS PERÍODOS"
    inicio_uhe = "PARÂMETROS DAS USINAS HIDRELÉTRICAS"
    inicio_ute = "PARÂMETROS DAS USINAS TERMELÉTRICAS"
    inicio_afluencias = "CENÁRIOS DE AFLUÊNCIAS POR HIDRELÉTRICA"
    fim_tabela = "X---"
    afluencias_por_periodo = 5

    def __init__(self,
                 caminho: str,
                 LOG_LEVEL: str):
        self.caminho = caminho
        self.metodo = ""
        coloredlogs.install(logger=logger, level=LOG_LEVEL)
        self.cfg: ConfigGeral = ConfigGeral.default_config()
        self.demandas: List[Demanda] = []
        self.uhes: List[UHE] = []
        self.utes: List[UTE] = []
        # Afluências estão salvas num dict com:
        # chave = id da UHE
        # valor = lista de listas de valores em hm3.
        # As listas são uma para cada período, sendo que
        # cada elemento é uma afluências possível
        self.afluencias: Dict[int, List[List[float]]] = {}
        # Atributos auxiliares para leitura
        self.usa_backup = False
        self.backup_linha = ""

    def le_arquivo(self):
        """
        Varre o arquivo de entrada (.txt), buscando os parâmetros
        que descrevem o estudo a ser realizado.
        """
        logger.info("# INICIANDO A LEITURA DO ARQUIVO: {} #".
                    format(self.caminho))
        logger.info("---------------------------------------")
        try:
            with open(self.caminho, "r") as arquivo:
                # Lê as configurações gerais
                self.cfg = self.__le_configs_gerais(arquivo)
                # Lê as demandas esperadas
                self.demandas = self.__le_demandas(arquivo)
                # Lê os parâmetros das hidrelétricas
                self.uhes = self.__le_parametros_hidreletricas(arquivo)
                # Lê os parâmetros das termelétricas
                self.utes = self.__le_parametros_termeletricas(arquivo)
                # Lê os cenários de afluências por período
                self.afluencias = self.__le_afluencias(arquivo)
            logger.info("---------------------------------------")
            logger.info("# FIM DA LEITURA #")
            logger.info("----------------------------------------")
        except Exception as e:
            logger.error("Erro na leitura do arquivo: {}".format(e))
            print_exc()

    def __le_configs_gerais(self, arquivo: IO) -> ConfigGeral:
        """
        Varre as linhas do arquivo de entrada, construindo o
        objeto de configurações gerais.
        """
        iniciou = False
        linha = ""
        while True:
            # Procura pelo início da tabela de configurações gerais
            if not iniciou:
                linha = self.__le_linha_com_backup(arquivo)
                iniciou = self.__inicio_configs_gerais(linha)
                continue
            # Quando achar, pula uma linha
            self.__le_linha_com_backup(arquivo)
            # Lê o arquivo linha a linha
            ci = 29
            cf = 44
            logger.info("Lendo Configurações Gerais....")
            logger.debug("X---------------------------X--------------X")
            nome = self.__le_linha_com_backup(arquivo)[ci:cf].strip()
            metodo = self.__le_linha_com_backup(arquivo)[ci:cf].strip()
            min_iters = int(self.__le_linha_com_backup(arquivo)[ci:cf])
            max_iters = int(self.__le_linha_com_backup(arquivo)[ci:cf])
            n_estagios = int(self.__le_linha_com_backup(arquivo)[ci:cf])
            n_aberturas = int(self.__le_linha_com_backup(arquivo)[ci:cf])
            n_cenarios = int(self.__le_linha_com_backup(arquivo)[ci:cf])
            aberturas_cauda = float(self.__le_linha_com_backup(arquivo)[ci:cf])
            peso_cauda = float(self.__le_linha_com_backup(arquivo)[ci:cf])
            intervalo_conf = float(self.__le_linha_com_backup(arquivo)[ci:cf])
            semente = int(self.__le_linha_com_backup(arquivo)[ci:cf])
            reamostrar = bool(int(self.__le_linha_com_backup(arquivo)[ci:cf]))
            n_pos_est = int(self.__le_linha_com_backup(arquivo)[ci:cf])
            custo_def = float(self.__le_linha_com_backup(arquivo)[ci:cf])
            n_uhe = int(self.__le_linha_com_backup(arquivo)[ci:cf])
            n_ute = int(self.__le_linha_com_backup(arquivo)[ci:cf])
            # Realiza o logging dos atributos lidos
            logger.debug(" NOME DO ESTUDO".ljust(27) + nome.rjust(15))
            logger.debug(" MÉTODO DE SOLUÇÃO".ljust(27) + metodo.rjust(15))
            if metodo != "PL_UNICO":
                logger.debug(" MIN. ITERAÇÕES".ljust(27) +
                             str(min_iters).rjust(15))
                logger.debug(" MAX. ITERAÇÕES".ljust(27) +
                             str(max_iters).rjust(15))
            logger.debug(" NÚMERO DE PERÍODOS".ljust(27) +
                         str(n_estagios).rjust(15))
            logger.debug(" ABERTURAS POR PERÍODO".ljust(27)
                         + str(n_aberturas).rjust(15))
            if metodo == "PDDE":
                logger.debug(" NÚMERO DE CENARIOS FWD".ljust(27) +
                             str(n_cenarios).rjust(15))
                if aberturas_cauda > 0 or peso_cauda > 0:
                    logger.debug(" --- AVERSÃO A RISCO >> HABILITADA << ---")
                    logger.debug("ALFA = {:4.2f}    LAMBDA = {:4.2f}".
                                 format(aberturas_cauda, peso_cauda))
                if reamostrar:
                    logger.debug("  --- REAMOSTRAGEM >> HABILITADA << ---")
            logger.debug(" NÚMERO DE HIDRELÉTRICAS".ljust(27) +
                         str(n_uhe).rjust(15))
            logger.debug(" NÚMERO DE TERMELÉTRICAS".ljust(27) +
                         str(n_ute).rjust(15))
            logger.debug("X---------------------------X--------------X")
            # Constroi o objeto de configurações gerais
            cfg = ConfigGeral(nome,
                              metodo,
                              min_iters,
                              max_iters,
                              n_estagios,
                              n_aberturas,
                              n_cenarios,
                              aberturas_cauda,
                              peso_cauda,
                              intervalo_conf,
                              semente,
                              reamostrar,
                              n_pos_est,
                              custo_def,
                              n_uhe,
                              n_ute)
            return cfg

    def __le_demandas(self, arquivo: IO) -> List[Demanda]:
        """
        Varre as linhas do arquivo de entrada, construindo a lista
        de demandas existentes em cada período de estudo.
        """
        iniciou = False
        linha = ""
        while True:
            # Procura pelo início da tabela de demandas
            if not iniciou:
                linha = self.__le_linha_com_backup(arquivo)
                iniciou = self.__inicio_demandas(linha)
                continue
            # Quando achar, pula duas linhas
            self.__le_linha_com_backup(arquivo)
            self.__le_linha_com_backup(arquivo)
            # Lê o arquivo linha a linha
            logger.info("Lendo Demandas....")
            logger.debug("X-------------X-------------------X")
            demandas: List[Demanda] = []
            for i in range(self.cfg.n_periodos):
                linha = self.__le_linha_com_backup(arquivo)
                d = Demanda.obtem_demanda_de_linha(linha)
                logger.debug(str(d.periodo).rjust(13)
                             + "  " + str(d.demanda).rjust(19))
                demandas.append(d)
            logger.debug("X-------------X-------------------X")
            return demandas

    def __le_parametros_hidreletricas(self, arquivo: IO) -> List[UHE]:
        """
        Varre as linhas do arquivo de entrada, construindo os objetos
        das usinas hidrelétricas existentes no sistema.
        """
        iniciou = False
        linha = ""
        while True:
            # Procura pelo início da tabela de UHEs
            if not iniciou:
                linha = self.__le_linha_com_backup(arquivo)
                iniciou = self.__inicio_hidreletricas(linha)
                continue
            # Quando achar, pula duas linhas
            self.__le_linha_com_backup(arquivo)
            self.__le_linha_com_backup(arquivo)
            # Lê o arquivo linha a linha
            logger.info("Lendo Parâmetros das UHEs....")
            uhes: List[UHE] = []
            for i in range(self.cfg.n_uhes):
                linha = self.__le_linha_com_backup(arquivo)
                uhe = UHE.le_uhe_da_linha(linha)
                logger.debug("                 UHE {}".format(uhe.id))
                logger.debug("X-------------------X-----------------X")
                logger.debug(" NOME              "
                             + str(uhe.nome).rjust(19))
                logger.debug(" VOL. INICIAL (hm3)"
                             + str(uhe.vol_inicial).rjust(19))
                logger.debug(" VOL. MÍNIMO (hm3) "
                             + str(uhe.vol_minimo).rjust(19))
                logger.debug(" VOL. MÁXIMO (hm3) "
                             + str(uhe.vol_maximo).rjust(19))
                logger.debug(" PROD. (MWmed/hm3) "
                             + str(uhe.produtividade).rjust(19))
                logger.debug(" ENGOL. MÁXIMO (hm3)"
                             + str(uhe.engolimento).rjust(18))
                logger.debug("X-------------------X-----------------X")
                uhes.append(uhe)
            return uhes

    def __le_parametros_termeletricas(self, arquivo: IO):
        """
        Varre as linhas do arquivo de entrada, construindo os objetos
        das usinas termelétricas existentes no sistema.
        """
        iniciou = False
        linha = ""
        while True:
            # Procura pelo início da tabela de UTEs
            if not iniciou:
                linha = self.__le_linha_com_backup(arquivo)
                iniciou = self.__inicio_termeletricas(linha)
                continue
            # Quando achar, pula duas linhas
            self.__le_linha_com_backup(arquivo)
            self.__le_linha_com_backup(arquivo)
            # Lê o arquivo linha a linha
            logger.info("Lendo Parâmetros das UTEs....")
            utes: List[UTE] = []
            for i in range(self.cfg.n_utes):
                linha = self.__le_linha_com_backup(arquivo)
                ute = UTE.le_ute_da_linha(linha)
                logger.debug("                 UTE {}".format(ute.id))
                logger.debug("X-------------------X-----------------X")
                logger.debug(" NOME              "
                             + str(ute.nome).rjust(19))
                logger.debug(" CAPACIDADE (MWmed)"
                             + str(ute.capacidade).rjust(19))
                logger.debug(" CUSTO ($/MWmed)   "
                             + str(ute.custo).rjust(19))
                logger.debug("X-------------------X-----------------X")
                utes.append(ute)
            return utes

    def __le_afluencias(self, arquivo: IO) -> Dict[int, List[List[float]]]:
        """
        Varre as linhas do arquivo de entrada, construindo os objetos
        das usinas hidrelétricas existentes no sistema.
        """
        iniciou = False
        linha = ""
        while True:
            # Procura pelo início da tabela de afluências
            if not iniciou:
                linha = self.__le_linha_com_backup(arquivo)
                iniciou = self.__inicio_afluencias(linha)
                continue
            # Quando achar, pula três linhas
            self.__le_linha_com_backup(arquivo)
            self.__le_linha_com_backup(arquivo)
            self.__le_linha_com_backup(arquivo)
            # Lê o arquivo linha a linha
            logger.info("Lendo Afluências....")
            afluencias: Dict[int, List[List[float]]] = {}
            for i in range(self.cfg.n_uhes):
                # Procura pelo começo das afluências da UHE
                while True:
                    linha = self.__le_linha_com_backup(arquivo)
                    if linha[1:7] != "      ":
                        self.usa_backup = True
                        self.backup_linha = linha
                        break
                # Identifica a UHE
                linha = self.__le_linha_com_backup(arquivo)
                self.usa_backup = True
                self.backup_linha = linha
                uhe_id = int(linha[1:7])
                # Para cada UHE, são esperadas tantas linhas
                # quanto períodos
                afluencias_uhe: Dict[int, List[float]] = {}
                for j in range(self.cfg.n_periodos):
                    # Lê na forma de dicionário, depois transforma em
                    # lista, ordenando adequadamente
                    linha = self.__le_linha_com_backup(arquivo)
                    periodo = int(linha[8:21])
                    afluencias_uhe[periodo] = []
                    ini_afl = 22
                    len_afl = 19
                    for k in range(LeituraEntrada.afluencias_por_periodo):
                        fim_afl = ini_afl + len_afl
                        afl = float(linha[ini_afl:fim_afl])
                        afluencias_uhe[periodo].append(afl)
                        ini_afl = fim_afl + 1
                # Converte o dicionário para lista, ordenando pela chave
                chaves_ordenadas = sorted(afluencias_uhe.keys())
                afluencias[uhe_id] = [afluencias_uhe[c]
                                      for c in chaves_ordenadas]
            return afluencias

    def __inicio_configs_gerais(self, linha: str) -> bool:
        """
        Verifica se uma linha contém o texto que indica a parte de
        configurações gerais no arquivo de entrada.
        """
        return LeituraEntrada.inicio_cfg_gerais in linha

    def __inicio_demandas(self, linha: str) -> bool:
        """
        Verifica se uma linha contém o texto que indica a parte de
        demandas no arquivo de entrada.
        """
        return LeituraEntrada.inicio_demanda in linha

    def __inicio_hidreletricas(self, linha: str) -> bool:
        """
        Verifica se uma linha contém o texto que indica a parte de
        parâmetros das hidrelétricas no arquivo de entrada.
        """
        return LeituraEntrada.inicio_uhe in linha

    def __inicio_termeletricas(self, linha: str) -> bool:
        """
        Verifica se uma linha contém o texto que indica a parte de
        parâmetros das termelétricas no arquivo de entrada.
        """
        return LeituraEntrada.inicio_ute in linha

    def __inicio_afluencias(self, linha: str) -> bool:
        """
        Verifica se uma linha contém o texto que indica a parte de
        afluências no arquivo de entrada.
        """
        return LeituraEntrada.inicio_afluencias in linha

    def __fim_tabela(self, linha: str) -> bool:
        """
        Verifica se uma linha é o fim de uma tabela.
        """
        return LeituraEntrada.fim_tabela in linha

    def __le_linha_com_backup(self, arquivo: IO) -> str:
        """
        Faz uma leitura de linha de um arquivo, mas com a opção de usar
        um backup de leitura anterior sinalizado anteriormente.
        """
        linha = ""
        if self.usa_backup:
            self.usa_backup = False
            linha = self.backup_linha
        else:
            linha = arquivo.readline()
        return linha
