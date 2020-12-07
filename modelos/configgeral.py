class ConfigGeral:
    """
    Configurações gerais para execução de um estudo de
    planejamento energético.
    """
    def __init__(self,
                 nome: str,
                 n_periodos: int,
                 aberturas_periodo: int,
                 n_cenarios: int,
                 n_pos_estudo: int,
                 custo_deficit: float,
                 n_uhes: int,
                 n_utes: int):
        self.nome = nome
        self.n_periodos = n_periodos
        self.aberturas_periodo = aberturas_periodo
        self.n_cenarios = n_cenarios
        self.n_pos_estudo = n_pos_estudo
        self.custo_deficit = custo_deficit
        self.n_uhes = n_uhes
        self.n_utes = n_utes

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {} - ".format(k, v)
        return to_str

    @classmethod
    def default_config(cls):
        """
        Retorna um objeto de configuração vazio.
        """
        return cls("", 0, 0, 0, 0, 0.0, 0, 0)
