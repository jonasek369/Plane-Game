#
# !!!!! WARNING DO NOT CHANGE ANYTHING IN THIS FILE IT CAN BREAK THE GAME !!!!
#
import math
import os
import random
from dataclasses import dataclass

from colorama import Fore, Style

UUID_LENGHT = 16
UUID_LIST = list("qwertzuiopasdfghjklyxcvbnnmQWERTZUIOPASDFGHJKLYXCVBNM0123456789")

MAP_SIZE = (8000, 8000)

os.system("cls")


# +------------------------------------------------------------+
# |                Made by Jonáš Erlebach                      |
# |  Thanks to third party libraries from https://pypi.org/    |
# +------------------------------------------------------------+


# HELPER FUNCTIONS

def make_uuid():
    return "".join(random.choices(UUID_LIST, k=UUID_LENGHT))


def random_color():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def distance(x1, x2, y1, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def distance_vec(fpos, spos):
    return math.sqrt((spos[0] - fpos[0]) ** 2 + (spos[1] - fpos[1]) ** 2)


def colored(rgb, text):
    return Fore.WHITE + "\033[38;2;{};{};{}m{} \033[38;2;255;255;255m".format(rgb[0], rgb[1], rgb[2],
                                                                              text) + Style.RESET_ALL


def averageout_array(array):
    arlen = len(array)
    if arlen == 0:
        return None
    return sum(array) / len(array)


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


def circles_collide(circle1, circle2):
    return circle1.pos.distance_to(circle2.pos) <= circle1.radius + circle2.radius


def log(LTYPE, message):
    prefix, color = LTYPE[0], LTYPE[1]
    print(colored(color, prefix) + message)


def cons(_min, val, _max):
    if val < _min:
        return _min
    if val > _max:
        return _max
    return val


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
