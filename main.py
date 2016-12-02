import pygame

SCREEN_HEIGHT = 800
SCREEN_WIDTH = 1280
FPS = 60
DEBUG = False


class Player(pygame.sprite.Sprite):
    HORIZONTAL_MOVE = 15
    VERTICAL_MOVE = 5
    img = 'art/ship.png'

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load(self.img)
        self.rect = pygame.rect.Rect((640, 650), self.image.get_size())
        self.dx = 0
        self.dy = 0

    def thrust_left(self, dt):
        self.dx -= self.HORIZONTAL_MOVE

    def thrust_right(self, dt):
        self.dx += self.HORIZONTAL_MOVE

    def thrust_forward(self, dt):
        self.dy -= self.VERTICAL_MOVE

    def thrust_backward(self, dt):
        self.dy += self.VERTICAL_MOVE

    def update(self, dt, game):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.thrust_left(dt)

        if keys[pygame.K_d]:
            self.thrust_right(dt)

        if keys[pygame.K_w]:
            self.thrust_forward(dt)

        if keys[pygame.K_s]:
            self.thrust_backward(dt)

        self.rect.x += self.dx * dt
        self.rect.y += self.dy * dt

        if self.rect.right > SCREEN_WIDTH and self.dx > 0:
            self.dx = -self.dx + abs(self.dx / 2)

        if self.rect.left < 0 and self.dx < 0:
            self.dx = -self.dx - abs(self.dx / 2)

        if self.rect.top < 0 or self.rect.bottom > SCREEN_HEIGHT:
            self.dy = 0

        if DEBUG:
            print("Player.dx = {}, dy = {}".format(self.dx, self.dy))


class Game(object):
    def run(self, screen):
        clock = pygame.time.Clock()

        sprites = pygame.sprite.Group()

        self.player = Player(sprites)
        background = pygame.image.load('art/spacefield.png')

        while True:
            dt = clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

            screen.blit(background, (0, 0))
            sprites.update(dt / 1000., self)
            sprites.draw(screen)
            pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game = Game()
    game.run(screen)
