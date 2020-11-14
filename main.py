from typing import List
import time
from models.uhe import UHE
from models.ute import UTE
from models.general_data import GeneralData
from models.system import System


def main():
    lista_uhe: List[UHE] = []
    lista_uhe.append(UHE("UHE DO MARCATO",
                         100.,
                         20.,
                         0.95,
                         60.,
                         [
                             [23., 16.],
                             [19., 14.],
                             [15., 11.]
                         ]))
    # lista_uhe.append(UHE("UHE DO VASCAO",
    #                      200.,
    #                      40.,
    #                      0.85,
    #                      100.,
    #                      [
    #                          [46., 32.],
    #                          [38., 28.],
    #                          [30., 22.]
    #                      ]))

    lista_ute: List[UTE] = []
    lista_ute.append(UTE("GT_1",
                         15.,
                         10.))
    lista_ute.append(UTE("GT_2",
                         10.,
                         25.))

    dgerais = GeneralData(500., [50., 50., 50.], 15, 3, 2)

    s = System(dgerais, lista_uhe, lista_ute)
    s.generateStates(0)
    s.dispatch()


if __name__ == "__main__":
    ti = time.time()
    main()
    tf = time.time()
    print("Tempo de execução: {}".format(tf - ti))
