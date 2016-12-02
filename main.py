import pygame

SCREEN_HEIGHT = 800
SCREEN_WIDTH = 1280
FPS = 60


class Sprite(pygame.sprite.Sprite):
    image = None

    def __init__(self, *groups):
        super().__init__(*groups)
        self._img = pygame.image.load(self.image)
        self.rect = pygame

    def draw(self, screen):
        screen.blit(self._img, (self.x, self.y))


class Player(pygame.sprite.Sprite):
    HORIZONTAL_MOVE = 150
    VERTICAL_MOVE = 100
    img = 'art/ship.png'

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load(self.img)
        self.rect = pygame.rect.Rect((640, 650), self.image.get_size())
        self.dx = 0
        self.dy = 0

    def move_left(self, dt):
        self.dx = min(self.dx + 8, 300)
        self.rect.x = max(self.rect.x - (self.HORIZONTAL_MOVE + self.dx) * dt, 0)

    def move_right(self, dt):
        self.dx = max(self.dx - 8, -300)
        self.rect.x = min(self.rect.x + (self.HORIZONTAL_MOVE - self.dx) * dt,
                          SCREEN_WIDTH - self.rect.width)

    def move_forward(self, dt):
        self.dy = min(self.dy - 8, -80)
        self.rect.y = max(self.rect.y - (self.VERTICAL_MOVE - self.dy) * dt, 0)

    def move_backward(self, dt):
        self.dy = max(self.dy + 8, 80)
        self.rect.y = min(self.rect.y + (self.VERTICAL_MOVE + self.dy) * dt,
                          SCREEN_HEIGHT - self.rect.height)

    def update(self, dt, game):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.move_left(dt)

        if keys[pygame.K_d]:
            self.move_right(dt)

        if keys[pygame.K_w]:
            self.move_forward(dt)

        if keys[pygame.K_s]:
            self.move_backward(dt)


class Background(pygame.sprite.Sprite):
    img = 'art/spacefield.png'

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load(self.img)
        self.rect = pygame.rect.Rect((0, 0), self.image.get_size())


class Game(object):
    def run(self, screen):
        clock = pygame.time.Clock()

        sprites = pygame.sprite.Group()

        self.player = Player(sprites)
        self.background = pygame.image.load('art/spacefield.png')

        while True:
            dt = clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

            screen.blit(self.background, (0, 0))
            sprites.update(dt / 1000., self)
            sprites.draw(screen)
            pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game = Game()
    game.run(screen)
