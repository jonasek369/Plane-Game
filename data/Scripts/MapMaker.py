import os
import random

import numpy as np
import vec_noise
from PIL import Image
from tqdm import tqdm


WORLD_SIZE = [2000, 2000, 3]

WORKING_DIR = os.getcwd()
DATA_DIR = WORKING_DIR[:-8]

os.system("cls")


# +------------------------------------------------------------+
# |                Made by Jonáš Erlebach                      |
# |  Thanks to third party libraries from https://pypi.org/    |
# +------------------------------------------------------------+

class WorldGeneration:
    def __init__(self, DATA_DIR):
        self.DATA_DIR = DATA_DIR
        self.NOISE_SCALE = 0.002  # def 0.002
        self.octaves_devider = 1

    def CreateImage(self):
        x = [[[0, 0, 0] for x in range(WORLD_SIZE[0])] for _y in range(WORLD_SIZE[1])]
        startx, starty = random.randint(0, 50000), random.randint(0, 50000)
        for x_ in tqdm(range(WORLD_SIZE[0])):
            for y in range(WORLD_SIZE[1]):
                value = vec_noise.snoise2(startx + x_ * self.NOISE_SCALE, starty + y * self.NOISE_SCALE,
                                          12 // self.octaves_devider)
                if value < -0.45:
                    x[x_][y][0] = 128
                    x[x_][y][1] = 197
                    x[x_][y][2] = 222
                    continue
                if value < -0.35:
                    x[x_][y][0] = 248
                    x[x_][y][1] = 240
                    x[x_][y][2] = 164
                    continue
                if value < 0.35:
                    x[x_][y][0] = 126
                    x[x_][y][1] = 200
                    x[x_][y][2] = 80
                    continue
                if value < 0.53:
                    x[x_][y][0] = 200
                    x[x_][y][1] = 200
                    x[x_][y][2] = 200
                    continue
                else:
                    x[x_][y][0] = 255
                    x[x_][y][1] = 255
                    x[x_][y][2] = 255
                    continue

        self.to_image(x)

    def to_image(self, array):
        print("Creating Image")
        array = np.array(array).astype(np.uint8)
        img = Image.fromarray(array)
        img.save(self.DATA_DIR + "\\Maps\\BG.png")
        print("Image Created")


if __name__ == '__main__':
    WorldGeneration(DATA_DIR).CreateImage()
