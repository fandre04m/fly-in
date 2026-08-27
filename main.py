from typing import Dict, List
from argparse import ArgumentParser
from pathlib import Path
from parser import Parser, ParserError, Config
from graph import Graph
from planner import (
    AtHub, ReservationTable, NeighborGen, Node, make_conn_name
)
from dijkstra import Dijkstra
from output_logger import Logger, Moves
from interface import make_gui


def moves_by_turn(
    paths: Dict[str, List[Node]]
) -> Dict[int, List[Moves]]:
    by_turn: Dict[int, List[Moves]] = {}

    for d_id, path in paths.items():
        for i, (location, turn) in enumerate(path):
            is_move = i > 0 and path[i - 1][0] != location

            if i > 0:
                prev_loc = path[i - 1][0]
            else:
                prev_loc = location

            by_turn.setdefault(turn, []).append(
                Moves(d_id, prev_loc, location, is_move)
            )

    return by_turn


def main() -> None:
    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        "--config-path", default="maps/easy/01_linear_path.txt"
    )
    arg_parser.add_argument("--no-gui", action="store_true")
    arg_parser.add_argument("--extra-logs", action="store_true")
    arg_parser.add_argument("--hub-cap", action="store_true")
    args = arg_parser.parse_args()

    parser = Parser()
    try:
        config: Config = parser.parse_config(Path(args.config_path))
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

    graph = Graph.from_config(config)

    try:
        graph.validate_static_graph(
            config.start_hub.name,
            config.end_hub.name
        )
    except ValueError as e:
        print(f"Graph validation error: {e}")
        return

    reserved = ReservationTable()
    neighbor_gen = NeighborGen(graph)
    dijkstra = Dijkstra(graph, neighbor_gen)
    paths: Dict[str, List[Node]] = {}

    for d_id in range(1, config.nb_drones.nb_drones + 1):
        try:
            path: List[Node] = dijkstra.run(
                reserved,
                config.start_hub.name,
                config.end_hub.name
            )

            for i, (loc, turn) in enumerate(path):
                if isinstance(loc, AtHub):
                    reserved.reserve_zone(loc.hub_name, turn)

                    if i == 0:
                        continue

                    prev_loc = path[i - 1][0]
                    if isinstance(prev_loc, AtHub) and (
                        prev_loc.hub_name != loc.hub_name
                    ):
                        conn = graph.get_connection(
                            prev_loc.hub_name, loc.hub_name
                        )
                        reserved.reserve_connection(
                            make_conn_name(conn), turn
                        )

                else:
                    reserved.reserve_connection(loc.conn_name, turn)

            paths[f"D{d_id}"] = path
        except ValueError as e:
            print(f"Algorithm error: D{d_id} {e}")
            return

    by_turn = moves_by_turn(paths)

    logger = Logger.build_log(paths, by_turn)
    logger.moves_per_turn()
    if args.extra_logs:
        logger.total_turns()
        logger.drones_per_turn()
        logger.turns_per_drone()
        logger.total_path_cost()
    # if args.hub_cap:
    #     logger.hub_capacity(reserved, graph)

    if not args.no_gui:
        make_gui(config, by_turn)


if __name__ == "__main__":
    main()
