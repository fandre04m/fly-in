import pygame


W_WIDTH = 1260
W_HEIGH = 720


pygame.init()
screen = pygame.display.set_mode((W_WIDTH, W_HEIGH))
pygame.display.set_caption("Fly-in")
clock = pygame.time.Clock()
running = True

bg_surface = pygame.image.load("sky.jpg")
bg_surface = pygame.transform.scale(bg_surface, (W_WIDTH, W_HEIGH))

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.blit(bg_surface, (0, 0))

    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
