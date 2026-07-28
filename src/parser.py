from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, field_validator, model_validator, Field


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
            raise ValueError(
                f"Unknown line type - {value}"
            )
        return value


class NbDrones(BaseModel):
    count: int = Field(ge=1)


class HubMetadata(BaseModel):
    zone: Literal[
        "normal",
        "blocked",
        "restricted",
        "priority"
    ] = "normal"
    color: Optional[str]
    max_drones: int = Field(default=1, ge=1)

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        if any(ch.isspace() for ch in value):
            raise ValueError(
                f"{value} - Color can only be a single word."
            )

        if not value:
            raise ValueError(
                f"{value} - Color can not be left empty."
            )

        return value


class ConnectionMetadata(BaseModel):
    max_link_capacity: int = Field(default=1, ge=1)


class Hub(BaseModel):
    hub_type: Literal["start_hub", "end_hub", "hub"]
    name: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    metadata: HubMetadata

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return validate_hub_name(value)


class Connection(BaseModel):
    source: str
    destination: str
    metadata: ConnectionMetadata

    @field_validator("source", "destination")
    @classmethod
    def validate_zone(cls, value: str) -> str:
        return validate_hub_name(value)

    @model_validator(mode="after")
    def validate_connection(self) -> "Connection":
        if self.source == self.destination:
            raise ValueError(
                f"'{self.source}-{self.destination}' - "
                "Hub is connected to itself."
            )
        return self


def validate_hub_name(value: str) -> str:
    if any(ch.isspace() for ch in value) or "-" in value:
        raise ValueError(
            f"{value} - Hub names cannot containt spaces or dashes."
        )
    return value


class Config(BaseModel):
    nb_drones: int
    start_hub: Hub
    end_hub: Hub
    hubs: Dict[str, Hub]
    connections: List[Connection]


class Parser:
    def __init__(self) -> None:
        self._raw_data: List[ConfigLine] = []
        self._nb_drones = None
        self._start_hub = None
        self._end_hub = None
        self._hubs: Dict[str, Hub] = {}
        self._connections: List[Connection] = []

    def _line_extractor(self, config_file: str) -> None:
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
                self._raw_data.append(
                    ConfigLine(
                        line_type=l_type.strip(),
                        line_data=l_data.strip()
                    )
                )
        if self._raw_data[0].line_type != "nb_drones":
            raise ParserError(
                "Invalid line #1 - Must be nb_drones type."
            )

    def _parse_nb_drones(self, line: ConfigLine) -> None:
        self._nb_drones = NbDrones(count=line.line_data)

    def parse_config(self, config_file: str) -> None:
        self._line_extractor(config_file)
        for line in self._raw_data:
            print(line)
        print()
        for line in self._raw_data:
            match line.line_type:
                case "nb_drones":
                    self._parse_nb_drones(line)
