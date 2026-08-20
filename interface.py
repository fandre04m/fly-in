from typing import Optional, Tuple, Dict, List
import pygame
from parser import Config, Hub


W_WIDTH = 1920
W_HEIGHT = 1010


class HubSprite(pygame.sprite.Sprite):
    def __init__(self, hub: Hub, pos: Tuple[float, float]) -> None:
        super().__init__()
        self.name: str = hub.name
        self.pos: Tuple[float, float] = pos
        self.color: Optional[str] = hub.metadata.color

        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)

        pygame.draw.circle(
            self.image,
            self.color,
            self.image.get_rect().center,
            19
        )
        pygame.draw.circle(
            self.image,
            "black",
            self.image.get_rect().center,
            20,
            2
        )


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
