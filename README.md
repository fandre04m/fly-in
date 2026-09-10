*This project has been created as part of the 42 curriculum by fandre-m*

# Fly-In

## Description

Fly-In is a Python simulation that moves drones through a network of connected hubs. The program reads a map file, validates it, finds paths from the start hub to the end hub, and schedules the drones while respecting hub and connection capacities.

The project includes terminal output for the planned movements and a Pygame interface that shows the map, hubs, drones, animation turns, and selected hub information.

## Instructions

### Requirements

- Python 3.10 or later
- `uv`
- A system that can open a Pygame window when the graphical interface is used

Install the dependencies with:

```bash
make install
```

Run the default map with the graphical interface:

```bash
make run
```

The main command also accepts these options:

- `--config-path PATH`: choose a map file.
- `--no-gui`: print the simulation without opening the Pygame interface.
- `--extra-logs`: print additional path statistics.

Example:

```bash
make run ARGS="--no-gui --extra-logs --config-path='maps/hard/01_maze_nightmare.txt'"
```

Useful development commands are:

```bash
make debug
make lint
make lint-strict
make clean
```

Run commands from the project root because the graphical interface loads `sky.jpg` using a relative path.

### Map format

Map files contain a drone count, one start hub, one end hub, optional hubs, and connections. Metadata can define a hub zone, color, hub capacity, or connection capacity.

Example:

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: middle 1 0 [color=blue]
end_hub: goal 2 0 [color=red]

connection: start-middle
connection: middle-goal
```

## Algorithm and implementation

The parser uses Pydantic models to validate each part of the configuration. It checks line types, hub names, metadata, capacities, duplicate connections, and references to known hubs.

The map is stored as an adjacency graph. Each hub has a list of its connections, which lets the pathfinding code find neighboring hubs without scanning every connection. Hub and connection objects are also stored in dictionaries by name for fast average-case lookup. At the scale of this project, the difference is very small, but using maps is useful practice for writing more efficient lookup logic.

The pathfinder uses Dijkstra's algorithm. A path node contains a location and a turn. A normal or priority hub takes one turn to enter. A restricted hub is represented by an intermediate connection location and takes two turns to reach. Blocked hubs are excluded from the possible neighbors.

The planner can add a waiting node when a drone cannot move. A `ReservationTable` stores zone occupancy and connection usage by turn. Before adding a movement, the neighbor generator checks both capacities. Drones are planned one after another, and each completed path adds its reservations before the next drone is planned.

Priority hubs are preferred when paths have the same arrival turn. A counter is used as a final queue tie-breaker so nodes with equal costs can still be compared safely.

## Visual representation

The Pygame interface displays:

- hubs with different shapes and colors based on their type and zone;
- connections between hubs;
- labelled drones moving between locations;
- the current turn and playback mode;
- keyboard controls;
- information about a hub selected with the mouse, including its type and occupancy;
- play, pause, step-by-step, and reset controls.

The graphical interface helps show why drones wait, which paths they use, and how their positions change during the simulation.

## Example output

For `maps/easy/01_linear_path.txt`, the terminal output is similar to:

```text
All moves per turn:
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Waiting drones are omitted from a line. In this example, D2 waits in turn 1 because the default capacity of `waypoint1` is one drone.

## Resources

- [Python documentation](https://docs.python.org/3/)
- [`heapq` documentation](https://docs.python.org/3/library/heapq.html)
- [`collections.deque` documentation](https://docs.python.org/3/library/collections.html#collections.deque)
- [Pygame sprite documentation](https://www.pygame.org/docs/ref/sprite.html)
- [Pydantic documentation](https://docs.pydantic.dev/latest/)
- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)

AI was used to help explain programming concepts, review design choices, identify possible edge cases, and draft repetitive documentation such as docstrings and this README. The code and decisions were reviewed in the project context, and the implementation remains as my responsibility to understand and explain.
