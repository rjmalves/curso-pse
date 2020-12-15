from utils.leituraentrada import LeituraEntrada
from modelos.resultado import Resultado
from plunico.plunico import PLUnico
from pddd.pddd import PDDD
from pdde.pdde import PDDE

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
    def obtem_metodo_pelo_nome(cls, valor: str):
        for k in cls:
            if valor == k.value:
                return k
        # Se não encontrou um dentro dos possíveis
        raise Exception("Método de solução inválido: {}".format(valor))

    def resolve(self,
                e: LeituraEntrada,
                LOG_LEVEL: str) -> Resultado:
        """
        Resolve o problema de otimização para o problema descrito,
        segundo o método escolhido.
        """
        # Armazena as UHES e UTES existentes
        self.__uhes = e.uhes
        self.__utes = e.utes
        # Resolve o problema e retorna a lista de cenários avaliados
        r: Resultado = Resultado(e.cfg, [], [], [], [], [], [], [])
        if self == Metodo.PL_UNICO:
            self.pl = PLUnico(e, LOG_LEVEL)
            r = self.pl.resolve_pl()
        elif self == Metodo.PDDD:
            self.pddd = PDDD(e, LOG_LEVEL)
            r = self.pddd.resolve_pddd()
        elif self == Metodo.PDDE:
            self.pdde = PDDE(e, LOG_LEVEL)
            r = self.pdde.resolve_pdde()
        else:
            raise Exception("Método de solução inválido")

        return r
