from .parser import Hub, Connection, Config
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Graph:
    hubs_dict: Dict[str, Hub]
    adjacency: Dict[str, List[Connection]]

    @classmethod
    def from_config(cls, config: Config) -> "Graph":
        hubs_dict = {hub.name: hub for hub in config.hubs}
        hubs_dict[config.start_hub.name] = config.start_hub
        hubs_dict[config.end_hub.name] = config.end_hub

        adjacency = {name: [] for name in hubs_dict}
        for conn in config.connections:
            adjacency[conn.hub_a].append(conn)
            adjacency[conn.hub_b].append(conn)

        return cls(hubs_dict=hubs_dict, adjacency=adjacency)
