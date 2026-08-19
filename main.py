from typing import Dict, List
from parser import Parser, ParserError, Config
from graph import Graph
from planner import AtHub, ReservationTable, NeighborGen, Node
from dijkstra import Dijkstra
from output_logger import Logger
from interface import gui


def main() -> None:
    parser = Parser()
    try:
        config: Config = parser.parse_config("config.txt")
    except (
        FileNotFoundError,
        PermissionError,
        OSError,
    ) as e:
        print(f"File system error: {e}")
        return
    except ParserError as e:
        print(f"Parser error: {e}")
        return

    graph = Graph.from_config(config)

    try:
        graph.validate_static_graph(
            config.start_hub.name,
            config.end_hub.name
        )
    except ValueError as e:
        print(f"Graph validation error: {e}")
        return

    reserved = ReservationTable()
    neighbor_gen = NeighborGen(graph)
    dijkstra = Dijkstra(graph, neighbor_gen)
    paths: Dict[str, List[Node]] = {}

    for d_id in range(1, config.nb_drones.nb_drones + 1):
        try:
            path: List[Node] = dijkstra.run(
                reserved,
                config.start_hub.name,
                config.end_hub.name
            )

            for zone in path:
                loc, turn = zone
                if isinstance(loc, AtHub):
                    reserved.reserve_zone(loc.hub_name, turn)
                else:
                    reserved.reserve_connection(loc.conn_name, turn)
            paths[f"D{d_id}"] = path
        except ValueError as e:
            print(f"Algorithm error: D{d_id} {e}")
            return

    logger = Logger.build_log(paths)
    logger.moves_per_turn()
    logger.total_turns()
    logger.drones_per_turn()
    logger.turns_per_drone()
    logger.total_path_cost()

    gui(config)


if __name__ == "__main__":
    main()
