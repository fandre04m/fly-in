from typing import Dict, Tuple, List
from planner import AtHub, Location, Node
from dataclasses import dataclass


@dataclass
class Logger:
    _by_turn: Dict[int, List[Tuple[str, Location, bool]]]
    _avg_turns_per_drone: float

    @classmethod
    def build_log(cls, paths: Dict[str, List[Node]]) -> "Logger":
        by_turn: Dict[int, List[Tuple[str, Location, bool]]] = {}
        total_turns_all_drones: int = 0

        for d_id, path in paths.items():
            for i, (location, turn) in enumerate(path):
                is_move = i > 0 and path[i - 1][0] != location
                by_turn.setdefault(turn, []).append((d_id, location, is_move))

            total_turns_all_drones += path[-1][1]

        avg_turns = total_turns_all_drones / len(paths)

        return cls(_by_turn=by_turn, _avg_turns_per_drone=avg_turns)

    def moves_per_turn(self) -> None:
        print("\nAll moves per turn:")
        for moves in self._by_turn.values():
            turn_moves = []
            for d_id, loc, is_move in moves:
                if isinstance(loc, AtHub):
                    loc_name = loc.hub_name
                else:
                    loc_name = loc.conn_name
                if is_move:
                    turn_moves.append(f"{d_id}-{loc_name}")
            if turn_moves:
                print(" ".join(turn_moves))

    def total_turns(self) -> None:
        print(f"\nTotal turns: {max(self._by_turn.keys())}")

    def drones_per_turn(self) -> None:
        print("\nDrones moved per turn:")
        for turn, moves in self._by_turn.items():
            moved_drones = set()
            for d_id, _, is_move in moves:
                if is_move:
                    moved_drones.add(d_id)
            if turn > 0:
                print(f"Turn {turn}: {len(moved_drones)}")

    def turns_per_drone(self) -> None:
        print(f"\nAverage turns per drone: {self._avg_turns_per_drone:.2f}")
