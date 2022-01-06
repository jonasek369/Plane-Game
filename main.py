import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass
from enum import Enum, auto

import pygame
from colorama import Fore
from colorama import Style
from win32api import GetSystemMetrics

pygame.init()
pygame.font.init()
myfont = pygame.font.SysFont('Arial', 24)
SCREENW, SCREENH = 1280, 720

WORKING_DIR = os.getcwd()
assert os.path.exists(
    WORKING_DIR + "\\" + "data"), "Could not file data folder please open exe file in same folder as where is located data folder"
DATA_DIR = WORKING_DIR + "\\" + "data"

controls_js = None
running = True
SCALE = 1
screen = pygame.display.set_mode([SCREENW, SCREENH])
clock = pygame.time.Clock()

FPS = 240

BULLET_LIFETIME = 5
BULLET_SPEED = 10000

entities = []
bullets = []
sprite_list = []

CAMERA_X = 0
CAMERA_Y = 0

PLAYERSIZE = 25

ENEMY_SIZE = 25
ENEMY_DEPTH = 5
ENEMY_SPEED = 400

RAY_LEN = 250

FREEZE = False
FREEZE_CD = 0.3
FREEZE_LC = 0

ANGLE_ADDER = 1.75
MOTOR_MINUSER = 50

NEEDED_KEYS = {}
AMMO_INFO = {}

IMPLEMENTED_AMMOTYPES = ["20", "303"]

try:
    with open(WORKING_DIR + "\\" + "data" + "\\" + "NeededKeys.json", "r") as file:
        NEEDED_KEYS = json.loads(file.read())
except Exception as e:
    raise Exception("??: Unknown Exception: ", e)

assert "KEYS" in NEEDED_KEYS.keys(), "LINE: ~58~ -> Could not load file needed keys from data folder make sure you openening exe in same folder as where is data folder "

with open(DATA_DIR + "\\Settings\\AmmoTypes.json", "r") as file:
    AMMO_INFO = json.loads(file.read())

for ammotype in IMPLEMENTED_AMMOTYPES:
    assert ammotype in AMMO_INFO, "AmmoTypes.json is not new enough"

if GetSystemMetrics(43) > 3:
    buttons = 5
else:
    buttons = 3

Vector2 = pygame.math.Vector2
Vector3 = pygame.math.Vector3


@dataclass
class LogTypes:
    """
    tuple[prefix, color]
    tuple[str, tuple]
    """
    ERROR: tuple[str, tuple] = ("[ERROR]", (255, 0, 0))
    WARNING: tuple[str, tuple] = ("[WARNING]", (238, 210, 2))
    INFO: tuple[str, tuple] = ("[INFO]", (173, 216, 230))
    SUCCESS: tuple[str, tuple] = ("[SUCCESS]", (0, 255, 0))


class EnemyState(Enum):
    WONDERING = auto()
    ATTACKING = auto()
    IDLING = auto()


def random_color():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def distance(x1, x2, y1, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def colored(rgb, text):
    return Fore.WHITE + "\033[38;2;{};{};{}m{} \033[38;2;255;255;255m".format(rgb[0], rgb[1], rgb[2],
                                                                              text) + Style.RESET_ALL


def calculate_angle(fpos, spos):
    xA, yA = fpos[0], fpos[1]
    xB, yB = spos[0], spos[1]
    y = yB - yA
    x = xB - xA
    return math.atan2(y, x)


def percentage(whole, percts):
    return (whole / 100) * percts


def get_percentage(whole, number):
    return number / (whole / 100)


class Bullet:
    def __init__(self, angle, startx, starty):
        self.BORNED = time.time()
        self.angle = angle
        self.alive = True
        self.pos = [startx, starty]

    def update(self, dt):
        if FREEZE:
            return
        self.pos[0] += math.cos(self.angle) * BULLET_SPEED * dt
        self.pos[1] += math.sin(self.angle) * BULLET_SPEED * dt
        for i in entities:
            if i.rect.collidepoint(self.pos):
                i.alive = False
                self.alive = False

    def render(self, scr):
        pygame.draw.circle(scr, (255, 255, 0), self.pos, 1)


class SpriteSheet:
    def __init__(self, image):
        self.sheet = image

    def get_image(self, frame, width, height, scale):
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), ((frame * width), 0, width, height))
        image = pygame.transform.scale(image, (width * scale, height * scale))
        return image


def circles_collide(circle1, circle2):
    return circle1.pos.distance_to(circle2.pos) <= circle1.radius + circle2.radius


class Circle:
    def __init__(self, pos: Vector2, radius):
        self.pos = pos
        self.radius = radius

    def draw(self):
        pygame.draw.circle(screen, (0, 0, 255), self.pos, self.radius)


class Player:
    def __init__(self, sprite_info):
        self.position = [SCREENW // 2, SCREENH // 2]
        self.angle = -math.pi / 2
        self.deltas = [math.cos(self.angle), math.sin(self.angle)]
        self.motor_percentage = 70

        self.guns = {

        }

        self.hitboxes_hp = {}
        self.hitbox_circle = None

        self.alive = True
        assert sprite_info is not None, "Class Player -> param: spritename -> Error: This parameter cant be None"
        self.sprite_info = {"PLANE_TIMER": time.time()}
        self.load_sprite_info(sprite_info)
        self.sprite = pygame.image.load(DATA_DIR + self.sprite_info["SPRITE_LOCATION"]).convert()
        self.spritesheet = SpriteSheet(self.sprite)

    def fire(self):
        for ammotype in self.guns:
            bullet_damage = AMMO_INFO[ammotype]["DAMAGE"]
            bullet_speed = AMMO_INFO[ammotype]["SPEED"]
            if self.guns[ammotype]["LAST_SHOT"] + self.guns[ammotype]["TIMEOUT"] <= time.time():
                if self.guns[ammotype]["RESERVE"] <= 0:
                    continue
                self.guns[ammotype]["LAST_SHOT"] = time.time()
                for GUNPOS in self.guns[ammotype]["POSITION"]:
                    # TODO: MAKE THIS SO IT POINTS AT THE GUNS
                    lefttop = [
                        self.position[0] - (self.sprite_info["DIMENSIONS"][0] * self.sprite_info["PLANE_SCALE"]) / 2,
                        self.position[1] - (self.sprite_info["DIMENSIONS"][1] * self.sprite_info["PLANE_SCALE"]) / 2
                    ]
                    lefttop[0] -= math.cos(self.angle) * (GUNPOS[0] * self.sprite_info["PLANE_SCALE"])
                    lefttop[1] -= math.sin(self.angle) * (GUNPOS[1] * self.sprite_info["PLANE_SCALE"])
                    pygame.draw.circle(screen, (255, 0, 0), lefttop, 4)
                    time.sleep(0.1)

    def load_sprite_info(self, spi):
        if ".json" not in spi:
            spi += ".json"
        with open(DATA_DIR + "\\" + "SpriteInfo" + "\\" + spi) as file:
            info = json.loads(file.read())
        for key in NEEDED_KEYS["KEYS"]:
            if key not in info.keys():
                raise KeyError("Class Player -> Function load_sprite_info ->", spi,
                               "dosent have all needed keys please check data/NeededKeys.json and insure", spi,
                               "has all keys")
        self.sprite_info = info
        self.guns = info["GUNS"]
        self.update_hitboxes()

    def update_hitboxes(self):
        if not self.hitboxes_hp:
            for PART in self.sprite_info["HITBOXES"]:
                self.hitboxes_hp[PART] = {self.sprite_info["HITBOXES"][PART]["HP"]}
        if self.hitbox_circle is None:
            part_bb = self.sprite_info["HITBOXES"][PART]["BOUNDING_BOX"]
            part_bb[0] = self.position[0]
            part_bb[1] = self.position[1]
            self.hitbox_circle = Circle(Vector2(part_bb), 25 * self.sprite_info["PLANE_SCALE"])

    def get_hit(self, PART_NAME, damage):
        self.hitboxes_hp[PART_NAME]["HP"] -= damage
        if self.hitboxes_hp[PART_NAME]["HP"] <= 0:
            print("boom")

    def render(self):
        global ang
        if self.sprite_info["PLANE_TIMER"] + self.sprite_info["PLANE_TIMEOUT"] <= time.time():
            self.sprite_info["PLANE_TIMER"] = time.time()
            self.sprite_info["PLANE_FRAME"] += 1
            if self.sprite_info["PLANE_FRAME"] >= self.sprite_info["FRAMES"]:
                self.sprite_info["PLANE_FRAME"] = 1
        IMG = self.spritesheet.get_image(self.sprite_info["PLANE_FRAME"], self.sprite_info["DIMENSIONS"][0],
                                         self.sprite_info["DIMENSIONS"][1], self.sprite_info["PLANE_SCALE"])
        image_copy = pygame.transform.rotate(IMG, -math.degrees(self.angle + 1.57079633))
        image_copy.set_colorkey(self.sprite_info["PLANE_BACKGROUD"])
        screen.blit(image_copy, (
            self.position[0] - int(image_copy.get_width() / 2), self.position[1] - int(image_copy.get_height() / 2)))

        # for rct in self.hitboxes_rects:
        #   pygame.draw.rect(screen, (0, 0, 255), rct["rect"])
        pygame.draw.line(screen, (0, 0, 255), self.position, (
            self.position[0] + math.cos(self.angle) * 50,
            self.position[1] + math.sin(self.angle) * 50
        ))
        textsurface = myfont.render(f"{self.motor_percentage}", True, (255, 255, 255))
        screen.blit(textsurface, (SCREENW - textsurface.get_size()[0], 0))
        pygame.draw.circle(screen, (0, 0, 255), self.position, 3)

    def motor(self, doru, dt):
        if doru == 1:
            self.motor_percentage += MOTOR_MINUSER * dt
            if self.motor_percentage >= 100:
                self.motor_percentage = 100
        if doru == 0:
            self.motor_percentage -= MOTOR_MINUSER * dt
            if self.motor_percentage <= 60:
                self.motor_percentage = 60

    def move(self, direction: int, dt):
        """
        :param direction: 0 up, 1 left, 2 down, 3 right
        :param dt: deltatime float or int
        :return:
        """
        if direction == 1:
            self.angle -= ANGLE_ADDER * dt
            if self.angle < 0:
                self.angle += 2 * math.pi
            self.deltas[0] = math.cos(self.angle)
            self.deltas[1] = math.sin(self.angle)
        if direction == 3:
            self.angle += ANGLE_ADDER * dt
            if self.angle > 2 * math.pi:
                self.angle -= 2 * math.pi
            self.deltas[0] = math.cos(self.angle)
            self.deltas[1] = math.sin(self.angle)

    def update(self, dt):
        global CAMERA_X, CAMERA_Y
        if FREEZE:
            return
        self.position[0] += self.deltas[0] * (percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
        self.position[1] += self.deltas[1] * (percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
        for ent in entities:
            ent.position[0] -= self.deltas[0] * (
                percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
            ent.position[1] -= self.deltas[1] * (
                percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
        CAMERA_X -= self.deltas[0] * (
            percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
        CAMERA_Y -= self.deltas[1] * (
            percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
        self.update_hitboxes()
        self.render()


p = Player("Spitfire.json")
entities.append(p)


class Ray:
    def __init__(self, base, angle, max_length, angle_offset, target):
        self.origin = base
        self.angle = angle + angle_offset
        self.max_len = max_length

    def check_for_player(self):
        for length in range(0, self.max_len, PLAYERSIZE):
            pygame.draw.circle(screen, (0, 0, 255), (self.origin[0] + ENEMY_SIZE / 2 + (math.cos(self.angle) * length),
                                                     self.origin[1] + ENEMY_SIZE / 2 + (math.sin(self.angle) * length)),
                               3)
            if p.rect.collidepoint(self.origin[0] + ENEMY_SIZE / 2 + (math.cos(self.angle) * length),
                                   self.origin[1] + ENEMY_SIZE / 2 + (math.sin(self.angle) * length)):
                return True
        return False


class Enemy:
    def __init__(self, x, y):
        self.STATE = EnemyState.WONDERING
        self.position = [x, y]
        self.rect = pygame.Rect(self.position[0], self.position[1], ENEMY_SIZE, ENEMY_SIZE)
        self.alive = True
        self.looking = math.radians(random.randint(0, 360))
        self.target = None

    def update(self, dt):
        if FREEZE:
            return
        if self.STATE == EnemyState.WONDERING:
            xcos = math.cos(self.looking) * ENEMY_SPEED * dt
            ysin = math.sin(self.looking) * ENEMY_SPEED * dt
            if self.can_move(self.position[0] + xcos, self.position[1] + ysin):
                self.position[0] += xcos
                self.position[1] += ysin
            else:
                self.looking += math.radians(random.randint(-90, 90))
        if self.STATE == EnemyState.ATTACKING:
            if self.target is not None:
                if distance(self.position[0], p.position[0], self.position[1], p.position[1]) > 250:
                    self.target = None
                    self.STATE = EnemyState.WONDERING
                    self.rect = pygame.Rect(self.position[0], self.position[1], ENEMY_SIZE, ENEMY_SIZE)
                    return
                else:
                    self.looking = calculate_angle(self.position, p.position)
                    self.position[0] += math.cos(self.looking) * ENEMY_SPEED * dt
                    self.position[1] += math.sin(self.looking) * ENEMY_SPEED * dt
        self.rect = pygame.Rect(self.position[0], self.position[1], ENEMY_SIZE, ENEMY_SIZE)
        if distance(self.position[0], p.position[0], self.position[1], p.position[1]) > 250:
            return
        self.look_for_target(ENEMY_DEPTH)

    def can_move(self, newx, newy):
        if newx <= 0:
            return False
        if newy <= 0:
            return False
        if newy >= SCREENH:
            return False
        if newx >= SCREENW:
            return False
        return True

    def look_for_target(self, depth):
        rays: [Ray] = []
        for i in range(-40, 40, depth):
            rays.append(Ray(self.position, self.looking, RAY_LEN, (i / 100), p))
        for ray in rays:
            if ray.check_for_player():
                self.STATE = EnemyState.ATTACKING
                if self.target is None or self.target != p:
                    self.target = p

    def render(self):
        """
        vykreslí postavu a úhel
        :return: None
        """
        pygame.draw.rect(screen, (255, 0, 0), self.rect)
        pygame.draw.line(screen, (0, 0, 255), (self.position[0] + ENEMY_SIZE / 2, self.position[1] + ENEMY_SIZE / 2), (
            self.position[0] + (math.cos(self.looking) * 250),
            self.position[1] + (math.sin(self.looking) * 250)), 2)


def log(LTYPE, message):
    prefix, color = LTYPE[0], LTYPE[1]
    print(colored(color, prefix) + message)


log(LogTypes.INFO, "Player class has been initialized")


# for i in range(1):
#     entities.append(Enemy(SCREENW / 2, (SCREENH / 2)))


def init():
    """
    innits all the important stuff
    :return: None
    """
    x = gb_controls()
    if x == "EX":
        pass
    else:
        log(LogTypes.INFO, "Created controls.json file")
    load_controls()
    log(LogTypes.INFO, "Controls loaded")
    log(LogTypes.SUCCESS, "Initialized all needed function!")
    loop()


def event_listener():
    global running
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


def controls(dt):
    """
    :param dt: float deltatime
    :return: None
    """
    for funcs in controls_js["keyboard"]:
        if pygame.key.get_pressed()[controls_js["keyboard"][funcs]["kc"]] == 1:
            do_controlaction(funcs, 1, dt)
    for funcs in controls_js["mouse"]:
        if pygame.mouse.get_pressed(buttons)[controls_js["mouse"][funcs]["but"] - 1]:
            do_controlaction(funcs, 0, dt)


def do_controlaction(function, device, dt):
    global FREEZE, FREEZE_LC
    """
    :param function: str function name
    :param device: bool, T = Keyboard, F = Mouse
    :param dt: float deltaTime
    :return:
    """
    if function == "freeze":
        if FREEZE_LC + FREEZE_CD < time.time():
            FREEZE = not FREEZE
            FREEZE_LC = time.time()
    if FREEZE:
        return
    if device:
        if function == "motor_up":
            p.motor(1, dt)
        if function == "left":
            p.move(1, dt)
        if function == "motor_down":
            p.motor(0, dt)
        if function == "right":
            p.move(3, dt)
        if function == "fire":
            p.fire()


def is_down(kc):
    """
    return if the key with certain keycode is pressed
    :param kc: int Key code
    :return bool
    """
    return pygame.key.get_pressed()[kc]


def get_function_key(function):
    """
    :param function: str Name of the function
    :return: kc: int Key code
    """
    for perif in controls_js:
        for c_func in controls_js[perif]:
            if c_func == function:
                if perif == "mouse":
                    return controls_js[perif][c_func]["but"]
                if perif == "keyboard":
                    return controls_js[perif][c_func]["kc"]
    return None


def load_controls():
    global controls_js
    with open("controls.json") as file:
        controls_js = json.loads(file.read())
        file.close()


def gb_controls():
    """
    generates base controls.json file that can be edited afterwards
    :return:
    """
    if os.path.exists("controls.json"):
        return "EX"
    with open("controls.json", "w") as file:
        base = {
            "keyboard": {
                "left": {"kc": pygame.K_a},
                "right": {"kc": pygame.K_d},
                "motor_up": {"kc": pygame.K_w},
                "motor_down": {"kc": pygame.K_s},
                "fire": {"kc": pygame.K_e},
                "freeze": {"kc": pygame.K_SPACE}
            },
            "mouse": {
            }

        }
        json.dump(base, file)


def drawfps(fps):
    fpsmeter = myfont.render(f"{int(fps)} FPS", True, (255, 255, 255))
    screen.blit(fpsmeter, (0, 0))


def drawentities(ents):
    ent = myfont.render(f"entities={len(ents) + len(bullets)}", True, (255, 255, 255))
    ent_spaceb = myfont.render(f"b={sys.getsizeof(ents) + sys.getsizeof(bullets)}", True, (255, 255, 255))
    ent_space = myfont.render(f"mb={(sys.getsizeof(ents) + sys.getsizeof(bullets)) / 1024}", True, (255, 255, 255))
    screen.blit(ent_spaceb, (0, 60))
    screen.blit(ent_space, (0, 40))
    screen.blit(ent, (0, 20))


trp = pygame.image.load(DATA_DIR + "\\Maps\\Trip.png").convert()

trp = pygame.transform.scale(trp, (2000 * 4, 2000 * 4))


def update(dt, fps):
    controls(dt)
    event_listener()
    for index, bullet in enumerate(bullets):
        if time.time() - bullet.BORNED >= BULLET_LIFETIME:
            bullets.pop(index)
            continue
        bullet.update(dt)
        bullet.render(screen)

    for pos, i in enumerate(entities):
        i.update(dt)
        i.render()
        if not i.alive:
            entities.pop(pos)
    p.update(dt)
    drawfps(fps)
    drawentities(entities)


def loop():
    global running
    getTicksLastFrame = 0
    while running:
        screen.fill((50, 50, 50))
        screen.blit(trp, (-4000 + CAMERA_X, -4000 + CAMERA_Y))

        t = pygame.time.get_ticks()
        dt = (t - getTicksLastFrame) / 1000.0
        getTicksLastFrame = t

        update(dt, clock.get_fps())
        clock.tick(0)
        pygame.display.update()
    pygame.quit()


init()
