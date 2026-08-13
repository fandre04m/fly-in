from parser import Parser, ParserError, Config
from graph import Graph
from planner import (
    ReservationTable, NeighborGen,
    # ConnLocation, ZoneLocation,
    # make_conn_name
)
from dijkstra import Dijkstra


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

    print("Extracted data:")
    print(
        f"{config.nb_drones}\n{config.start_hub}\n{config.end_hub}"
    )
    for hub in config.hubs:
        print(hub)
    for connect in config.connections:
        print(connect)

    graph = Graph.from_config(config)

    # print("\nConnection list by hub:")
    # for key, value in graph.adjacency.items():
    #     print(f"{key}: {value}")
    # print()
    shortest_dist: int | None = graph.validate_static_graph(
        config.start_hub.name,
        config.end_hub.name
    )
    if shortest_dist is None:
        print(
            "Graph error: No valid path found between start and end hubs."
        )
        return
    max_turns = shortest_dist * 3

    reserved = ReservationTable()
    neighbor_gen = NeighborGen(graph)
    dijkstra = Dijkstra(graph, neighbor_gen)
    test_path = dijkstra.run(
        reserved,
        config.start_hub.name,
        config.end_hub.name,
        max_turns
    )
    print()
    print(test_path)


if __name__ == "__main__":
    main()
