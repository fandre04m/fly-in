from typing import Dict, List, Tuple


class ParserError(Exception):
    """Base exception for configuration parsing errors."""
    pass


class Extractor:
    def load_config(self, config_file: str) -> List[Tuple[str, str]]:
        raw_data: List[Tuple[str, str]] = []
        with open(config_file, encoding="utf-8") as f:
            for num, line in enumerate(f, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    raise ParserError(
                        f"Line #{num} '{line}' has invalid format. "
                        "(expected TYPE: DATA)"
                    )
                line_type, line_data = line.split(":", 1)
                raw_data.append((line_type.strip(), line_data.strip()))
        return raw_data


def main() -> None:
    extractor = Extractor()
    raw_data = extractor.load_config("../config.txt")
    for line in raw_data:
        print(line)


main()
