from typing import List


class UHE:
    def __init__(self,
                 name: str,
                 maxVolume: float,
                 minVolume: float,
                 productivity: float,
                 swallowing: float,
                 affluents: List[List[float]]):
        self.name = name
        self.maxVolume = maxVolume
        self.minVolume = minVolume
        self.productivity = productivity
        self.swallowing = swallowing
        self.affluents = affluents
