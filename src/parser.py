from typing import List, Literal, Optional, Dict, Tuple, Set
from pydantic import BaseModel, field_validator, model_validator, Field


class ParserError(Exception):
    """Base exception for configuration parsing errors."""
    pass


class ConfigLine(BaseModel):
    num: int
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
    nb_drones: int = Field(ge=1)


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
    def normalize_color(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None

        return value


class ConnectionMetadata(BaseModel):
    max_link_capacity: int = Field(default=1, ge=1)


class Hub(BaseModel):
    hub_type: Literal["start_hub", "end_hub", "hub"]
    name: str
    x: int
    y: int
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
            f"{value} - Hub names cannot contain spaces or dashes."
        )
    return value


class Config(BaseModel):
    nb_drones: NbDrones
    start_hub: Hub
    end_hub: Hub
    hubs: List[Hub]
    connections: List[Connection]


class Parser:
    def __init__(self) -> None:
        self._raw_data: List[ConfigLine] = []
        self._nb_drones: Dict[str, str] = {}
        self._start_hub: Dict[str, str | HubMetadata] = {}
        self._end_hub: Dict[str, str | HubMetadata] = {}
        self._hubs: List[Dict[str, str | HubMetadata]] = []
        self._connections: List[Dict[str, str | ConnectionMetadata]] = []
        self._seen_hub_names: Set[str] = set()
        self._seen_connections: Set[Tuple[str, ...]] = set()

    def _line_extractor(self, config_file: str) -> None:
        with open(config_file, encoding="utf-8") as f:
            for num, line in enumerate(f, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    raise ParserError(
                        f"Line {num} '{line}' has invalid format. "
                        "(expected TYPE: DATA)"
                    )
                l_type, l_data = line.split(":", 1)
                self._raw_data.append(
                    ConfigLine(
                        num=num,
                        line_type=l_type.strip(),
                        line_data=l_data.strip()
                    )
                )
        if self._raw_data[0].line_type != "nb_drones":
            raise ParserError(
                "First valid line must be nb_drones."
            )

    def _parse_metadata(
        self,
        num: int,
        line_data: str
    ) -> Tuple[str, Dict[str, str]]:
        metadata_dict: Dict[str, str] = {}
        if "[" in line_data:
            data, metadata = line_data.split("[", 1)
            metadata = metadata.strip("]")
            if "[" in metadata:
                raise ParserError(
                    f"Line {num} has more than one metadata set -> '[]'"
                )
            pairs: List[str] = metadata.split()
            for pair in pairs:
                if pair.count("=") != 1:
                    raise ParserError(
                        f"Line {num} - invalid metadata field '{pair}'."
                    )
                key, value = pair.split("=")
                if key in metadata_dict:
                    raise ParserError(
                        f"Line {num} - repeated metadata field '{key}'."
                    )
                metadata_dict[key] = value
            return data.strip(), metadata_dict
        return line_data, metadata_dict

    def _parse_hub(self, line: ConfigLine) -> None:
        data, metadata_dict = self._parse_metadata(line.num, line.line_data)

        for key in metadata_dict.keys():
            if key not in {"zone", "color", "max_drones"}:
                raise ParserError(
                    f"Line {line.num} - wrong metadata field '{key}'"
                )

        hub_data = data.split()
        if len(hub_data) != 3:
            raise ParserError(
                f"Line {line.num} - Hub data with wrong configuration.\n"
                "Expected 'name x y'."
            )

        hub: Dict[str, str | HubMetadata] = {}
        hub["hub_type"] = line.line_type
        hub["name"] = hub_data[0]
        hub["x"] = hub_data[1]
        hub["y"] = hub_data[2]
        hub["metadata"] = HubMetadata.model_validate(metadata_dict)

        if hub["name"] in self._seen_hub_names:
            raise ParserError(
                f"Line {line.num} - Repeated hub name '{hub['name']}'."
            )
        self._seen_hub_names.add(hub["name"])

        if hub["hub_type"] == "start_hub":
            if self._start_hub:
                raise ParserError(
                    f"Line {line.num} - Only one start_hub allowed."
                )
            self._start_hub = hub
        elif hub["hub_type"] == "end_hub":
            if self._end_hub:
                raise ParserError(
                    f"Line {line.num} - Only one end_hub allowed."
                )
            self._end_hub = hub
        else:
            self._hubs.append(hub)

    def _parse_connection(self, line: ConfigLine) -> None:
        data, metadata_dict = self._parse_metadata(line.num, line.line_data)

        if len(metadata_dict) != 1 or next(
                iter(metadata_dict)) != "max_link_capacity":
            raise ParserError(
                f"Line {line.num} - Wrong connection metadata.\n"
                "Expected 'max_link_capacity'."
            )

        connect_data = data.split("-")
        if len(connect_data) > 2:
            raise ParserError(
                f"Line {line.num} - Wrong connection data.\n"
                "Expected 'source-destination'."
            )
        e_1, e_2 = connect_data[0], connect_data[1]
        if e_1 not in self._seen_hub_names or e_2 not in self._seen_hub_names:
            raise ParserError(
                f"Line {line.num} - Connection using undefined hub names."
                "Possible mistype '{e_1}' or '{e_2}'."
            )

        connect: Dict[str, str | ConnectionMetadata] = {}
        connect["source"] = e_1
        connect["destination"] = e_2
        connect["metadata"] = ConnectionMetadata.model_validate(metadata_dict)

        pair = tuple(sorted((connect["source"], connect["destination"])))
        if pair in self._seen_connections:
            raise ParserError(
                f"Line {line.num} - Repeated connections found '{pair}'."
            )
        self._seen_connections.add(pair)

        self._connections.append(connect)

    def parse_config(self, config_file: str) -> Config:
        self._line_extractor(config_file)
        for line in self._raw_data:
            print(f"{line.line_type}: {line.line_data}")
        print()
        for line in self._raw_data:
            match line.line_type:
                case "nb_drones":
                    self._nb_drones[line.line_type] = line.line_data
                case "start_hub" | "end_hub" | "hub":
                    self._parse_hub(line)
                case "connection":
                    self._parse_connection(line)
        return Config(
            nb_drones=NbDrones.model_validate(self._nb_drones),
            start_hub=Hub.model_validate(self._start_hub),
            end_hub=Hub.model_validate(self._end_hub),
            hubs=[Hub.model_validate(hub) for hub in self._hubs],
            connections=[Connection.model_validate(connect) for
                         connect in self._connections]
        )
