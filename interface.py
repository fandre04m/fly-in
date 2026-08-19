import pygame


W_WIDTH = 1260
W_HEIGHT = 720


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


def run() -> None:
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((W_WIDTH, W_HEIGHT))
    running = True

    pygame.display.set_caption("Fly-in")

    bg_surface = pygame.image.load("sky.jpg").convert()
    bg_surface = pygame.transform.scale(bg_surface, (W_WIDTH, W_HEIGHT))
    bg_x_pos: float = 0.0

    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        bg_x_pos = animate_bg(screen, bg_surface, bg_x_pos, dt)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

        pygame.display.flip()

    pygame.quit()


run()
