class UTE:
    def __init__(self,
                 name: str,
                 capacity: float,
                 cost: float):
        self.name = name
        self.capacity = capacity
        self.cost = cost

    @classmethod
    def from_json(cls, json_dict: dict):
        return cls(json_dict["name"],
                   json_dict["capacity"],
                   json_dict["cost"])
