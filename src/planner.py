from typing import Dict, Tuple


class ReservationTable:
    def __init__(self) -> None:
        self.zone_occupancy: Dict[Tuple[str, int], int] = {}
        self.conn_occupancy: Dict[Tuple[str, int], int] = {}
