from typing import List
from pydantic import BaseModel, field_validator


class ParserError(Exception):
    """Base exception for configuration parsing errors."""
    pass


class ConfigLine(BaseModel):
    line_type: str
    line_data: str

    @field_validator("line_type")
    @classmethod
    def validate_line_type(cls, value: str) -> str:
        valid = {
            "nb_drones",
            "start_hub",
            "end_hub",
            "hub",
            "connection",
        }
        if value not in valid:
            raise ParserError(
                f"Unknown line type - {value}" 
            )
        return value


class Parser:
    def line_extractor(self, config_file: str) -> List[ConfigLine]:
        raw_data: List[ConfigLine] = []
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
                l_type, l_data = line.split(":", 1)
                raw_data.append(
                    ConfigLine(
                        line_type=l_type.strip(),
                        line_data=l_data.strip()
                    )
                )
        return raw_data
