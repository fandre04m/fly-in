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
        predecessors: Dict[Node, Node] = {}
        queue: List[Tuple[int, int, Node]] = [
            (0, next(tiebreaker), start_node)]

        while queue:
            node = heapq.heappop(queue)[2]
            if node in visited:
                continue

            visited.add(node)

            location, turn = node
            if isinstance(location, ZoneLocation) and location.hub_name == end:
                path: List[Node] = []
                curr: Union[Node, None] = node

                while curr is not None:
                    path.append(curr)
                    curr = predecessors.get(curr)
                    path.reverse()

                return path

            if turn >= max_turns:
                continue

            for neighbor in self.neighbor_gen.get_neighbors(node, reserved):
                # add hub type priority logic later.
                # this requires another data field in each queue object.
                new_cost = neighbor[1]

                if neighbor not in distances or new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    predecessors[neighbor] = node
                    heapq.heappush(
                        queue, (new_cost, next(tiebreaker), neighbor)
                    )

        return None
