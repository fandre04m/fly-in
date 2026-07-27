from src import Parser, ParserError


def main() -> None:
    parser = Parser()
    try:
        lines = parser.line_extractor("config.txt")
        for line in lines:
            print(line)
    except (
        FileNotFoundError,
        PermissionError,
        OSError,
        ParserError,
    ) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
