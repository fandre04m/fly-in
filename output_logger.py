from typing import Dict, Tuple, List
from planner import Location, Node
from dataclasses import dataclass


@dataclass
class Logger:
    by_turn: Dict[int, List[Tuple[str, Location, bool]]]

    @classmethod
    def build_log(cls, paths: Dict[str, List[Node]]) -> "Logger":
        by_turn: Dict[int, List[Tuple[str, Location, bool]]] = {}

        for d_id, path in paths.items():
            for i, (location, turn) in enumerate(path):
                is_move = i > 0 and path[i - 1][0] != location
                by_turn.setdefault(turn, []).append((d_id, location, is_move))

        return cls(by_turn=by_turn)

    def print_log(self) -> None:
        for turn, moves in self.by_turn.items():
            if turn > 0:
                print(f"Turn: {turn}")
            for d_id, loc, is_move in moves:
                if is_move:
                    print(f"{d_id}-{loc}")
