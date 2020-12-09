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
                 aberturas_cauda: float,
                 peso_cauda: float,
                 intervalo_conf: float,
                 n_pos_estudo: int,
                 custo_deficit: float,
                 n_uhes: int,
                 n_utes: int):
        self.nome = nome
        self.n_periodos = n_periodos
        self.aberturas_periodo = aberturas_periodo
        self.n_cenarios = n_cenarios
        self.aberturas_cauda = aberturas_cauda
        self.peso_cauda = peso_cauda
        self.intervalo_conf = intervalo_conf
        self.n_pos_estudo = n_pos_estudo
        self.custo_deficit = custo_deficit
        self.n_uhes = n_uhes
        self.n_utes = n_utes
        # Inicializa o atributo que indica se é usada aversão
        # a risco no estudo
        self.aversao_risco = False
        if (self.aberturas_cauda > 0 and self.peso_cauda > 0):
            self.aversao_risco = True

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
        return cls("", 0, 0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0, 0)
