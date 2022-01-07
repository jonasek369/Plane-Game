import json
import os
import sys
import time
from dataclasses import dataclass
from enum import Enum, auto

import pygame
from win32api import GetSystemMetrics

from data.Scripts.Utils import *

pygame.init()
pygame.font.init()
myfont = pygame.font.SysFont('Arial', 24)
SCREENW, SCREENH = 1920, 1080

WORKING_DIR = os.getcwd()
assert os.path.exists(
    WORKING_DIR + "\\" + "data"), "Could not file data folder please open exe file in same folder as where is located data folder"
DATA_DIR = WORKING_DIR + "\\" + "data"

controls_js = None
running = True
screen = pygame.display.set_mode([SCREENW, SCREENH])
clock = pygame.time.Clock()

Vector2 = pygame.math.Vector2
Vector3 = pygame.math.Vector3

"""
uch_ prefix means that variable is changeable only by user: user changeable
"""

uch_DEBUGGING = False

FPS = 240

BULLET_LIFETIME = 5
BULLET_RADIUS = 2

entities = []
bullets = []
sprite_list = []

C_X = 0
C_Y = 0

PLAYERSIZE = 25

"""
Prefix E = Enemy
"""

E_DEFAULT_PLANE = "Bf109E-3.json"

"""
Prefix R = Ray
"""
R_LEN = 1000
R_RANGE = Vector2(-40, 40)
R_HITBOX_SIZE = 5
R_DEPTH = 1

FREEZE = False
FREEZE_CD = 0.3
FREEZE_LC = 0

ANGLE_ADDER = 1.75
MOTOR_MINUSER = 50

NEEDED_KEYS = {}
AMMO_INFO = {}
GAME_SETTINGS = {}

IMPLEMENTED_AMMOTYPES = ["20", "303"]

USER_UUID = make_uuid()

try:
    with open(WORKING_DIR + "\\" + "data" + "\\" + "NeededKeys.json", "r") as file:
        NEEDED_KEYS = json.loads(file.read())
except Exception as e:
    raise Exception("??: Unknown Exception: ", e)

assert "KEYS" in NEEDED_KEYS.keys(), "LINE: ~58~ -> Could not load file needed keys from data folder make sure you openening exe in same folder as where is data folder "

with open(DATA_DIR + "\\Settings\\AmmoTypes.json", "r") as file:
    AMMO_INFO = json.loads(file.read())

with open(DATA_DIR + "\\Settings\\Game.json", "r") as file:
    GAME_SETTINGS = json.loads(file.read())

for ammotype in IMPLEMENTED_AMMOTYPES:
    assert ammotype in AMMO_INFO, "AmmoTypes.json is not new enough"

if GetSystemMetrics(43) > 3:
    buttons = 5
else:
    buttons = 3


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
    PERSUING = auto()


class Circle:
    def __init__(self, pos, radius):
        self.pos = Vector2(pos)
        self.radius = radius

    def draw(self):
        pygame.draw.circle(screen, (255, 255, 0), self.pos, self.radius)


class Bullet:
    def __init__(self, angle, startx, starty, _type, owner):
        self.info = AMMO_INFO[_type]
        self.BORNED = time.time()
        self.angle = angle
        self.alive = True
        self.position = [startx, starty]
        self.hitbox = Circle([startx, starty], 1)
        self.owner = owner

    def update(self, dt):
        if FREEZE:
            return
        self.hitbox = Circle(self.position, BULLET_RADIUS)
        self.hitbox.radius = self.info["SIZE"]
        for i in entities:
            if circles_collide(i.hitbox, self.hitbox):
                if self.owner == i.uuid:
                    continue
                i.get_hit(self.info["DAMAGE"])
                self.alive = False
        self.position[0] += math.cos(self.angle) * self.info["SPEED"] * dt
        self.position[1] += math.sin(self.angle) * self.info["SPEED"] * dt

    def render(self):
        global drawing
        self.hitbox.draw()


class SpriteSheet:
    """
    from:
    https://github.com/russs123/pygame_tutorials
    """

    def __init__(self, image):
        self.sheet = image

    def get_image(self, frame, width, height, scale):
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), ((frame * width), 0, width, height))
        image = pygame.transform.scale(image, (width * scale, height * scale))
        return image


class Player:
    def __init__(self, sprite_info):
        self.position = [SCREENW // 2, SCREENH // 2]
        self.angle = math.pi * 1.5
        self.deltas = [math.cos(self.angle), math.sin(self.angle)]
        self.motor_percentage = 70
        self.guns = {}
        self.hitbox = None

        self.uuid = USER_UUID

        self.constants = {

        }

        self.alive = True
        assert sprite_info is not None, "Class Player -> param: spritename -> Error: This parameter cant be None"
        self.sprite_info = {"PLANE_TIMER": time.time()}
        self.load_sprite_info(sprite_info)
        self.sprite = pygame.image.load(DATA_DIR + self.sprite_info["SPRITE_LOCATION"]).convert()
        self.spritesheet = SpriteSheet(self.sprite)

    def fire(self) -> None:
        topleft = [
            self.position[0] + math.cos(self.angle - 0.78) * (
                    (self.sprite_info["DIMENSIONS"][0] * self.sprite_info["PLANE_SCALE"]) / 1.41),
            self.position[1] + math.sin(self.angle - 0.78) * (
                    (self.sprite_info["DIMENSIONS"][1] * self.sprite_info["PLANE_SCALE"]) / 1.41)
        ]
        for ammotype in self.guns:
            if self.guns[ammotype]["LAST_SHOT"] + self.guns[ammotype]["TIMEOUT"] <= time.time():
                if self.guns[ammotype]["RESERVE"] <= 0:
                    continue
                self.guns[ammotype]["LAST_SHOT"] = time.time()
                for GUNPOS in self.guns[ammotype]["POSITION"]:
                    righty = [
                        topleft[0] + math.cos(self.angle - math.pi) * (GUNPOS[1] * self.sprite_info["PLANE_SCALE"]),
                        topleft[1] + math.sin(self.angle - math.pi) * (GUNPOS[1] * self.sprite_info["PLANE_SCALE"])]
                    backer = [
                        topleft[0] + math.cos(self.angle - math.pi) * (
                                (GUNPOS[1] - 1) * self.sprite_info["PLANE_SCALE"]),
                        topleft[1] + math.sin(self.angle - math.pi) * (
                                (GUNPOS[1] - 1) * self.sprite_info["PLANE_SCALE"])]
                    from_ = [
                        backer[0] + math.cos(self.angle + (math.pi / 2)) * (
                                (GUNPOS[0]) * self.sprite_info["PLANE_SCALE"]),
                        backer[1] + math.sin(self.angle + (math.pi / 2)) * (GUNPOS[0] * self.sprite_info["PLANE_SCALE"])
                    ]
                    to_ = [
                        righty[0] + math.cos(self.angle + (math.pi / 2)) * (
                                GUNPOS[0] * self.sprite_info["PLANE_SCALE"]),
                        righty[1] + math.sin(self.angle + (math.pi / 2)) * (GUNPOS[0] * self.sprite_info["PLANE_SCALE"])
                    ]
                    self.guns[ammotype]["RESERVE"] -= 1
                    bullets.append(Bullet(calculate_angle(to_, from_), to_[0], to_[1], ammotype, self.uuid))

    def load_sprite_info(self, spi) -> None:
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

    def update_hitboxes(self) -> None:
        if self.hitbox is None:
            for PART in self.sprite_info["HITBOXES"]:
                part_bb = self.sprite_info["HITBOXES"][PART]["BOUNDING_BOX"]
                part_bb[0] = self.position[0]
                part_bb[1] = self.position[1]
                self.hitbox = Circle(Vector2(part_bb), 25 * self.sprite_info["PLANE_SCALE"])

    def get_hit(self, damage) -> None:
        self.sprite_info["HP"] -= damage
        if self.sprite_info["HP"] <= 0:
            self.alive = False

    def render(self) -> None:
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
        if uch_DEBUGGING:
            pygame.draw.line(screen, (0, 0, 255), self.position, (
                self.position[0] + math.cos(self.angle) * 50,
                self.position[1] + math.sin(self.angle) * 50
            ))
        done = [20, 0]
        for GUN in self.guns:
            textsurface = myfont.render(f"{GUN}: {self.guns[GUN]['RESERVE']}", True, (255, 255, 255))
            screen.blit(textsurface, (SCREENW - textsurface.get_size()[0], done[1]))
            done[0] += textsurface.get_size()[0]
            done[1] += textsurface.get_size()[1]
        pygame.draw.circle(screen, (0, 0, 255), self.position, 3)

    def motor(self, doru, dt) -> None:
        if doru == 1:
            self.motor_percentage += MOTOR_MINUSER * dt
            if self.motor_percentage >= 100:
                self.motor_percentage = 100
        if doru == 0:
            self.motor_percentage -= MOTOR_MINUSER * dt
            if self.motor_percentage <= 60:
                self.motor_percentage = 60

    def move(self, direction: int, dt) -> None:
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

    def update(self, dt) -> None:
        global C_X, C_Y
        if FREEZE:
            return
        self.position[0] += self.deltas[0] * (percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
        self.position[1] += self.deltas[1] * (percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
        for ent in entities:
            ent.position[0] -= self.deltas[0] * (
                percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
            ent.position[1] -= self.deltas[1] * (
                percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
        for bullet in bullets:
            bullet.position[0] -= self.deltas[0] * (
                percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
            bullet.position[1] -= self.deltas[1] * (
                percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
        C_X -= self.deltas[0] * (
            percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt
        C_Y -= self.deltas[1] * (
            percentage(self.sprite_info["PLANE_SPEED"], self.motor_percentage)) * dt

        self.update_hitboxes()
        self.render()


p = Player("Spitfire.json")
entities.append(p)


class Ray:
    def __init__(self, origin: Vector2, angle: float, plr: Player):
        self.origin = origin
        self.angle = angle
        self.plr = plr

    def search_for_player(self):
        for length in range(0, R_LEN, (self.plr.sprite_info["PLANE_SCALE"] * 25)):
            pos = (
                self.origin[0] + (math.cos(self.angle) * length),
                self.origin[1] + (math.sin(self.angle) * length)
            )
            pygame.draw.circle(screen, (0, 0, 255), pos, 3)
            if circles_collide(Circle(pos, R_HITBOX_SIZE), p.hitbox):
                return True
        return False


class Enemy:
    def __init__(self, pos, sprite_info):
        self.position = Vector2(pos)
        self.alive = True
        self.target = None
        self.uuid = make_uuid()

        self.angle = math.pi * 1.5
        self.guns = {}
        self.hitbox = Circle(self.position, 0)
        self.sprite_info = {"PLANE_TIMER": time.time()}
        self.load_sprite_info(sprite_info)
        self.sprite = pygame.image.load(DATA_DIR + self.sprite_info["SPRITE_LOCATION"]).convert()
        self.spritesheet = SpriteSheet(self.sprite)

    def get_hit(self, damage) -> None:
        self.sprite_info["HP"] -= damage
        if self.sprite_info["HP"] <= 0:
            print("enemy dead")
            self.alive = False

    def update_hitboxes(self) -> None:
        self.hitbox = Circle(Vector2(self.position), 25 * self.sprite_info["PLANE_SCALE"])

    def load_sprite_info(self, spi) -> None:
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

    def update(self, dt):
        self.update_hitboxes()
        player = None
        for entity in entities:
            if entity.uuid != USER_UUID:
                continue
            else:
                player = entity
        if player is None or not player.alive:
            return

        rays: [Ray] = []
        for i in range(-40, 40, R_DEPTH):
            rays.append(Ray(self.position, self.angle + (i / 100), player))
        for ray in rays:
            if ray.search_for_player():
                print("Found Player")

        #raise NotImplementedError("Enemy Function not implemeted")

    def render(self):
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
        ent = myfont.render(f"HP: {self.sprite_info['HP']}", True, (255, 255, 255))
        screen.blit(ent, (self.position.x, self.position.y - 20))
        # self.hitbox.draw()


def log(LTYPE, message):
    prefix, color = LTYPE[0], LTYPE[1]
    print(colored(color, prefix) + message)


log(LogTypes.INFO, "Player class has been initialized")

uch_DEBUGGING = GAME_SETTINGS["DEBUGGING"]

for i in range(5):
    entities.append(Enemy(Vector2(639 + i*128, -466), E_DEFAULT_PLANE))


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


def is_down(kc) -> bool:
    """
    return if the key with certain keycode is pressed
    :param kc: int Key code
    :return bool
    """
    return pygame.key.get_pressed()[kc]


def get_function_key(function) -> None or int:
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


def gb_controls() -> None or str:
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
        bullet.render()

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
        screen.blit(trp, (-4000 + C_X, -4000 + C_Y))

        t = pygame.time.get_ticks()
        dt = (t - getTicksLastFrame) / 1000.0
        getTicksLastFrame = t

        update(dt, clock.get_fps())
        clock.tick(0)
        pygame.display.update()
        # print((p.position[0] - C_X, p.position[1] - C_Y))
    pygame.quit()


init()
