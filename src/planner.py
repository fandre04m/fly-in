from typing import Dict, Tuple
from parser import Hub, Connection


def connection_name(conn: Connection) -> str:
    return f"{conn.hub_a}-{conn.hub_b}"


class ReservationTable:
    def __init__(self) -> None:
        self.zone_occupancy: Dict[Tuple[str, int], int] = {}
        self.conn_occupancy: Dict[Tuple[str, int], int] = {}

    def has_zone_capacity(self, hub: Hub, turn: int) -> bool:
        current: int = self.zone_occupancy.get((hub.name, turn), 0)
        return current < hub.metadata.max_drones

    def has_link_capacity(self, conn: Connection, turn: int) -> bool:
        key: Tuple[str, int] = (connection_name(conn), turn)
        current: int = self.conn_occupancy.get(key, 0)
        return current < conn.metadata.max_link_capacity

    def reserve_zone(self, hub: Hub, turn: int) -> None:
        key: Tuple[str, int] = (hub.name, turn)
        self.zone_occupancy[key] = self.zone_occupancy.get(key, 0) + 1

    def reserve_connection(self, conn: Connection, turn: int) -> None:
        key: Tuple[str, int] = (connection_name(conn), turn)
        self.conn_occupancy[key] = self.conn_occupancy.get(key, 0) + 1
