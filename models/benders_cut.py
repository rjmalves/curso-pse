from typing import List


class BendersCut:
    def __init__(self,
                 wmc: List[float],
                 offset: float):
        self.wmc = wmc
        self.offset = offset

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {}\n".format(k, v)
        return to_str
