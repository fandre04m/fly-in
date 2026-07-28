from src import Parser, ParserError


def main() -> None:
    parser = Parser()
    try:
        parser.parse_config("config.txt")
    except (
        FileNotFoundError,
        PermissionError,
        OSError,
        ParserError,
    ) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
