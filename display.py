import time
import math
from config import *
from neopixel import NeoPixel
from machine import RTC
from consts import *


def scrollText(neobus: NeoPixel, text: str, color: Color, sleepTime=1):
    displayText = "    " + text.lower() + "    "

    neobus[dots[0]] = Color(0, 0, 0)
    neobus[dots[1]] = Color(0, 0, 0)

    for i in range(0, len(displayText) - 3):
        displayNumber(neobus, 0, displayText[i], color)
        displayNumber(neobus, 1, displayText[i + 1], color)
        displayNumber(neobus, 2, displayText[i + 2], color)
        displayNumber(neobus, 3, displayText[i + 3], color)
        neobus.write()
        time.sleep(sleepTime)


def displayNumber(neobus: NeoPixel, index, char, color: Color):
    for j in range(0, 7):
        if (CHARS[char][j] == 1):
            neobus[segments[index][j][0]] = color
            neobus[segments[index][j][1]] = color
        else:
            neobus[segments[index][j][0]] = Color(0, 0, 0)
            neobus[segments[index][j][1]] = Color(0, 0, 0)


def displayClock(neobus: NeoPixel, config: Config, pulse_phase: float):
    t = RTC().datetime()
    hour = "{:2}".format(t[4])
    min = "{:02d}".format(t[5])
    displayNumber(neobus, 0, hour[0], config.color)
    displayNumber(neobus, 1, hour[1], config.color)
    displayNumber(neobus, 2, min[0], config.color)
    displayNumber(neobus, 3, min[1], config.color)

    brightness = (math.sin(pulse_phase) + 1) / 2
    dots_color = Color(
        int(config.color[0] * brightness),
        int(config.color[1] * brightness),
        int(config.color[2] * brightness)
    )
    neobus[dots[0]] = dots_color
    neobus[dots[1]] = dots_color

    neobus.write()


def displayTemp(config, neobus, celsius: float):
    t = "{:4.1f}".format(celsius)
    displayNumber(neobus, 0, t[0], config.color)
    displayNumber(neobus, 1, t[1], config.color)
    displayNumber(neobus, 2, t[3], config.color)
    displayNumber(neobus, 3, ' ', config.color)
    neobus[dots[0]] = Color(0, 0, 0)
    neobus[dots[1]] = config.color
    neobus.write()


def display(config: Config, neobus: NeoPixel, queue: list[DisplayTask], temp: dict):
    pulse_phase = 0.0
    loading = {'enabled': False, 'cnt': 0}
    while True:
        if (len(queue) > 0):
            task = queue.pop(0)
            {
                'text': (
                    lambda: scrollText(neobus,
                                       task.payload.get('text', ''),
                                       task.payload.get('color', Color(1, 0, 0)),
                                       task.payload.get('sleepTime', 1),
                                       )),
                'loading_start': lambda: loading.__setitem__('enabled', True),
                'loading_stop': lambda: loading.__setitem__('enabled', False),
                'temperature': lambda: displayTemp(config, neobus, temp.get('current', 0)) or time.sleep(
                    task.payload.get('sleepTime', 3))
            }[task.type]()

        if (loading['enabled']):
            s = loadingAnim[loading['cnt'] % len(loadingAnim)]
            loading['cnt'] += 1
            neobus[dots[0]] = Color(0, 0, 0)
            neobus[dots[1]] = Color(0, 0, 0)
            displayNumber(neobus, 0, ' ', config.color)
            displayNumber(neobus, 1, ' ', config.color)
            displayNumber(neobus, 2, ' ', config.color)
            displayNumber(neobus, 3, ' ', config.color)
            displayNumber(neobus, s[0], s[1], config.color)
            neobus.write()
            time.sleep(0.1)
        else:
            displayClock(neobus, config, pulse_phase)
            pulse_phase += 0.15
            if pulse_phase > 2 * math.pi:
                pulse_phase = 0.0
            time.sleep(0.05)
