import pygame
import numpy as np
from queue import Queue
from threading import Thread

from leap import Sensor, calibrate, data_puller

# Colors
black = (0, 0, 0)
red = (255, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)
blue = (0, 0, 255)

# Pygame Variables
theta = 0
v = 0
vel = 0
acc = 0
gravity = 9.86

# Start Pygame
width, height = 900, 700
pygame.init()
background = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()

rootx = width // 2
rooty = 50


# Tarzan
class Pendulum(object):
    def __init__(self, XY):
        self.x = XY[0] - rootx  # includes width//2
        self.y = XY[1] - rooty
        self.length = np.sqrt(self.x**2 + self.y**2)
        print("LENGTH: ", self.length)
        self.radius = 15
        self.theta = np.asin(self.x / self.length)
        self.dt = 0.01
        self.friction = .9
        self.ang_vel = 0
        self.mass = 100

    def draw(self, bg):
        self.advance()
        pygame.draw.line(bg, white, (rootx, rooty), (self.x, self.y), 4)
        pygame.draw.circle(bg, red, (self.x, self.y), self.radius)
        pygame.draw.circle(bg, green, (20, height - 20),
                           np.abs(self.ang_vel) * 50)

    def advance(self):
        # basic integration
        # theta = theta + dt*theta_dot
        # theta_dot = theta_dot + dt*(mg/l sin(theta))
        # x is simply a trig function of theta and l
        self.ang_vel = self.friction * self.ang_vel - self.dt * (
            (self.mass * gravity / self.length) * np.sin(self.theta))
        self.theta += self.dt * self.ang_vel
        self.x = rootx + self.length * np.sin(self.theta)
        self.y = rooty + self.length * np.cos(self.theta)


def add_force(p):
    x, y = pygame.mouse.get_pos()
    print(x)
    if x < width // 2:
        p.ang_vel -= 0.1
    else:
        p.ang_vel += 0.1


def add_stretch_force(p, v):
    p.ang_vel += 5e-5 * v


def print_dynamics(p):
    print(p.x, p.y, p.theta, p.ang_vel)


def redraw():
    background.fill(black)
    pendulum.draw(background)
    pygame.draw.circle(background, blue, (width - 20, height - 20), v * 1e-4)
    pygame.display.update()


# sensor calibration #
pendulum = Pendulum((rootx, height - 100))
sensor = Sensor()
baseline = calibrate(sensor)
print("BASELINE: ", baseline)

data_q = Queue()
msg_q = Queue()

# pull data, subtract baseline, apply filter
alpha = 0.75
t = Thread(target=data_puller, args=(data_q, msg_q, baseline, alpha))
t.daemon = True
t.start()

stop = False
while not stop:
    clock.tick(60)
    while not data_q.empty():
        v = data_q.get()
        # print(v)
    add_stretch_force(pendulum, v)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            msg_q.put("STOP")
            stop = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            add_force(pendulum)
            print("mouse down")

    redraw()
    # print_dynamics(pendulum)
t.join()
pygame.quit()
quit()
