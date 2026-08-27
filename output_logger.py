from typing import Dict, List
from dataclasses import dataclass
from collections import namedtuple
# from graph import Graph
from planner import AtHub, Node  # ReservationTable


Moves = namedtuple("Moves", ["d_id", "prev_loc", "loc", "is_move"])


@dataclass
class Logger:
    _moves_per_turn: Dict[int, List[str]]
    _drones_per_turn: Dict[int, int]
    _total_turns: int
    _avg_turns_per_drone: float
    _total_cost_all_drones: int

    @classmethod
    def build_log(
        cls,
        paths: Dict[str, List[Node]],
        by_turn: Dict[int, List[Moves]]
    ) -> "Logger":
        total_turns_all_drones: int = 0
        for path in paths.values():
            total_turns_all_drones += path[-1][1]
        avg_turns = total_turns_all_drones / len(paths)

        moves_per_turn: Dict[int, List[str]] = {}
        drones_per_turn: Dict[int, int] = {}
        for turn, moves in by_turn.items():
            turn_moves = []
            moved_drones = set()

            for d_id, _, loc, is_move in moves:
                if isinstance(loc, AtHub):
                    loc_name = loc.hub_name
                else:
                    loc_name = loc.conn_name

                if is_move:
                    turn_moves.append(f"{d_id}-{loc_name}")
                    moved_drones.add(d_id)

            if turn_moves:
                moves_per_turn[turn] = turn_moves

            drones_per_turn[turn] = len(moved_drones)

        total_turns = max(by_turn.keys())

        return cls(
            _moves_per_turn=moves_per_turn,
            _drones_per_turn=drones_per_turn,
            _total_turns=total_turns,
            _avg_turns_per_drone=avg_turns,
            _total_cost_all_drones=total_turns_all_drones
        )

    # def hub_capacity(self, tables: ReservationTable, graph: Graph) -> None:
    #     print("\nHubs occupancy by turn:")
    #     for turn in range(1, self._total_turns + 1):
    #         entries: List[str] = []
    #         for name, hub in graph.hubs_dict.items():
    #             max_drones = hub.metadata.max_drones if (
    #                 hub.hub_type == "hub") else float("inf")
    #             count = tables.zone_occupancy.get((name, turn), 0)
    #             entries.append(f"{name}({count}/{max_drones})")
    #
    #         if entries:
    #             print(f"Turn {turn}: {' '.join(entries)}")
    #
    def moves_per_turn(self) -> None:
        print("\nAll moves per turn:")
        for moves in self._moves_per_turn.values():
            print(" ".join(moves))

    def total_turns(self) -> None:
        print(f"\nTotal turns: {self._total_turns}")

    def drones_per_turn(self) -> None:
        print("\nDrones moved per turn:")
        for turn, drones in self._drones_per_turn.items():
            if turn > 0:
                print(f"Turn {turn}: {drones}")

    def turns_per_drone(self) -> None:
        print(f"\nAverage turns per drone: {self._avg_turns_per_drone:.2f}")

    def total_path_cost(self) -> None:
        print(f"\nTotal path cost: {self._total_cost_all_drones}")
