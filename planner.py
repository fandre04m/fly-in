from typing import Dict, List, Tuple, Union
from dataclasses import dataclass
from parser import Hub, Connection
from graph import Graph


def make_conn_name(conn: Connection) -> str:
    """Create the stored name for a connection.

    Args:
        conn: Connection whose endpoint names should be joined.

    Returns:
        The connection name in ``hub_a-hub_b`` form.
    """
    return f"{conn.hub_a}-{conn.hub_b}"


class ReservationTable:
    """Track zone and connection reservations by turn."""

    def __init__(self) -> None:
        """Initialize empty zone and connection reservations.

        Returns:
            None.
        """
        self.zone_occupancy: Dict[Tuple[str, int], int] = {}
        self.conn_occupancy: Dict[Tuple[str, int], int] = {}

    def has_zone_capacity(self, hub: Hub, turn: int) -> bool:
        """Check whether a hub can accept another drone at a turn.

        Args:
            hub: Hub whose capacity should be checked.
            turn: Turn when the hub would be occupied.

        Returns:
            True when the hub has available capacity.
        """
        if hub.hub_type in {"start_hub", "end_hub"}:
            return True
        current: int = self.zone_occupancy.get((hub.name, turn), 0)
        return current < hub.metadata.max_drones

    def has_link_capacity(self, conn: Connection, turn: int) -> bool:
        """Check whether a connection can accept another drone at a turn.

        Args:
            conn: Connection whose capacity should be checked.
            turn: Turn when the connection would be used.

        Returns:
            True when the connection has available capacity.
        """
        key: Tuple[str, int] = (make_conn_name(conn), turn)
        current: int = self.conn_occupancy.get(key, 0)
        return current < conn.metadata.max_link_capacity

    def reserve_zone(self, hub_name: str, turn: int) -> None:
        """Reserve one place in a hub for a turn.

        Args:
            hub_name: Name of the hub to reserve.
            turn: Turn when the hub is occupied.

        Returns:
            None.
        """
        key: Tuple[str, int] = (hub_name, turn)
        self.zone_occupancy[key] = self.zone_occupancy.get(key, 0) + 1

    def reserve_connection(self, conn_name: str, turn: int) -> None:
        """Reserve one place on a connection for a turn.

        Args:
            conn_name: Name of the connection to reserve.
            turn: Turn when the connection is used.

        Returns:
            None.
        """
        key: Tuple[str, int] = (conn_name, turn)
        self.conn_occupancy[key] = self.conn_occupancy.get(key, 0) + 1


@dataclass(frozen=True)
class AtHub:
    """Represent a drone located at a hub."""

    hub_name: str


@dataclass(frozen=True)
class AtConn:
    """Represent a drone moving through a connection."""

    conn_name: str
    dest: str


Location = Union[AtHub, AtConn]
Node = Tuple[Location, int]


class NeighborGen:
    """Generate valid next nodes for the path planner."""

    def __init__(self, graph: Graph) -> None:
        """Initialize the generator with a graph.

        Args:
            graph: Graph used to find neighboring hubs and connections.

        Returns:
            None.
        """
        self.graph = graph

    def _neighbors_from_zone(
        self,
        location: AtHub,
        turn: int,
        reserv: ReservationTable,
        start: str
    ) -> List[Node]:
        """Find valid next nodes when a drone is at a hub.

        Args:
            location: Current hub location.
            turn: Current simulation turn.
            reserv: Existing reservations.
            start: Name of the starting hub.

        Returns:
            Valid neighboring nodes for the next step.
        """
        neighbors: List[Node] = []

        for conn in self.graph.adjacency[location.hub_name]:
            neighbor_name = conn.hub_b if (
                    conn.hub_a == location.hub_name
                ) else conn.hub_a
            neighbor_hub = self.graph.hubs_dict[neighbor_name]

            if neighbor_name == start and location.hub_name != start:
                continue

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
        """Find the next node after a restricted connection step.

        Args:
            location: Current connection location.
            turn: Current simulation turn.

        Returns:
            The destination hub at the next turn.
        """
        return [(AtHub(location.dest), turn + 1)]

    def get_neighbors(
        self,
        node: Node,
        reserv: ReservationTable,
        start: str
    ) -> List[Node]:
        """Get valid next nodes for a planner node.

        Args:
            node: Current location and turn.
            reserv: Existing reservations.
            start: Name of the starting hub.

        Returns:
            Valid neighboring nodes.
        """
        location, turn = node

        if isinstance(location, AtHub):
            return self._neighbors_from_zone(location, turn, reserv, start)
        return self._neighbors_from_conn(location, turn)
