from typing import Optional, Tuple, Dict, List
import pygame
from graph import Graph
from parser import Config, Connection, Hub
from output_logger import Moves
from planner import Location, Node, AtHub, ReservationTable


W_WIDTH = 1750
W_HEIGHT = 880
X_PADDING = 200
Y_PADDING = 200
TURN_DUR = 1.0
PAUSE_DUR = TURN_DUR / 5


class HubSprite(pygame.sprite.Sprite):
    """Display a hub on the simulation map."""

    def __init__(self, hub: Hub, pos: Tuple[float, float]) -> None:
        """Create a sprite for a hub.

        Args:
            hub: Hub represented by the sprite.
            pos: Initial position on the screen.

        Returns:
            None.
        """
        super().__init__()
        self.hub = hub
        self.pos: Tuple[float, float] = pos
        self.color: Optional[str] = hub.metadata.color

        hub_size = 40 if self.hub.hub_type == "hub" else 60
        self.image = pygame.Surface((hub_size, hub_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)

        self.draw_hub()

    def draw_hub(self) -> None:
        """Draw the hub according to its type and zone.

        Returns:
            None.
        """
        if self.color is None or self.color not in pygame.color.THECOLORS:
            self.color = "pink2"

        circle_rad = 20 if self.hub.hub_type == "hub" else 30
        rect = self.image.get_rect()
        center = self.image.get_rect().center

        if self.hub.metadata.zone == "normal":
            pygame.draw.circle(self.image, self.color, center, circle_rad)
            pygame.draw.circle(self.image, "black", center, circle_rad, 2)
        elif self.hub.metadata.zone == "priority":
            pygame.draw.rect(self.image, self.color, rect, border_radius=7)
            pygame.draw.rect(self.image, "black", rect, 2, 7)
        elif self.hub.metadata.zone == "blocked":
            cut = rect.width // 4
            points = [
                (rect.left + cut, rect.top),
                (rect.right - cut, rect.top),
                (rect.right, rect.top + cut),
                (rect.right, rect.bottom - cut),
                (rect.right - cut, rect.bottom),
                (rect.left + cut, rect.bottom),
                (rect.left, rect.bottom - cut),
                (rect.left, rect.top + cut)
            ]
            pygame.draw.polygon(self.image, "black", points)
            small_rect = self.image.get_rect().inflate(-4, -4)
            cut = small_rect.width // 4
            points = [
                (small_rect.left + cut, small_rect.top),
                (small_rect.right - cut, small_rect.top),
                (small_rect.right, small_rect.top + cut),
                (small_rect.right, small_rect.bottom - cut),
                (small_rect.right - cut, small_rect.bottom),
                (small_rect.left + cut, small_rect.bottom),
                (small_rect.left, small_rect.bottom - cut),
                (small_rect.left, small_rect.top + cut)
            ]
            pygame.draw.polygon(self.image, self.color, points)
        else:
            points = [
                rect.topleft,
                rect.topright,
                rect.midbottom
            ]
            pygame.draw.polygon(self.image, self.color, points)
            pygame.draw.polygon(self.image, "black", points, 2)


class DroneSprite(pygame.sprite.Sprite):
    """Display and animate one drone on the simulation map."""

    def __init__(
        self,
        name: str,
        pos: Tuple[float, float],
        font: pygame.font.Font
    ) -> None:
        """Create a drone sprite at an initial position.

        Args:
            name: Name displayed on the drone.
            pos: Initial position on the screen.
            font: Font used for the drone name.

        Returns:
            None.
        """
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)

        rect = self.image.get_rect()
        center = rect.center

        points = [
            (center[0], rect.top),
            (rect.right, center[1]),
            (center[0], rect.bottom),
            (rect.left, center[1])
        ]

        pygame.draw.polygon(self.image, (60, 60, 60), points)
        name_sur = font.render(name, True, "white")
        name_rect = name_sur.get_rect(center=center)
        self.image.blit(name_sur, name_rect)

        self.rect = self.image.get_rect(center=pos)

        self.initial_pos = pos
        self.start_pos = pos
        self.target_pos = pos
        self.progress = 0.0
        self.duration = TURN_DUR

    def start_move(
        self,
        start_pos: Tuple[float, float],
        target_pos: Tuple[float, float]
    ) -> None:
        """Start moving the drone between two positions.

        Args:
            start_pos: Position where the movement begins.
            target_pos: Position where the movement ends.

        Returns:
            None.
        """
        self.start_pos = start_pos
        self.target_pos = target_pos
        self.progress = 0.0

    def reset(self) -> None:
        """Return the drone to its initial position and animation state.

        Returns:
            None.
        """
        self.start_pos = self.initial_pos
        self.target_pos = self.initial_pos
        self.progress = 0.0
        self.rect.center = (
            round(self.initial_pos[0]),
            round(self.initial_pos[1])
        )

    def update(self, dt: float) -> None:
        """Move the drone according to the elapsed time.

        Args:
            dt: Time elapsed since the previous update in seconds.

        Returns:
            None.
        """
        self.progress += dt / self.duration

        if self.progress >= 1.0:
            self.progress = 1.0

        start_x, start_y = self.start_pos
        target_x, target_y = self.target_pos

        x = start_x + (target_x - start_x) * self.progress
        y = start_y + (target_y - start_y) * self.progress

        self.rect.center = (round(x), round(y))


class TextPanel:
    """Draw the information panel shown below the map."""

    def __init__(self) -> None:
        """Create the panel surface, fonts, and panel layout.

        Returns:
            None.
        """
        self.image = pygame.Surface((1750, 180))
        self.rect = self.image.get_rect(bottomright=(W_WIDTH, W_HEIGHT))
        self.box_size: Tuple[int, int] = (580, 180)
        self.big_font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 30)

    def draw_key_box(self) -> None:
        """Draw the keyboard controls in the panel.

        Returns:
            None.
        """
        surface = pygame.Surface(self.box_size, pygame.SRCALPHA)
        box_pos = surface.get_rect(midright=self.image.get_rect().midright)

        lines: List[str] = [
            "Space: Play/Pause",
            "Right: Step mode",
            "R: Reset animation",
            "Esc: Exit"
        ]
        line_height = self.small_font.get_linesize() + 10
        total_height = line_height * len(lines)
        start_y = (180 - total_height) // 2
        max_len = max(len(line) for line in lines) * 10
        x = (580 - max_len) // 2

        for line in lines:
            text_sur = self.small_font.render(line, True, "white")
            text_pos = text_sur.get_rect(left=x, top=start_y)
            surface.blit(text_sur, text_pos)
            start_y += line_height

        self.image.blit(surface, box_pos)

    def draw_turn_box(self, turn: int, mode: str) -> None:
        """Draw the current turn and playback mode.

        Args:
            turn: Turn number shown to the user.
            mode: Current playback mode.

        Returns:
            None.
        """
        surface = pygame.Surface(self.box_size, pygame.SRCALPHA)
        box_pos = surface.get_rect(midleft=self.image.get_rect().midleft)

        lines: List[str] = [
            f"Turn: {turn}",
            f"Mode: {mode}"
        ]

        line_height = self.big_font.get_linesize() + 10
        total_height = line_height * len(lines)
        start_y = (180 - total_height) // 2
        x = (580 - 220) // 2

        for line in lines:
            text_sur = self.big_font.render(line, True, "white")
            text_pos = text_sur.get_rect(left=x, top=start_y)
            surface.blit(text_sur, text_pos)
            start_y += line_height

        self.image.blit(surface, box_pos)

    def draw_hub_box(
        self,
        turn: int,
        hub: Optional[Hub],
        tables: ReservationTable,
    ) -> None:
        """Draw information about the selected hub.

        Args:
            turn: Turn for which occupancy is shown.
            hub: Selected hub, or None when no hub is selected.
            tables: Reservation data used for occupancy information.

        Returns:
            None.
        """
        surface = pygame.Surface(self.box_size, pygame.SRCALPHA)
        box_pos = surface.get_rect(center=self.image.get_rect().center)
        if hub is None:
            return

        max_cap = hub.metadata.max_drones if hub.hub_type == "hub" else "inf"
        occupancy = tables.zone_occupancy.get((hub.name, turn), 0)
        lines: List[str] = [
            f"Name: {hub.name}",
            f"Type: {hub.metadata.zone}",
            f"Capacity: {occupancy}/{max_cap}"
        ]

        line_height = self.small_font.get_linesize() + 10
        total_height = line_height * len(lines)
        start_y = (180 - total_height) // 2
        x = (580 - 250) // 2

        for line in lines:
            text_sur = self.small_font.render(line, True, "white")
            text_pos = text_sur.get_rect(left=x, top=start_y)
            surface.blit(text_sur, text_pos)
            start_y += line_height

        self.image.blit(surface, box_pos)

    def draw_panel(
        self,
        screen: pygame.Surface,
        turn: int,
        step_mode: str,
        hub: Optional[Hub],
        tables: ReservationTable,
        graph: Graph
    ) -> None:
        """Draw all information boxes on the screen.

        Args:
            screen: Surface where the panel should be displayed.
            turn: Turn number shown to the user.
            step_mode: Current playback mode text.
            hub: Selected hub, or None when no hub is selected.
            tables: Reservation data used for hub information.
            graph: Graph containing the map data.

        Returns:
            None.
        """
        self.image.fill((40, 40, 40))
        self.draw_key_box()
        self.draw_turn_box(turn, step_mode)
        self.draw_hub_box(turn, hub, tables)
        screen.blit(self.image, self.rect)


def animate_bg(
    screen: pygame.surface.Surface,
    bg_surface: pygame.surface.Surface,
    bg_x_pos: float,
    dt: float
) -> float:
    """Move and draw the scrolling background.

    Args:
        screen: Surface where the background should be drawn.
        bg_surface: Background image to draw.
        bg_x_pos: Current horizontal background position.
        dt: Time elapsed since the previous frame in seconds.

    Returns:
        The updated horizontal background position.
    """
    bg_speed: float = 20.0

    bg_x_pos -= bg_speed * dt
    if bg_x_pos <= -W_WIDTH:
        bg_x_pos = 0
    screen.blit(bg_surface, (bg_x_pos, 0))
    screen.blit(bg_surface, (W_WIDTH + bg_x_pos, 0))

    return bg_x_pos


def make_grid(
    hubs: List[Hub]
) -> Dict[Tuple[int, int], Tuple[float, float]]:
    """Convert hub map coordinates into screen positions.

    Args:
        hubs: Hubs whose positions should be converted.

    Returns:
        A mapping from map coordinates to screen positions.
    """
    grid: Dict[Tuple[int, int], Tuple[float, float]] = {}

    min_x = min(hub.x for hub in hubs)
    max_x = max(hub.x for hub in hubs)
    min_y = min(hub.y for hub in hubs)
    max_y = max(hub.y for hub in hubs)

    width_cells = max_x - min_x + 1
    height_cells = max_y - min_y + 1

    cell_width = (W_WIDTH - X_PADDING) / width_cells
    cell_height = (W_HEIGHT - Y_PADDING) / height_cells
    cell_size = min(cell_width, cell_height)
    if cell_size > 150.0:
        cell_size = 150.0

    grid_width = cell_size * width_cells
    grid_height = cell_size * height_cells

    o_x = (W_WIDTH - grid_width) / 2
    o_y = (W_HEIGHT - grid_height) / 3

    for hub in hubs:
        grid_x = hub.x - min_x
        grid_y = hub.y - min_y

        pixel_x = o_x + grid_x * cell_size + cell_size / 2
        pixel_y = o_y + (height_cells - grid_y - 1) * cell_size + cell_size / 2

        grid[(hub.x, hub.y)] = (pixel_x, pixel_y)

    return grid


def make_hub_sprite_lst(
    hubs: List[Hub],
    grid: Dict[Tuple[int, int], Tuple[float, float]],
    sprites: pygame.sprite.Group
) -> Dict[str, HubSprite]:
    """Create and register sprites for all hubs.

    Args:
        hubs: Hubs to display.
        grid: Mapping from hub coordinates to screen positions.
        sprites: Group where the created sprites should be registered.

    Returns:
        A mapping from hub names to their sprites.
    """
    sprite_names: Dict[str, HubSprite] = {}

    for hub in hubs:
        pos = grid[(hub.x, hub.y)]
        sprite = HubSprite(hub, pos)
        sprites.add(sprite)
        sprite_names[hub.name] = sprite

    return sprite_names


def draw_connections(
    surface: pygame.Surface,
    connections: List[Connection],
    sprites_dict: Dict[str, HubSprite]
) -> None:
    """Draw all map connections between hub sprites.

    Args:
        surface: Surface where the connections should be drawn.
        connections: Connections to draw.
        sprites_dict: Hub sprites used to find endpoint positions.

    Returns:
        None.
    """
    for conn in connections:
        pygame.draw.line(
            surface,
            (90, 90, 90),
            sprites_dict[conn.hub_a].rect.center,
            sprites_dict[conn.hub_b].rect.center,
            2
        )


def make_drone_sprite_lst(
    paths: Dict[str, List[Node]],
    start: Hub,
    hub_grid: Dict[Tuple[int, int], Tuple[float, float]],
    sprites: pygame.sprite.Group
) -> Dict[str, DroneSprite]:
    """Create and register sprites for all drones.

    Args:
        paths: Planned paths for each drone.
        start: Starting hub for the drones.
        hub_grid: Mapping from hub coordinates to screen positions.
        sprites: Group where the created sprites should be registered.

    Returns:
        A mapping from drone names to their sprites.
    """
    drone_dict = {}
    font = pygame.font.Font(None, 15)

    for d_id in paths:
        sprite = DroneSprite(d_id, hub_grid[start.x, start.y], font)
        sprites.add(sprite)
        drone_dict[d_id] = sprite

    return drone_dict


def resolve_pos(
    loc: Location,
    group_by_hub: Dict[str, HubSprite],
) -> Tuple[float, float]:
    """Find the screen position of a planned location.

    Args:
        loc: Hub or connection location to resolve.
        group_by_hub: Hub sprites used to find screen positions.

    Returns:
        The screen position for the location.
    """
    if isinstance(loc, AtHub):
        return group_by_hub[loc.hub_name].rect.center

    hub_a, hub_b = loc.conn_name.split("-")
    pt_a = group_by_hub[hub_a].rect.center
    pt_b = group_by_hub[hub_b].rect.center
    return ((pt_a[0] + pt_b[0]) / 2, (pt_a[1] + pt_b[1]) / 2)


def make_gui(
    config: Config,
    paths: Dict[str, List[Node]],
    by_turn: Dict[int, List[Moves]],
    tables: ReservationTable,
    graph: Graph
) -> None:
    """Run the graphical drone simulation.

    Args:
        config: Parsed map configuration.
        paths: Planned path for each drone.
        by_turn: Drone moves grouped by turn.
        tables: Reservation data used by the information panel.
        graph: Map graph used by the interface.

    Returns:
        None.
    """
    pygame.init()
    pygame.display.set_caption("Fly-in")

    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((W_WIDTH, W_HEIGHT))
    running = True
    drones_paused = True
    # Background setup
    bg_surface = pygame.image.load("sky.jpg").convert()
    bg_surface = pygame.transform.scale(bg_surface, (W_WIDTH, W_HEIGHT))
    bg_x_pos: float = 0.0

    all_hubs = config.hubs.copy()
    all_hubs.extend((config.start_hub, config.end_hub))
    # Grid that translates int graph coords to pixel coords
    hub_grid = make_grid(all_hubs)
    # Hub sprites
    hub_group = pygame.sprite.Group()
    group_by_hub: Dict[str, HubSprite] = make_hub_sprite_lst(
        all_hubs,
        hub_grid,
        hub_group
    )
    # Connection surface with all lines drawn
    lines_surface = pygame.Surface((W_WIDTH, W_HEIGHT), pygame.SRCALPHA)
    draw_connections(lines_surface, config.connections, group_by_hub)
    # Drone sprites
    drone_group = pygame.sprite.Group()
    group_by_drone: Dict[str, DroneSprite] = make_drone_sprite_lst(
        paths,
        config.start_hub,
        hub_grid,
        drone_group
    )
    # Text panel instance
    info_panel = TextPanel()
    selected_hub: Optional[Hub] = None
    # Turn variables
    curr_turn = 1
    display_turn = 0
    display_mode = "Paused"
    turn_started = False
    mid_pause = False
    pause_elapsed = 0.0
    step_mode = False

    total_turns = max(by_turn.keys())

    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Key events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    drones_paused = not drones_paused
                    step_mode = False
                    display_mode = "Paused" if drones_paused else "Play"
                if event.key == pygame.K_RIGHT:
                    drones_paused = False
                    step_mode = True
                    display_mode = "Step"
                if event.key == pygame.K_r:
                    curr_turn = 1
                    display_turn = 0
                    display_mode = "Paused"
                    turn_started = False
                    mid_pause = False
                    pause_elapsed = 0.0
                    step_mode = False
                    drones_paused = True
                    for drone in group_by_drone.values():
                        drone.reset()
            # Mouse click event
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    selected_hub = None
                    for sprite in group_by_hub.values():
                        if sprite.rect.collidepoint(event.pos):
                            selected_hub = sprite.hub
                            break

        # Drone animation logic
        if curr_turn <= total_turns:
            if not drones_paused:
                if not turn_started:
                    display_turn = curr_turn
                    for d_id, prev_loc, loc, _ in by_turn[curr_turn]:
                        start_pos = resolve_pos(prev_loc, group_by_hub)
                        target_pos = resolve_pos(loc, group_by_hub)
                        group_by_drone[d_id].start_move(start_pos, target_pos)
                    turn_started = True
                if not mid_pause:
                    drone_group.update(dt)
                    if all(s.progress == 1.0 for s in group_by_drone.values()):
                        if step_mode:
                            curr_turn += 1
                            turn_started = False
                            mid_pause = False
                            drones_paused = True
                            step_mode = False
                        else:
                            mid_pause = True
                            pause_elapsed = 0.0
                else:
                    pause_elapsed += dt
                    if pause_elapsed >= PAUSE_DUR:
                        curr_turn += 1
                        turn_started = False
                        mid_pause = False

        # Animate the background
        bg_x_pos = animate_bg(screen, bg_surface, bg_x_pos, dt)
        # Draw connections and hub
        screen.blit(lines_surface, (0, 0))
        hub_group.draw(screen)
        # Draw bottom grey text box
        info_panel.draw_panel(
            screen,
            display_turn,
            display_mode,
            selected_hub,
            tables,
            graph
        )
        # Draw drones
        drone_group.draw(screen)

        pygame.display.flip()

    pygame.quit()
