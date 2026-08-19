from typing import Optional, Tuple
import pygame
from parser import Config, Hub


W_WIDTH = 1260
W_HEIGHT = 720


class HubSprite(pygame.sprite.Sprite):
    def __init__(self, hub: Hub, pos: Tuple[float, float]) -> None:
        super().__init__()
        self.name: str = hub.name
        self.pos: Tuple[float, float] = pos
        self.color: Optional[str] = hub.metadata.color + "3"

        self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)

        pygame.draw.circle(
            self.image,
            self.color,
            self.image.get_rect().center,
            28
        )
        pygame.draw.circle(
            self.image,
            "black",
            self.image.get_rect().center,
            30,
            3
        )


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

    hub_sprites = pygame.sprite.Group()
    hub_sprites.add(HubSprite(config.hubs[0], (W_WIDTH / 3, W_HEIGHT / 2)))
    hub_sprites.add(HubSprite(config.hubs[-1], (W_WIDTH * 2 / 3, W_HEIGHT / 2)))

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
