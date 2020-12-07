from typing import List


class UHE:
    def __init__(self,
                 name: str,
                 initial_volume: float,
                 max_volume: float,
                 min_volume: float,
                 productivity: float,
                 swallowing: float,
                 affluents: List[List[float]]):
        self.name = name
        self.initial_volume = initial_volume
        self.volume = initial_volume
        self.max_volume = max_volume
        self.min_volume = min_volume
        self.productivity = productivity
        self.swallowing = swallowing
        self.affluents = affluents

    @classmethod
    def from_json(cls, json_dict: dict):
        return cls(json_dict["name"],
                   json_dict["initialVolume"],
                   json_dict["maxVolume"],
                   json_dict["minVolume"],
                   json_dict["productivity"],
                   json_dict["swallowing"],
                   json_dict["affluents"])

    def __str__(self):
        to_str = ""
        for k, v in self.__dict__.items():
            to_str += "{}: {}\n".format(k, v)
        return to_str
