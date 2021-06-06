import pygame
import numpy as np
from queue import Queue
from threading import Thread

from leap import Sensor, calibrate, data_puller

black = (0, 0, 0)
red = (255, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)
blue = (0, 0, 255)

width, height = 900, 700
background = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
pygame.init()

sensor = Sensor()
baseline_ins, baseline_exp = calibrate(sensor)

data_q = Queue()
msg_q = Queue()

t = Thread(target=data_puller, args=(data_q, msg_q))
t.daemon = True
t.start()

period = 8  # secs
dt = 1 / 60
freq = 1 / period
timepoints = np.linspace(0, period, int(period / dt))
changes = (height // 2) * np.sin(2 * np.pi * freq * timepoints)

stop = False
i = 0
alpha = 0.75
interp = (height // 2) / (baseline_ins - baseline_exp)
old_v = 0
new_v = 0
while not stop:
    clock.tick(60)
    v = data_q.get()
    new_v = ((v - baseline_exp) * interp * alpha) + old_v * (1 - alpha)
    old_v = new_v
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            msg_q.put("STOP")
            stop = True
    top = height // 2 + changes[i]
    background.fill(black)
    pygame.draw.rect(
        background,
        blue,
        pygame.Rect(0, top, width, height),
    )

    pygame.draw.circle(background, red, (width // 2, height // 2 + new_v), 20)
    pygame.display.update()
    if i == len(changes) - 1:
        i = 0
    else:
        i += 1

t.join()
pygame.quit()
quit()