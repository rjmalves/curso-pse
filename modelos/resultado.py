from modelos.cenario import Cenario
from modelos.configgeral import ConfigGeral
from modelos.cortebenders import CorteBenders
from modelos.uhe import UHE
from modelos.ute import UTE

from typing import List, Tuple


class Resultado:
    """
    Armazena o resultado de execução de um método de
    solução para o problema de despacho, guardando algumas das
    configurações que foram feitas.
    """
    def __init__(self,
                 cfg: ConfigGeral,
                 uhes: List[UHE],
                 utes: List[UTE],
                 cenarios: List[Cenario],
                 z_sup: List[float],
                 z_inf: List[float],
                 intervalo_conf: List[Tuple[float, float]],
                 cortes: List[List[List[CorteBenders]]]):

        self.cfg = cfg
        self.uhes = uhes
        self.utes = utes
        self.cenarios = cenarios
        self.z_sup = z_sup
        self.z_inf = z_inf
        self.intervalo_confianca = intervalo_conf
        self.cortes = cortes
