from parser import Hub, Connection, Config
from dataclasses import dataclass
from collections import deque
from typing import Dict, List, Tuple


@dataclass
class Graph:
    hubs_dict: Dict[str, Hub]
    adjacency: Dict[str, List[Connection]]

    @classmethod
    def from_config(cls, config: Config) -> "Graph":
        hubs_dict: Dict[str, Hub] = {hub.name: hub for hub in config.hubs}
        hubs_dict[config.start_hub.name] = config.start_hub
        hubs_dict[config.end_hub.name] = config.end_hub

        adjacency: Dict[str, List[Connection]] = {
            name: [] for name in hubs_dict
        }
        for conn in config.connections:
            adjacency[conn.hub_a].append(conn)
            adjacency[conn.hub_b].append(conn)

        return cls(hubs_dict=hubs_dict, adjacency=adjacency)

    def validate_static_graph(self, start: str, end: str) -> int:
        if self.hubs_dict[end].metadata.zone == "blocked":
            raise ValueError(
                "End hub has matadata 'zone=blocked'."
            )

        visited: set[str] = {start}
        queue: deque[Tuple[str, int]] = deque([(start, 0)])

        while queue:
            curr, dist = queue.popleft()
            if curr == end:
                return dist

            for conn in self.adjacency[curr]:
                neighbor = conn.hub_b if conn.hub_a == curr else conn.hub_a
                if neighbor in visited:
                    continue
                if self.hubs_dict[neighbor].metadata.zone == "blocked":
                    continue
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))

        raise ValueError(
            "End hub not reachable with current graph configuration."
        )
