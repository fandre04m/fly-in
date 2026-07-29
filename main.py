from src import Parser, ParserError, Config
from pydantic import ValidationError


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
        ParserError,
    ) as e:
        print(f"Error: {e}")
    except ValidationError as e:
        print(e.errors()[0]['msg'])


if __name__ == "__main__":
    main()
