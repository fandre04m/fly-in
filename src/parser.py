from typing import List, Literal, Optional, Dict, Tuple, Set, NoReturn
from pydantic import (
    BaseModel, ValidationError, field_validator, model_validator, Field
)


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
                f"Unknown line type '{value}'"
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
        if any(ch.isspace() for ch in value) or "-" in value:
            raise ValueError(
                f"Hub names can't contain spaces or dashes '{value}'."
            )
        return value


class Connection(BaseModel):
    source: str
    destination: str
    metadata: ConnectionMetadata

    @model_validator(mode="after")
    def validate_connection(self) -> "Connection":
        if self.source == self.destination:
            raise ValueError(
                "Hub is connected to itself "
                f"'{self.source}-{self.destination}'."
            )
        return self


class Config(BaseModel):
    nb_drones: NbDrones
    start_hub: Hub
    end_hub: Hub
    hubs: List[Hub]
    connections: List[Connection]


class Parser:
    def __init__(self) -> None:
        self._raw_data: List[ConfigLine] = []
        self._seen_hub_names: Set[str] = set()
        self._seen_connections: Dict[Tuple[str, ...], int] = {}

    @staticmethod
    def _raise_validation_error(
        line_num: int,
        e: ValidationError,
    ) -> NoReturn:
        err = e.errors()[0]
        raise ParserError(
            f"Line {line_num} - {err['loc']} {err['msg']}"
        ) from e

    def _line_extractor(self, config_file: str) -> None:
        with open(config_file, encoding="utf-8") as f:
            for num, line in enumerate(f, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    raise ParserError(
                        f"Line {num} '{line}' has invalid format.\n"
                        "(expected TYPE: DATA)"
                    )
                l_type, l_data = line.split(":", 1)
                try:
                    self._raw_data.append(
                        ConfigLine(
                            num=num,
                            line_type=l_type.strip(),
                            line_data=l_data.strip()
                        )
                    )
                except ValidationError as e:
                    self._raise_validation_error(num, e)

        if not self._raw_data:
            raise ParserError(
                "No valid lines where found in the configuration file."
            )

        if self._raw_data[0].line_type != "nb_drones":
            raise ParserError(
                "'nb_drones' not the first valid line of configuration file."
            )

    def _parse_nbdrones(self, line: ConfigLine) -> NbDrones:
        nbdrones_dict: Dict[str, str] = {}
        nbdrones_dict[line.line_type] = line.line_data

        try:
            return NbDrones.model_validate(nbdrones_dict)
        except ValidationError as e:
            self._raise_validation_error(line.num, e)

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
                    f"Line {num} - More than one metadata set -> '[]'"
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

    def _parse_hub(self, line: ConfigLine) -> Hub:
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
        try:
            hub["metadata"] = HubMetadata.model_validate(metadata_dict)
        except ValidationError as e:
            self._raise_validation_error(line.num, e)

        if hub["name"] in self._seen_hub_names:
            raise ParserError(
                f"Line {line.num} - Repeated hub name '{hub['name']}'."
            )
        self._seen_hub_names.add(hub["name"])

        try:
            return Hub.model_validate(hub)
        except ValidationError as e:
            self._raise_validation_error(line.num, e)

    def _parse_connection(self, line: ConfigLine) -> Connection:
        data, metadata_dict = self._parse_metadata(line.num, line.line_data)

        if len(metadata_dict) != 1 or next(
                iter(metadata_dict)) != "max_link_capacity":
            raise ParserError(
                f"Line {line.num} - Wrong connection metadata.\n"
                "Only valid field: 'max_link_capacity'."
            )

        connect_data = data.split("-")
        if len(connect_data) > 2:
            raise ParserError(
                f"Line {line.num} - Wrong connection data.\n"
                "Expected 'source-destination'."
            )
        e_1, e_2 = connect_data[0], connect_data[1]
        connect: Dict[str, str | ConnectionMetadata] = {}
        connect["source"] = e_1
        connect["destination"] = e_2
        try:
            connect["metadata"] = ConnectionMetadata.model_validate(
                metadata_dict
            )
        except ValidationError as e:
            self._raise_validation_error(line.num, e)

        pair = tuple(sorted((connect["source"], connect["destination"])))
        if pair in self._seen_connections:
            raise ParserError(
                f"Line {line.num} - Repeated connections found '{pair}'."
            )
        self._seen_connections[pair] = line.num

        try:
            return Connection.model_validate(connect)
        except ValidationError as e:
            self._raise_validation_error(line.num, e)

    def _validate_conn_names(self) -> None:
        for pair in self._seen_connections:
            e_1, e_2 = pair
            if (e_1 not in self._seen_hub_names) or (
                    e_2 not in self._seen_hub_names):
                raise ParserError(
                    f"Line {self._seen_connections[pair]} - Connection "
                    f"references an undefined hub ('{e_1}', '{e_2}')"
                )

    def parse_config(self, config_file: str) -> Config:
        nb_drones: NbDrones | None = None
        start_hub: Hub | None = None
        end_hub: Hub | None = None
        hubs: List[Hub] = []
        connections: List[Connection] = []

        self._line_extractor(config_file)
        for line in self._raw_data:
            match line.line_type:
                case "nb_drones":
                    nb_drones = self._parse_nbdrones(line)
                case "start_hub":
                    if start_hub:
                        raise ParserError(
                            f"Line {line.num} - Only one start_hub allowed."
                        )
                    start_hub = self._parse_hub(line)
                case "end_hub":
                    if end_hub:
                        raise ParserError(
                            f"Line {line.num} - Only one end_hub allowed."
                        )
                    end_hub = self._parse_hub(line)
                case "hub":
                    hubs.append(self._parse_hub(line))
                case "connection":
                    connections.append(self._parse_connection(line))

        if not nb_drones:
            raise ParserError(
                "No 'nb_drones' line present in configuration file."
            )
        if not start_hub:
            raise ParserError(
                "No 'start_hub' line present in configuration file."
            )
        if not end_hub:
            raise ParserError(
                "No 'end_hub' line present in configuration file."
            )

        self._validate_conn_names()

        return Config(
            nb_drones=nb_drones,
            start_hub=start_hub,
            end_hub=end_hub,
            hubs=hubs,
            connections=connections
        )
