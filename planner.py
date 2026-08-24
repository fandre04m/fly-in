from typing import Dict, List, Tuple, Union
from dataclasses import dataclass
from parser import Hub, Connection
from graph import Graph


def make_conn_name(conn: Connection) -> str:
    return f"{conn.hub_a}-{conn.hub_b}"


class ReservationTable:
    def __init__(self) -> None:
        self.zone_occupancy: Dict[Tuple[str, int], int] = {}
        self.conn_occupancy: Dict[Tuple[str, int], int] = {}

    def has_zone_capacity(self, hub: Hub, turn: int) -> bool:
        if hub.hub_type in {"start_hub", "end_hub"}:
            return True
        current: int = self.zone_occupancy.get((hub.name, turn), 0)
        return current < hub.metadata.max_drones

    def has_link_capacity(self, conn: Connection, turn: int) -> bool:
        key: Tuple[str, int] = (make_conn_name(conn), turn)
        current: int = self.conn_occupancy.get(key, 0)
        return current < conn.metadata.max_link_capacity

    def reserve_zone(self, hub_name: str, turn: int) -> None:
        key: Tuple[str, int] = (hub_name, turn)
        self.zone_occupancy[key] = self.zone_occupancy.get(key, 0) + 1

    def reserve_connection(self, conn_name: str, turn: int) -> None:
        key: Tuple[str, int] = (conn_name, turn)
        self.conn_occupancy[key] = self.conn_occupancy.get(key, 0) + 1


@dataclass(frozen=True)
class AtHub:
    hub_name: str


@dataclass(frozen=True)
class AtConn:
    conn_name: str
    dest: str


Location = Union[AtHub, AtConn]
Node = Tuple[Location, int]


class NeighborGen:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def _neighbors_from_zone(
        self,
        location: AtHub,
        turn: int,
        reserv: ReservationTable
    ) -> List[Node]:
        neighbors: List[Node] = []

        for conn in self.graph.adjacency[location.hub_name]:
            neighbor_name = conn.hub_b if (
                    conn.hub_a == location.hub_name
                ) else conn.hub_a
            neighbor_hub = self.graph.hubs_dict[neighbor_name]

            if neighbor_hub.metadata.zone in {"normal", "priority"}:
                link_ok = reserv.has_link_capacity(conn, turn + 1)
                zone_ok = reserv.has_zone_capacity(neighbor_hub, turn + 1)
                if link_ok and zone_ok:
                    neighbors.append((AtHub(neighbor_name), turn + 1))

            if neighbor_hub.metadata.zone == "restricted":
                link_ok = reserv.has_link_capacity(conn, turn + 1)
                zone_ok = reserv.has_zone_capacity(neighbor_hub, turn + 2)
                if link_ok and zone_ok:
                    conn_name = make_conn_name(conn)
                    neighbors.append(
                        (AtConn(conn_name, neighbor_name), turn + 1)
                    )
        if reserv.has_zone_capacity(
            self.graph.hubs_dict[location.hub_name], turn + 1
        ):
            neighbors.append((AtHub(location.hub_name), turn + 1))

        return neighbors

    def _neighbors_from_conn(
        self,
        location: AtConn,
        turn: int
    ) -> List[Node]:
        return [(AtHub(location.dest), turn + 1)]

    def get_neighbors(
        self,
        node: Node,
        reserv: ReservationTable
    ) -> List[Node]:
        location, turn = node

        if isinstance(location, AtHub):
            return self._neighbors_from_zone(location, turn, reserv)
        return self._neighbors_from_conn(location, turn)
