from random import randrange, choice
from math import copysign
import pygame

SCREEN_HEIGHT = 1000
SCREEN_WIDTH = 1000
FPS = 60


class Laser(pygame.sprite.Sprite):
    def __init__(self, start_position, *groups, dy=200):
        super().__init__(*groups)
        self.dy = dy
        self.image = pygame.image.load('assets/ssr/PNG/Lasers/laserBlue07.png')
        self.rect = self.image.get_rect()
        self.rect.midbottom = start_position

    def update(self, dt):
        self.rect.y -= self.dy * dt
        if self.rect.bottom < 0:
            self.kill()


class Player(pygame.sprite.Sprite):
    HORIZONTAL_MOVE = 15
    VERTICAL_MOVE = 5
    img = 'assets/ssr/PNG/playerShip1_orange.png'

    def __init__(self, start_position, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load(self.img)
        self.rect = pygame.rect.Rect(start_position, self.image.get_size())
        self.collide = pygame.mixer.Sound('assets/sound/collide_1.wav')
        self.laser_1 = pygame.mixer.Sound('assets/sound/laser_1.wav')
        self.burst_effect = pygame.mixer.Sound('assets/sound/burst.wav')
        self.laser_1_cooldown = 0.3
        self.laser_1_cooldown_state = 0
        self.burst_cooldown = 5
        self.burst_cooldown_state = 0
        self.burst_force = 250
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

    def shoot(self, game):
        if self.laser_1_cooldown_state == 0:
            self.laser_1.play()
            self.laser_1_cooldown_state = self.laser_1_cooldown
            game.lasers.add(Laser(self.rect.midtop))

    def burst(self):
        """
        A burst of speed in whatever direction the player is moving.
        """
        if self.burst_cooldown_state == 0:
            self.burst_effect.play()
            self.burst_cooldown_state = self.burst_cooldown
            self.dx, self.dy = (
                (copysign(self.dx + self.burst_force, self.dx)),
                (copysign(self.dy + self.burst_force, self.dy))
            )

    def update(self, dt, game):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.thrust_left(dt)

        if keys[pygame.K_RIGHT]:
            self.thrust_right(dt)

        if keys[pygame.K_UP]:
            self.thrust_forward(dt)

        if keys[pygame.K_DOWN]:
            self.thrust_backward(dt)

        if keys[pygame.K_LSHIFT]:
            self.shoot(game)

        if keys[pygame.K_SPACE]:
            self.burst()

        self.rect.x, self.rect.y = (
            (self.rect.x + self.dx * dt),
            (self.rect.y + self.dy * dt)
        )

        # Bounce off the sides of the screen, and reduce absolute velocity.
        # If the hit is hard enough, play collision sound
        if (self.rect.right > SCREEN_WIDTH and self.dx > 0) or (self.rect.left < 0 and self.dx < 0):
            if abs(self.dx) > 400:
                self.collide.play()
            self.dx = round(-(self.dx + (0 - self.dx / 2)))

        if self.rect.top < 0 or self.rect.bottom > SCREEN_HEIGHT:
            self.dy = 0

        # Adjust cooldowns
        self.laser_1_cooldown_state = max(self.laser_1_cooldown_state - dt, 0)
        self.burst_cooldown_state = max(self.burst_cooldown_state - dt, 0)


class Enemy(pygame.sprite.Sprite):
    points = 100
    image_file = 'assets/ssr/PNG/Enemies/enemyBlack3.png'

    def __init__(self, start_position, *groups, dy=50):
        super().__init__(*groups)
        self.dy = dy
        self.image = pygame.image.load(self.image_file)
        self.rect = pygame.rect.Rect(start_position, self.image.get_size())
        self.explosion_sound = pygame.mixer.Sound('assets/sound/explosion_1.wav')

    def update(self, dt):
        self.rect.y += self.dy * dt

    def destroy(self):
        self.explosion_sound.play()
        self.kill()


class Star(object):
    def __init__(self, screen):
        self.screen = screen
        self.y = randrange(0, screen.get_height() - 1)
        self._randomize()

    def _randomize(self):
        self.x = randrange(0, self.screen.get_width())
        self.dx, self.size, self.color = choice([
            (4, 1, (100, 100, 100)),
            (6, 1, (120, 120, 120)),
            (8, 1, (180, 180, 180))
        ])

    def draw(self):
        self.screen.fill(self.color, (self.x, self.y, self.size, self.size))

    def update(self, dt):
        self.y += self.dx * dt
        if self.y >= self.screen.get_height():
            self.y = 0
            self._randomize()


class Starfield(object):
    def __init__(self, screen, max_stars=300):
        self.stars = []
        self.screen = screen
        for _ in range(max_stars):
            star = Star(self.screen)
            self.stars.append(star)

    def update(self, dt):
        for star in self.stars:
            star.update(dt)
            star.draw()


class Game(object):
    def add_random_enemies(self):
        for _ in range(randrange(1, 4)):
            position = (randrange(0, (SCREEN_WIDTH - 70)), -100)
            speed = randrange(90, 170, 10)
            Enemy(position, self.enemies, dy=speed)

    def run(self, screen):
        stats = False
        clock = pygame.time.Clock()
        player_score = 1000000
        player_powerup = 0

        sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.lasers = pygame.sprite.Group()

        self.player = Player((SCREEN_WIDTH / 2, 650), sprites)

        background = pygame.image.load('assets/art/spacefield1600x1000.png')
        starfield = Starfield(screen)
        show_starfield = True

        font = pygame.font.Font('assets/fonts/ShareTechMono-Regular.ttf', 16, bold=True)
        score_font = pygame.font.Font('assets/ssr/Bonus/kenvector_future.ttf', 20)

        background_music = pygame.mixer.Sound('assets/sound/music/DigitalNativeLooped.ogg')
        background_music.set_volume(0.9)
        powerup_sound = pygame.mixer.Sound('assets/sound/powerup_1.wav')
        background_music.play(loops=-1, fade_ms=2000)

        paused = False
        enemy_cooldown = 4
        enemy_cooldown_state = 0
        enemy_cooldown_timer = 10  # how often we reduce the cooldown
        enemy_cooldown_timer_state = 0

        while True:
            dt = clock.tick(FPS) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_F1:
                        stats = not stats
                    if event.key == pygame.K_F2:
                        show_starfield = not show_starfield
                    if event.key == pygame.K_MINUS:
                        background_music.set_volume(background_music.get_volume() - 0.1)
                    if event.key == pygame.K_EQUALS:
                        background_music.set_volume(background_music.get_volume() + 0.1)
                    if event.key == pygame.K_p:
                        paused = not paused

            if paused:
                continue

            # Spawn Enemies
            if enemy_cooldown_state <= 0:
                self.add_random_enemies()
                enemy_cooldown_state = enemy_cooldown
            if enemy_cooldown_timer_state <= 0:
                enemy_cooldown_timer_state = enemy_cooldown_timer
                # progressively faster spawn times
                enemy_cooldown = max(enemy_cooldown - 0.2, 0.6)
            enemy_cooldown_state -= dt
            enemy_cooldown_timer_state -= dt

            # Sprite Updates
            self.lasers.update(dt)
            sprites.update(dt, self)
            self.enemies.update(dt)
            self.lasers.update(dt)

            # Draw
            screen.blit(background, (0, 0))
            if show_starfield:
                starfield.update(dt)
            self.enemies.draw(screen)
            self.lasers.draw(screen)
            sprites.draw(screen)

            # Game Logic
            hits = pygame.sprite.groupcollide(self.enemies, self.lasers, False, True)
            for enemy in hits.keys():
                player_score += enemy.points
                player_powerup += enemy.points
                enemy.destroy()

            if player_powerup > 5000:
                powerup_sound.play()
                self.player.laser_1_cooldown = max(0.2, self.player.laser_1_cooldown - 0.012)
                player_powerup = 0

            # Display

            score_display = score_font.render('{:,}'.format(player_score), True, (200, 200, 200))
            display_width = score_display.get_width()
            display_x = SCREEN_WIDTH - 10 - display_width
            screen.blit(score_display, (display_x, 10))

            if stats:
                lines = [
                    "FPS {:.0f}".format(clock.get_fps()),
                    "Player dx={:+} dy={:+}".format(self.player.dx, self.player.dy),
                    "Laser Atk Speed {:.3f}".format(self.player.laser_1_cooldown),
                    "Wave Spawn Interval {:.3f}".format(enemy_cooldown),
                ]
                pixel_offset = 10
                for line in lines:
                    surface = font.render(line, True, (200, 200, 200))
                    screen.blit(surface, (10, pixel_offset))
                    pixel_offset += 20
            pygame.display.flip()


if __name__ == '__main__':
    pygame.mixer.pre_init(buffer=1024)
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game = Game()
    game.run(screen)
