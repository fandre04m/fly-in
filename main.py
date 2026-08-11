from parser import Parser, ParserError, Config
from graph import Graph
from planner import (
    ReservationTable, NeighborGen, ConnLocation, ZoneLocation,
    make_conn_name
)


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
    # print("\nHubs dictionary:")
    # for key, value in graph.hubs_dict.items():
    #     print(f"{key}: {value}")
    print("\nConnection list by hub:")
    for key, value in graph.adjacency.items():
        print(f"{key}: {value}")
    print()
    neighbor_gen = NeighborGen(graph)
    reserved = ReservationTable()
    conn = config.connections[2]
    node = (ConnLocation(make_conn_name(conn), conn.hub_b), 2)
    location, turn = node
    node_neighbors = neighbor_gen.get_neighbors(node, reserved)
    print(f"Node '{location.conn_name}' possible neighbors next turn "
          f"(current {turn}):\n{node_neighbors}")


if __name__ == "__main__":
    main()
