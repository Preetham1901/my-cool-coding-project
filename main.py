import pygame

pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Move the Red Square!")

# Square properties
square_size = 40
square = pygame.Rect(180, 130, square_size, square_size)
speed = 5

# Clock to control frame rate
clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Handle continuous arrow key presses for smooth movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        square.x -= speed
    if keys[pygame.K_RIGHT]:
        square.x += speed
    if keys[pygame.K_UP]:
        square.y -= speed
    if keys[pygame.K_DOWN]:
        square.y += speed

    # Keep square within the window boundaries
    square.clamp_ip(screen.get_rect())

    # Drawing
    screen.fill((0, 150, 255))
    pygame.draw.rect(screen, (255, 0, 0), square)
    pygame.display.flip()

    # Limit to 60 frames per second
    clock.tick(60)

pygame.quit()
