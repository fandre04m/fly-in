from typing import Dict, Tuple, Union, List
from graph import Graph
from planner import NeighborGen, Node, ReservationTable, AtHub
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
    ) -> List[Node]:
        tiebreaker = count()
        start_node: Node = (AtHub(start), 0)

        visited: set[Node] = set()
        distances: Dict[Node, int] = {start_node: 0}
        predecessors: Dict[Node, Node] = {}
        priority_count: Dict[Node, int] = {}
        # (cost, nb_of_priorities, tiebreaker, node)
        queue: List[Tuple[int, int, int, Node]] = [
            (0, 0, next(tiebreaker), start_node)]

        while queue:
            node = heapq.heappop(queue)[3]
            if node in visited:
                continue

            visited.add(node)

            location = node[0]
            if isinstance(location, AtHub) and location.hub_name == end:
                path: List[Node] = []
                curr: Union[Node, None] = node

                while curr is not None:
                    path.append(curr)
                    curr = predecessors.get(curr)

                path.reverse()
                return path

            for neighbor in self.neighbor_gen.get_neighbors(node, reserved):
                neighbor_loc = neighbor[0]
                # new_cost is the turn. Smaller turn = less time to get there
                new_cost = neighbor[1]
                new_priority = priority_count.get(node, 0)

                if isinstance(neighbor_loc, AtHub):
                    name = neighbor_loc.hub_name
                    if self.graph.hubs_dict[name].metadata.zone == "priority":
                        new_priority += 1

                if neighbor not in distances or new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    predecessors[neighbor] = node
                    priority_count[neighbor] = new_priority
                    heapq.heappush(
                        queue, (new_cost, -new_priority,
                                next(tiebreaker), neighbor)
                    )

                elif (
                    new_cost == distances[neighbor]
                    and new_priority > priority_count[neighbor]
                ):
                    predecessors[neighbor] = node
                    priority_count[neighbor] = new_priority
                    heapq.heappush(
                        queue, (new_cost, -new_priority,
                                next(tiebreaker), neighbor)
                    )

        raise ValueError(
            "could not reach the end hub."
        )
