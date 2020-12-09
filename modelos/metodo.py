from utils.leituraentrada import LeituraEntrada
from modelos.cenario import Cenario
from modelos.uhe import UHE
from modelos.ute import UTE
from plunico.plunico import PLUnico
from pddd.pddd import PDDD
from pdde.pdde import PDDE

import time
import logging
from typing import List, Tuple
from enum import Enum


class Metodo(Enum):
    """
    Método de estudo adotado para o problema de planejamento
    energético. O método influencia na formulação e na
    complexidade do problema de otimização. Podem ser:

    PL ÚNICO: Problema Linear Único

    PDDD: Programação Dinâmica Dual Determinística

    PDDE: Programação Dinâmica Dual Estocástica
    """
    PL_UNICO = "PL_UNICO"
    PDDD = "PDDD"
    PDDE = "PDDE"

    @classmethod
    def obtem_metodo_pelo_valor(cls, valor: str):
        for k in cls:
            if valor == k.value:
                return k
        # Se não encontrou um dentro dos possíveis
        raise Exception("Método de solução inválido: {}".format(valor))

    def resolve(self,
                e: LeituraEntrada,
                log: logging.Logger) -> List[Cenario]:
        """
        Resolve o problema de otimização para o problema descrito,
        segundo o método escolhido.
        """
        log.info("Resolvendo o problema de {}".format(self.value))
        caminho_saida = "results/{}/{}/{}/".format(e.cfg.nome,
                                                   self.value,
                                                   int(time.time()))
        # Armazena as UHES e UTES existentes
        self.__uhes = e.uhes
        self.__utes = e.utes
        # Resolve o problema e retorna a lista de cenários avaliados
        cen: List[Cenario] = []
        if self == Metodo.PL_UNICO:
            self.pl = PLUnico(e, log)
            cen = self.pl.resolve_pl()
            self.pl.escreve_saidas(caminho_saida)
        elif self == Metodo.PDDD:
            self.pddd = PDDD(e, log)
            cen = self.pddd.resolve_pddd()
            self.pddd.escreve_saidas(caminho_saida)
        elif self == Metodo.PDDE:
            self.pdde = PDDE(e, log)
            cen = self.pdde.resolve_pdde()
            self.pdde.escreve_saidas(caminho_saida)
        else:
            raise Exception("Método de solução inválido")

        return cen

    @property
    def uhes(self) -> List[UHE]:
        return self.__uhes

    @property
    def utes(self) -> List[UTE]:
        return self.__utes

    @property
    def z_sup(self) -> List[float]:
        if self == Metodo.PDDD:
            return self.pddd.z_sup
        elif self == Metodo.PDDE:
            return self.pdde.z_sup
        return []

    @property
    def z_inf(self) -> List[float]:
        if self == Metodo.PDDD:
            return self.pddd.z_inf
        elif self == Metodo.PDDE:
            return self.pdde.z_inf
        return []

    @property
    def intervalo_confianca(self) -> List[Tuple[float, float]]:
        if self == Metodo.PDDE:
            return self.pdde.intervalo_conf
        return []
