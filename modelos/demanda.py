class Demanda:
    """
    Representa uma demanda existente de energia em
    um determinado período de estudo.
    """
    def __init__(self,
                 periodo: int,
                 demanda: float):
        self.periodo = periodo
        self.demanda = demanda

    @classmethod
    def obtem_demanda_de_linha(cls, linha: str):
        """
        Constroi um objeto demanda a partir de uma linha
        de um arquivo de entrada (.txt).
        """
        periodo = int(linha[2:14])
        demanda = float(linha[15:34])
        return cls(periodo, demanda)

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {} - ".format(k, v)
        return to_str
