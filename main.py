from typing import Dict, List
from parser import Parser, ParserError, Config
from graph import Graph
from planner import AtHub, ReservationTable, NeighborGen, Node
from dijkstra import Dijkstra
from output_logger import Logger


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
    #
    # print("Hubs:")
    # print(
    #     f"{config.nb_drones}\n{config.start_hub}\n{config.end_hub}"
    # )
    # for hub in config.hubs:
    #     print(hub)
    # print("Connections:")
    # for connect in config.connections:
    #     print(connect)
    # print()
    graph = Graph.from_config(config)

    try:
        shortest_dist: int = graph.validate_static_graph(
            config.start_hub.name,
            config.end_hub.name
        )
    except ValueError as e:
        print(f"Graph validation error: {e}")
        return

    max_turns = shortest_dist * 3

    reserved = ReservationTable()
    neighbor_gen = NeighborGen(graph)
    dijkstra = Dijkstra(graph, neighbor_gen)
    paths: Dict[str, List[Node]] = {}

    for d_id in range(1, config.nb_drones.nb_drones + 1):
        try:
            path: List[Node] = dijkstra.run(
                reserved,
                config.start_hub.name,
                config.end_hub.name,
                max_turns
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
    #
    # for drone, path in paths.items():
    #     print(f"{drone}:\n{path}\n")

    logger = Logger.build_log(paths)
    logger.print_log()


if __name__ == "__main__":
    main()
