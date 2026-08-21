from typing import Optional, Tuple, Dict, List
import pygame
from parser import Config, Hub


W_WIDTH = 1750
W_HEIGHT = 880


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


def make_grid(
    hubs: List[Hub]
) -> Dict[Tuple[int, int], Tuple[float, float]]:
    grid: Dict[Tuple[int, int], Tuple[float, float]] = {}
    x_padding, y_padding = 200, 200

    min_x = min(hub.x for hub in hubs)
    max_x = max(hub.x for hub in hubs)
    min_y = min(hub.y for hub in hubs)
    max_y = max(hub.y for hub in hubs)

    width_cells = max_x - min_x + 1
    height_cells = max_y - min_y + 1

    cell_width = (W_WIDTH - x_padding) / width_cells
    cell_height = (W_HEIGHT - y_padding) / height_cells
    cell_size = min(cell_width, cell_height)
    if cell_size > 150.0:
        cell_size = 150.0

    grid_width = cell_size * width_cells
    grid_height = cell_size * height_cells

    o_x = (W_WIDTH - grid_width) / 2
    o_y = (W_HEIGHT - grid_height) / 2

    for hub in hubs:
        grid_x = hub.x - min_x
        grid_y = hub.y - min_y

        pixel_x = o_x + grid_x * cell_size + cell_size / 2
        pixel_y = o_y + (height_cells - grid_y - 1) * cell_size + cell_size / 2

        grid[(hub.x, hub.y)] = (pixel_x, pixel_y)

    return grid


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


def gui(config: Config) -> None:
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((W_WIDTH, W_HEIGHT))
    running = True

    pygame.display.set_caption("Fly-in")

    bg_surface = pygame.image.load("sky.jpg").convert()
    bg_surface = pygame.transform.scale(bg_surface, (W_WIDTH, W_HEIGHT))
    bg_x_pos: float = 0.0

    all_hubs = config.hubs.copy()
    all_hubs.extend((config.start_hub, config.end_hub))

    hub_sprites = pygame.sprite.Group()
    grid = make_grid(all_hubs)

    for hub in all_hubs:
        pos = grid[(hub.x, hub.y)]
        sprite = HubSprite(hub, pos)
        hub_sprites.add(sprite)

    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        bg_x_pos = animate_bg(screen, bg_surface, bg_x_pos, dt)

        hub_sprites.draw(screen)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

        pygame.display.flip()

    pygame.quit()
