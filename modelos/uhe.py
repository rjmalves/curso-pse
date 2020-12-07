class UHE:
    """
    Modelo de uma usina hidrelétrica em um estudo de
    planejamento energético.
    """
    def __init__(self,
                 uhe_id: int,
                 nome: str,
                 vol_inicial: float,
                 vol_minimo: float,
                 vol_maximo: float,
                 produtividade: float,
                 engolimento: float):
        self.id = uhe_id
        self.nome = nome
        self.vol_inicial = vol_inicial
        self.vol_minimo = vol_minimo
        self.vol_maximo = vol_maximo
        self.produtividade = produtividade
        self.engolimento = engolimento


    @classmethod
    def le_uhe_da_linha(cls, linha: str):
        """
        Processa uma linha do arquivo de entrada e constroi
        o objeto UHE.
        """
        uhe_id = int(linha[1:7])
        nome = linha[8:25].strip()
        vol_inicial = float(linha[26:45])
        vol_minimo = float(linha[46:65])
        vol_maximo = float(linha[66:85])
        produtividade = float(linha[86:105])
        engolimento = float(linha[106:125])
        return cls(uhe_id,
                   nome,
                   vol_inicial,
                   vol_minimo,
                   vol_maximo,
                   produtividade,
                   engolimento)

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {} - ".format(k, v)
        return to_str
