class UTE:
    """
    Modelo de uma usina termelétrica em um estudo de
    planejamento energético.
    """
    def __init__(self,
                 ute_id: int,
                 nome: str,
                 capacidade: float,
                 custo: float):
        self.id = ute_id
        self.nome = nome
        self.capacidade = capacidade
        self.custo = custo

    @classmethod
    def le_ute_da_linha(cls, linha: str):
        """
        Processa uma linha do arquivo de entrada e constroi
        o objeto UTE.
        """
        ute_id = int(linha[1:7])
        nome = linha[8:25].strip()
        capacidade = float(linha[26:45])
        custo = float(linha[46:65])
        return cls(ute_id,
                   nome,
                   capacidade,
                   custo)

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {} - ".format(k, v)
        return to_str
