from typing import Dict, Tuple, Union, List
from graph import Graph
from planner import NeighborGen, Node, ReservationTable, ZoneLocation
import heapq
from itertools import count


class Dijkstra:
    def __init__(self, graph: Graph, neighbor_gen: NeighborGen) -> None:
        self.graph = graph
        self.neighbor_gen = neighbor_gen

    def run(
        self,
        reserved: ReservationTable,
        start: str,
        end: str,
        max_turns: int
    ) -> Union[List[Node], None]:
        tiebreaker = count()
        start_node: Node = (ZoneLocation(start), 0)

        distances: Dict[Node, int] = {start_node: 0}
        visited: set[Node] = set()
        queue: List[Tuple[int, int, Node]] = [
                (0, next(tiebreaker), start_node)]

        while queue:
            cost, _, node = heapq.heappop(queue)
            if node in visited:
                continue

            visited.add(node)

            location, turn = node
            if isinstance(location, ZoneLocation) and location.hub_name == end:
                print(f"Goal reached: {node} at cost {cost}")
                return []

            if turn >= max_turns:
                continue

            for neighbor, cost in self.neighbor_gen.get_neighbors(
                    node, reserved):
                pass

        return None
