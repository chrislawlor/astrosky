import os
from random import randrange, choice
from math import copysign
import pygame

SCREEN_HEIGHT = 960
SCREEN_WIDTH = 640
SCREEN_RECT = pygame.rect.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
FPS = 60


_image_cache = {}


def load_image(path):
    if path not in _image_cache:
        local_path = os.path.join(*path.split("/"))
        image = pygame.image.load(local_path).convert_alpha()
        _image_cache[path] = image
    return _image_cache[path].copy()


class LaserUpdateMixin(object):
    """
    Updates sprite positions, and destroys them when they leave the
    top of the screen.

    Must go first in MRO, since ``pygame.sprite.Sprite`` provides a
    no-op ``update`` method.
    """

    def update(self, dt):
        self.rect.x, self.rect.y = (
            (self.rect.x + self.dx * dt),
            (self.rect.y + self.dy * dt)
        )
        if self.rect.bottom < 0:
            self.kill()


class Laser(LaserUpdateMixin, pygame.sprite.Sprite):

    def __init__(self, start_position, *groups, dy=-400, dx=0):
        super().__init__(*groups)
        self.dy = dy
        self.dx = dx
        self.image = load_image('assets/ssr/PNG/Lasers/laserBlue07.png')
        self.rect = self.image.get_rect()
        self.rect.midbottom = start_position


class LaserHit(pygame.sprite.Sprite):
    image_file = 'assets/ssr/PNG/Lasers/laserBlue08.png'

    def __init__(self, position, *groups):
        super().__init__(*groups)
        image = load_image('assets/ssr/PNG/Lasers/laserBlue08.png')
        angle = randrange(1, 360)
        self.image = pygame.transform.rotate(image, angle)
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


class SpreadLaser(LaserUpdateMixin, pygame.sprite.Sprite):
    image_file = 'assets/ssr/PNG/Lasers/laserBlue08.png'

    def __init__(self, position, *groups, dx=0, dy=-400):
        super().__init__(*groups)
        self.dx, self.dy = dx, dy
        self.angle = 0
        image = load_image('assets/ssr/PNG/Lasers/laserBlue08.png')
        self.image_master = pygame.transform.scale(image, (24, 23))
        self.image = self.image_master
        self.rect = pygame.rect.Rect(position, self.image.get_size())

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
        self.image = load_image(self.img)
        self.rect = pygame.rect.Rect(start_position, self.image.get_size())
        self.collide = pygame.mixer.Sound('assets/sound/collide_1.wav')
        self.laser_1 = pygame.mixer.Sound('assets/sound/laser_1.wav')
        self.q_sound = pygame.mixer.Sound('assets/sound/laser_3.wav')
        self.burst_effect = pygame.mixer.Sound('assets/sound/burst.wav')
        self.powerup_sound = pygame.mixer.Sound('assets/sound/powerup_1.wav')
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
            game.lasers.add(Laser(self.rect.midtop))
        else:
            game.lasers.add(Laser(self.rect.midleft))
            game.lasers.add(Laser(self.rect.midright))

    def q(self, game):
        if self.q_cooldown_state == 0:
            self.q_sound.play()
            self.q_cooldown_state = self.q_cooldown
            game.lasers.add(SpreadLaser(self.rect.topleft, dy=-70, dx=-330))
            game.lasers.add(SpreadLaser(self.rect.topright, dy=-70, dx=330))

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
            'black': pygame.transform.scale(load_image('assets/ssr/PNG/Enemies/enemyBlack3.png'), scale),
            'blue': pygame.transform.scale(load_image('assets/ssr/PNG/Enemies/enemyBlue3.png'), scale),
            'green': pygame.transform.scale(load_image('assets/ssr/PNG/Enemies/enemyGreen3.png'), scale),
        }

    def spawn(self, position, *groups, color=None, **kwargs):
        if color is None:
            color = choice(list(self.images.keys()))
        image = self.images[color].copy()
        return Enemy(image, position, *groups, **kwargs)


class BiggerEnemyFactory(object):
    def __init__(self):
        self.images = {
            'black': load_image('assets/ssr/PNG/Enemies/enemyBlack4.png'),
            'blue': load_image('assets/ssr/PNG/Enemies/enemyBlue4.png'),
            'green': load_image('assets/ssr/PNG/Enemies/enemyGreen4.png'),
        }

    def spawn(self, position, *groups, color=None, **kwargs):
        if color is None:
            color = choice(list(self.images.keys()))
        image = self.images[color].copy()
        return BiggerEnemy(image, position, *groups, **kwargs)


class Star(object):
    def __init__(self, bounds):
        self.bounds = bounds
        self.y = randrange(self.bounds.top, self.bounds.bottom - 1)
        self._randomize()

    def _randomize(self):
        self.x = randrange(self.bounds.left, self.bounds.right)
        self.dy, self.size, self.color = choice([
            (4, 1, (100, 100, 100)),
            (6, 1, (120, 120, 120)),
            (8, 1, (180, 180, 180))
        ])

    def draw(self, screen):
        screen.fill(self.color, (self.x, self.y, self.size, self.size))

    def update(self, dt):
        self.y += self.dy * dt
        if self.y >= self.bounds.bottom:
            self.y = self.bounds.top
            self._randomize()


class Starfield(object):
    def __init__(self, bounding_rect, max_stars=300):
        self.stars = []
        for _ in range(max_stars):
            star = Star(bounding_rect)
            self.stars.append(star)

    def update(self, dt):
        for star in self.stars:
            star.update(dt)

    def draw(self, screen):
        for star in self.stars:
            star.draw(screen)


class Background(object):
    def __init__(self):
        # super().__init__(*groups)
        self.image = load_image('assets/art/spacefield1600x1000.png')
        self.rect = pygame.rect.Rect((0, 0), self.image.get_size())
        self.rect.centerx = SCREEN_RECT.centerx
        self.starfield = Starfield(self.rect)
        self.show_starfield = True

    def update(self, dt, player):
        player_offset = SCREEN_RECT.centerx - player.rect.centerx
        self.rect.centerx = SCREEN_RECT.centerx + (player_offset * 0.03)
        if self.show_starfield:
            self.starfield.update(dt)

    def draw(self, screen):
        surface = pygame.Surface(self.rect.size)
        surface.blit(self.image, (0, 0))
        if self.show_starfield:
            self.starfield.draw(surface)
        screen.blit(surface, self.rect)

    def toggle_starfield(self):
        self.show_starfield = not self.show_starfield


class ScoreDisplay(object):
    def __init__(self, text, position, ttl=0.7):
        self.text, self.position, self.ttl = text, position, ttl
        self.color = (200, 200, 200)

    def draw(self, font, screen):
        surface = font.render(self.text, True, self.color)
        surface.set_alpha(150)
        screen.blit(surface, self.position)


class ScoreDisplayGroup(object):
    def __init__(self):
        self.font = pygame.font.Font('assets/ssr/Bonus/kenvector_future.ttf', 20)
        self.scores = []

    def add(self, text, position):
        self.scores.append(ScoreDisplay(text, position))

    def update(self, dt):
        # this is kinda ugly, but we update the ttl and remove dead scores
        # all in one shot.
        new_scores = []
        for score in self.scores:
            score.ttl -= dt
            if score.ttl > 0:
                new_scores.append(score)
        self.scores = new_scores

    def draw(self, screen):
        for score in self.scores:
            score.draw(self.font, screen)


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

        self.background = Background()

        effects = pygame.sprite.Group()
        self.enemy_factory = EnemyFactory()
        self.bigger_enemy_factory = BiggerEnemyFactory()

        self.enemies = pygame.sprite.Group()
        self.lasers = pygame.sprite.Group()
        score_display_group = ScoreDisplayGroup()

        self.player = Player((SCREEN_WIDTH / 2, 650), sprites)

        font = pygame.font.Font('assets/fonts/ShareTechMono-Regular.ttf', 16, bold=True)
        score_font = pygame.font.Font('assets/ssr/Bonus/kenvector_future.ttf', 25)

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
            dt = clock.tick(FPS) / 1000.

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_F1:
                        stats = not stats
                    if event.key == pygame.K_F2:
                        self.background.toggle_starfield()
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
            self.background.update(dt, self.player)
            self.lasers.update(dt)
            sprites.update(dt, self)
            self.enemies.update(dt)
            effects.update(dt)
            score_display_group.update(dt)

            # Game Logic
            hits = pygame.sprite.groupcollide(self.enemies, self.lasers, False, True)
            for enemy, lasers in hits.items():
                # Hit effect
                laser = lasers[0]
                LaserHit(laser.rect.midtop, effects)
                is_destroyed = enemy.hit()
                if is_destroyed:
                    player_score += enemy.points
                    player_powerup += enemy.points
                    score_display_group.add(str(enemy.points), enemy.rect.midleft)

            if player_powerup > 5000:
                self.player.powerup()
                player_powerup = 0

            # Draw
            self.background.draw(screen)
            self.enemies.draw(screen)
            self.lasers.draw(screen)
            sprites.draw(screen)
            effects.draw(screen)
            score_display_group.draw(screen)

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
