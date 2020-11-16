from typing import List


class UHE:
    def __init__(self,
                 name: str,
                 max_volume: float,
                 min_volume: float,
                 productivity: float,
                 swallowing: float,
                 affluents: List[List[float]]):
        self.name = name
        self.max_volume = max_volume
        self.min_volume = min_volume
        self.productivity = productivity
        self.swallowing = swallowing
        self.affluents = affluents

    @classmethod
    def from_json(cls, json_dict: dict):
        return cls(json_dict["name"],
                   json_dict["maxVolume"],
                   json_dict["minVolume"],
                   json_dict["productivity"],
                   json_dict["swallowing"],
                   json_dict["affluents"])
