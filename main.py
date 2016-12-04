from random import randrange, choice
from math import copysign
import pygame

SCREEN_HEIGHT = 1000
SCREEN_WIDTH = 1000
FPS = 60


class SpriteFactory(object):
    """
    A simple Sprite factory.

    Sprite classes must have an ``image_file`` attribute, and accept
    an image as thier first positional argument. All other arguments
    passed to the factory ``spawn`` method are passed to the sprite
    class's ``__init__`` method.

    """

    def __init__(self, sprite_class):
        self.sprite_class = sprite_class
        self.image_master = pygame.image.load(self.sprite_class.image_file)

    def spawn(self, *args, **kwargs):
        image = self.image_master.copy()
        return self.sprite_class(image, *args, **kwargs)


class Laser(pygame.sprite.Sprite):
    image_file = 'assets/ssr/PNG/Lasers/laserBlue07.png'

    def __init__(self, image, start_position, *groups, dy=400, dx=0):
        super().__init__(*groups)
        self.dy = dy
        self.dx = dx
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.midbottom = start_position

    def update(self, dt):
        self.rect.y -= self.dy * dt
        self.rect.x += self.dx * dt
        if self.rect.bottom < 0:
            self.kill()


class LaserHit(pygame.sprite.Sprite):
    image_file = 'assets/ssr/PNG/Lasers/laserBlue08.png'

    def __init__(self, image, position, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.lifespan = 0.15
        self.original_width = self.rect.width
        self.original_height = self.rect.height
        self.width_scale_factor = self.rect.width / self.lifespan
        self.height_scale_factor = self.rect.height / self.lifespan

    def update(self, dt):
        self.lifespan -= dt
        width = max(round(self.width_scale_factor * self.lifespan), 0)
        height = max(round(self.height_scale_factor * self.lifespan), 0)
        if not any((width, height)):
            self.kill()
            return
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect(center=self.rect.center)
        if self.lifespan < 0:
            self.kill()


class LaserHitFactory(object):
    def __init__(self):
        self.image_master = pygame.image.load('assets/ssr/PNG/Lasers/laserBlue08.png')

    def spawn(self, position, *groups):
        # adjust the position up a bit because it looks better
        position = (position[0], position[1] - 10)
        # rotate to a random angle
        angle = randrange(1, 360)
        image = pygame.transform.rotate(self.image_master, angle)
        return LaserHit(image, position, *groups)


class SpreadLaser(Laser):
    image_file = 'assets/ssr/PNG/Lasers/laserBlue08.png'

    def __init__(self, *args, **kwargs):
        self.angle = 0
        super().__init__(*args, **kwargs)
        self.image = pygame.transform.scale(self.image, (24, 23))
        self.image_master = self.image.copy()
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, dt):
        self.angle += 230 * dt
        self.image = pygame.transform.rotate(self.image_master, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        super().update(dt)


class Player(pygame.sprite.Sprite):
    HORIZONTAL_MOVE = 15
    VERTICAL_MOVE = 5
    img = 'assets/ssr/PNG/playerShip1_orange.png'
    max_level = 10

    def __init__(self, start_position, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load(self.img)
        self.rect = pygame.rect.Rect(start_position, self.image.get_size())
        self.collide = pygame.mixer.Sound('assets/sound/collide_1.wav')
        self.laser_1 = pygame.mixer.Sound('assets/sound/laser_1.wav')
        self.q_sound = pygame.mixer.Sound('assets/sound/laser_3.wav')
        self.burst_effect = pygame.mixer.Sound('assets/sound/burst.wav')
        self.powerup_sound = pygame.mixer.Sound('assets/sound/powerup_1.wav')
        self.laser_factory = SpriteFactory(Laser)
        self.spread_laser_factory = SpriteFactory(SpreadLaser)
        self.laser_1_cooldown = 0.2
        self.laser_1_cooldown_state = 0
        self.burst_cooldown = 5
        self.burst_cooldown_state = 0
        self.q_cooldown = 5
        self.q_cooldown_state = 0
        self.burst_force = 250
        self.dx = 0
        self.dy = 0
        self.level = 1

    def thrust_left(self, dt):
        self.dx -= self.HORIZONTAL_MOVE

    def thrust_right(self, dt):
        self.dx += self.HORIZONTAL_MOVE

    def thrust_forward(self, dt):
        self.dy -= self.VERTICAL_MOVE

    def thrust_backward(self, dt):
        self.dy += self.VERTICAL_MOVE

    def shoot(self, game):
        if self.laser_1_cooldown_state > 0:
            return
        self.laser_1.play()
        self.laser_1_cooldown_state = self.laser_1_cooldown
        if self.level < 4:
            game.lasers.add(self.laser_factory.spawn(self.rect.midtop))
        else:
            game.lasers.add(self.laser_factory.spawn(self.rect.midleft))
            game.lasers.add(self.laser_factory.spawn(self.rect.midright))

    def q(self, game):
        if self.q_cooldown_state == 0:
            self.q_sound.play()
            self.q_cooldown_state = self.q_cooldown
            game.lasers.add(self.spread_laser_factory.spawn(self.rect.topleft, dy=70, dx=-330))
            game.lasers.add(self.spread_laser_factory.spawn(self.rect.topright, dy=70, dx=330))

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

    def powerup(self):
        if self.level < self.max_level:
            self.level += 1
            self.powerup_sound.play()
            self.laser_1_cooldown -= 0.01

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

        if keys[pygame.K_q]:
            self.q(game)

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
        self.q_cooldown_state = max(self.q_cooldown_state - dt, 0)


class Enemy(pygame.sprite.Sprite):
    points = 100
    image_file = 'assets/ssr/PNG/Enemies/enemyBlack3.png'

    def __init__(self, image, start_position, *groups, dy=50):
        super().__init__(*groups)
        self.dy = dy
        self.image = image
        self.rect = pygame.rect.Rect(start_position, self.image.get_size())
        self.explosion_sound = pygame.mixer.Sound('assets/sound/explosion_1.wav')
        self.hp = 1

    def update(self, dt):
        self.rect.y += self.dy * dt
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def hit(self):
        self.hp -= 1
        if self.hp == 0:
            self.destroy()
            return True
        return False

    def destroy(self):
        self.explosion_sound.play()
        self.kill()


class BiggerEnemy(Enemy):
    points = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hp = 2


class EnemyFactory(object):
    def __init__(self):
        sf = 0.8
        scale = (int(103 * sf), int(84 * sf))
        self.images = {
            'black': pygame.transform.scale(pygame.image.load('assets/ssr/PNG/Enemies/enemyBlack3.png'), scale),
            'blue': pygame.transform.scale(pygame.image.load('assets/ssr/PNG/Enemies/enemyBlue3.png'), scale),
            'green': pygame.transform.scale(pygame.image.load('assets/ssr/PNG/Enemies/enemyGreen3.png'), scale),
        }

    def spawn(self, position, *groups, color=None, **kwargs):
        if color is None:
            color = choice(list(self.images.keys()))
        image = self.images[color].copy()
        return Enemy(image, position, *groups, **kwargs)


class BiggerEnemyFactory(object):
    def __init__(self):
        self.images = {
            'black': pygame.image.load('assets/ssr/PNG/Enemies/enemyBlack4.png'),
            'blue': pygame.image.load('assets/ssr/PNG/Enemies/enemyBlue4.png'),
            'green': pygame.image.load('assets/ssr/PNG/Enemies/enemyGreen4.png'),
        }

    def spawn(self, position, *groups, color=None, **kwargs):
        if color is None:
            color = choice(list(self.images.keys()))
        image = self.images[color].copy()
        return BiggerEnemy(image, position, *groups, **kwargs)


class Star(object):
    def __init__(self, screen):
        self.screen = screen
        self.y = randrange(0, screen.get_height() - 1)
        self._randomize()

    def _randomize(self):
        self.x = randrange(0, self.screen.get_width())
        self.dy, self.size, self.color = choice([
            (4, 1, (100, 100, 100)),
            (6, 1, (120, 120, 120)),
            (8, 1, (180, 180, 180))
        ])

    def draw(self):
        self.screen.fill(self.color, (self.x, self.y, self.size, self.size))

    def update(self, dt):
        self.y += self.dy * dt
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
        color = choice(['black', 'blue', 'green'])
        speed = randrange(120, 200, 10)
        for _ in range(randrange(0, 3)):
            position = (randrange(0, (SCREEN_WIDTH - 90)),
                        randrange(-200, -100))
            self.enemy_factory.spawn(position, self.enemies, color=color, dy=speed)
        position = (randrange(0, (SCREEN_WIDTH - 90)),
                    randrange(-200, -100))
        self.bigger_enemy_factory.spawn(position, self.enemies, color=color, dy=speed)

    def run(self, screen):
        stats = False
        clock = pygame.time.Clock()
        player_score = 0
        player_powerup = 0

        sprites = pygame.sprite.Group()
        effects = pygame.sprite.Group()
        hit_factory = LaserHitFactory()
        self.enemy_factory = EnemyFactory()
        self.bigger_enemy_factory = BiggerEnemyFactory()

        self.enemies = pygame.sprite.Group()
        self.lasers = pygame.sprite.Group()

        self.player = Player((SCREEN_WIDTH / 2, 650), sprites)

        background = pygame.image.load('assets/art/spacefield1600x1000.png')
        starfield = Starfield(screen)
        show_starfield = True

        font = pygame.font.Font('assets/fonts/ShareTechMono-Regular.ttf', 16, bold=True)
        score_font = pygame.font.Font('assets/ssr/Bonus/kenvector_future.ttf', 20)

        background_music = pygame.mixer.Sound('assets/sound/music/DigitalNativeLooped.ogg')
        # background_music = pygame.mixer.Sound('assets/sound/music/techno_gameplay_loop.ogg')
        background_music.set_volume(0.9)
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
            effects.update(dt)

            # Game Logic
            hits = pygame.sprite.groupcollide(self.enemies, self.lasers, False, True)
            for enemy, lasers in hits.items():
                # Hit effect
                laser = lasers[0]
                hit_factory.spawn(laser.rect.midtop, effects)
                is_destroyed = enemy.hit()
                if is_destroyed:
                    player_score += enemy.points
                    player_powerup += enemy.points

            if player_powerup > 5000:
                self.player.powerup()
                player_powerup = 0

            # Draw
            screen.blit(background, (0, 0))
            if show_starfield:
                starfield.update(dt)
            self.enemies.draw(screen)
            self.lasers.draw(screen)
            sprites.draw(screen)
            effects.draw(screen)

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
