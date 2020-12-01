from utils.leituraentrada import LeituraEntrada
from plunico.plunico import PLUnico

import time
import logging
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
        return Metodo.PL_UNICO

    def resolve(self, e: LeituraEntrada, log: logging.Logger):
        """
        Resolve o problema de otimização para o problema descrito,
        segundo o método escolhido.
        """
        log.info("Resolvendo o problema de {}".format(self.value))
        caminho_saida = "results/{}/{}/{}/".format(e.cfg.nome,
                                                   self.value,
                                                   int(time.time()))
        if self == Metodo.PL_UNICO:
            pl = PLUnico(e, log)
            if pl.resolve_pl():
                pl.escreve_saidas(caminho_saida)
        elif self == Metodo.PDDD:
            pass
        elif self == Metodo.PDDE:
            pass
        else:
            pass
