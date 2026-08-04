from src import Parser, ParserError, Config
from src import Graph


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
    print("\nHubs dictionary:")
    for key, value in graph.hubs_dict.items():
        print(f"{key}: {value}")
    print("\nConnection list by hub:")
    for key, value in graph.adjacency.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
