import random
import math
from colorama import Fore, Style

UUID_LENGHT = 16
UUID_LIST = list("qwertzuiopasdfghjklyxcvbnnmQWERTZUIOPASDFGHJKLYXCVBNM0123456789")
TOLERANCE = 20

def make_uuid():
    return "".join(random.choices(UUID_LIST, k=UUID_LENGHT))


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

def circles_collide(circle1, circle2):
    return circle1.pos.distance_to(circle2.pos) <= circle1.radius + circle2.radius

