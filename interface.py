from typing import Optional, Tuple, Dict, List
import pygame
from parser import Config, Connection, Hub
from output_logger import Moves
from planner import Node


W_WIDTH = 1750
W_HEIGHT = 880
X_PADDING = 200
Y_PADDING = 200


class HubSprite(pygame.sprite.Sprite):
    def __init__(self, hub: Hub, pos: Tuple[float, float]) -> None:
        super().__init__()
        self.hub = hub
        self.pos: Tuple[float, float] = pos
        self.color: Optional[str] = hub.metadata.color

        hub_size = 40 if self.hub.hub_type == "hub" else 60
        self.image = pygame.Surface((hub_size, hub_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)

        self.draw_hub()

    def draw_hub(self) -> None:
        if self.color is None or self.color not in pygame.color.THECOLORS:
            self.color = "pink"

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


class VisualConn:
    def __init__(
        self,
        hub_a: HubSprite,
        hub_b: HubSprite
    ) -> None:
        self.point_a = hub_a.rect.center
        self.point_b = hub_b.rect.center


class DroneSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        name: str,
        pos: Tuple[float, float],
        font: pygame.font.Font
    ) -> None:
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

        self.start_pos = pos
        self.target_pos = pos
        self.progress = 0.0
        self.duration = 1.0

    def start_move(
        self,
        start_pos: Tuple[float, float],
        target_pos: Tuple[float, float]
    ) -> None:
        self.start_pos = start_pos
        self.target_pos = target_pos
        self.progress = 0.0

    def update(self, dt: float) -> None:
        self.progress += dt / self.duration

        if self.progress >= 1.0:
            self.progress = 1.0

        start_x, start_y = self.start_pos
        target_x, target_y = self.target_pos

        x = start_x + (target_x - start_x) * self.progress
        y = start_y + (target_y - start_y) * self.progress

        self.rect.center = (round(x), round(y))


def animate_bg(
    screen: pygame.surface.Surface,
    bg_surface: pygame.surface.Surface,
    bg_x_pos: float,
    dt: float
) -> float:
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
    o_y = (W_HEIGHT - grid_height) / 4

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
    sprite_names: Dict[str, HubSprite] = {}

    for hub in hubs:
        pos = grid[(hub.x, hub.y)]
        sprite = HubSprite(hub, pos)
        sprites.add(sprite)
        sprite_names[hub.name] = sprite

    return sprite_names


def draw_connections(
    connections: List[Connection],
    sprites_dict: Dict[str, HubSprite]
) -> pygame.Surface:
    surface = pygame.Surface((W_WIDTH, W_HEIGHT), pygame.SRCALPHA)

    lines: List[VisualConn] = []
    for conn in connections:
        lines.append(VisualConn(
            sprites_dict[conn.hub_a], sprites_dict[conn.hub_b]
        ))

    for line in lines:
        pygame.draw.line(
            surface, (90, 90, 90), line.point_a, line.point_b, 2
        )
    return surface


def make_drone_sprite_lst(
    paths: Dict[str, List[Node]],
    start: Hub,
    hub_grid: Dict[Tuple[int, int], Tuple[float, float]],
    sprites: pygame.sprite.Group
) -> Dict[str, DroneSprite]:
    drone_dict = {}
    drone_ids = [d_id for d_id in paths.keys()]
    font = pygame.font.Font(None, 15)

    for d_id in drone_ids:
        sprite = DroneSprite(d_id, hub_grid[start.x, start.y], font)
        sprites.add(sprite)
        drone_dict[d_id] = sprite

    return drone_dict


def draw_text_box() -> pygame.Surface:
    surface = pygame.Surface((1750, 200))
    surface.fill((40, 40, 40))

    return surface


def make_gui(
    config: Config,
    paths: Dict[str, List[Node]],
    by_turn: Dict[int, List[Moves]]
) -> None:
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
    lines_surface: pygame.Surface = draw_connections(
        config.connections,
        group_by_hub
    )
    # Bottom text box
    text_box: pygame.Surface = draw_text_box()
    box_pos = text_box.get_rect(midbottom=(W_WIDTH / 2, W_HEIGHT))
    # Drone sprites
    drone_group = pygame.sprite.Group()
    group_by_drone: Dict[str, DroneSprite] = make_drone_sprite_lst(
        paths,
        config.start_hub,
        hub_grid,
        drone_group
    )
    # Drone animation test
    drone = group_by_drone["D1"]
    drone.start_move(hub_grid[(0, 0)], hub_grid[(2, 0)])
    # Turn mechanics
    curr_turn = 1

    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    drones_paused = not drones_paused

        bg_x_pos = animate_bg(screen, bg_surface, bg_x_pos, dt)

        screen.blit(text_box, box_pos)

        screen.blit(lines_surface, (0, 0))
        hub_group.draw(screen)

        if not drones_paused:
            drone_group.update(dt)
        drone_group.draw(screen)

        pygame.display.flip()

    pygame.quit()
