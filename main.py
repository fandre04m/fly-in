from src import Parser, ParserError, Config


def main() -> None:
    parser = Parser()
    try:
        config: Config = parser.parse_config("config.txt")
        print(
            f"{config.nb_drones}\n{config.start_hub}\n{config.end_hub}"
        )
        for hub in config.hubs:
            print(hub)
        for connect in config.connections:
            print(connect)
    except (
        FileNotFoundError,
        PermissionError,
        OSError,
    ) as e:
        print(f"File system error: {e}")
    except ParserError as e:
        print(f"Parser error: {e}")


if __name__ == "__main__":
    main()
