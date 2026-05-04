import json

from config import Config, DisplayTask, Color, SongTask
from machine import Pin, RTC, ADC
from neopixel import NeoPixel
import network, _thread
from display import display
import ntptime, time
from phew import server, logging
from phew.server import Response
from buzzer_music import music
from thermistor import Thermistor

logging.disable_logging_types(logging.LOG_ALL)

displayQueue = []
songQueue = []
temp = dict()
config = Config()
neobus = NeoPixel(Pin(5), 61, 3, 1)
network.hostname(config.hostname)

displayQueue.append(DisplayTask('loading_start', {}))

_thread.start_new_thread(display, (config, neobus, displayQueue, temp))

if (config.wifiSSID):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(1)
    wlan.connect(config.wifiSSID, config.wifiPassword)
    while not wlan.isconnected():
        pass
    ntptime.settime(2)
else:
    wlan = network.WLAN(network.AP_IF)
    wlan.active(True)
    wlan.config(ssid="EspCLOCK")

displayQueue.append(
    DisplayTask('text', {'text': wlan.ifconfig()[0], 'color': config.color, 'sleepTime': 0.2}))
displayQueue.append(DisplayTask('loading_stop', {}))


def network_thread():
    ntpPassCnt = 0
    while True:
        ntpPassCnt += 1
        if not wlan.isconnected():
            wlan.active(False)
            time.sleep(1)
            wlan.active(True)
            time.sleep(1)
            wlan.connect(config.wifiSSID, config.wifiPassword)
            while not wlan.isconnected():
                pass
            displayQueue.append(
                DisplayTask('text', {'text': wlan.ifconfig()[0], 'color': config.color, 'sleepTime': 0.2}))
            pass

        if ntpPassCnt > 60:
            ntpPassCnt = 0
            ntptime.settime(2)

        time.sleep(60)


with open("html/index.html.gz", "rb") as f:
    _html_gz = f.read()

@server.route("/", methods=["GET"])
def index(request):
    return Response(_html_gz, status=200, headers={"Content-Type": "text/html", "Content-Encoding": "gzip"})


@server.route("/api/status", methods=["GET"])
def status(request):
    return json.dumps(dict(
        status=True,
        data=dict(
            time=RTC().datetime(),
            host=config.hostname,
            wifi_ssid=config.wifiSSID,
            color=config.color,
            temp=temp.get("current", 0)
        ),
        error=dict()
    )), 200, "application/json"


@server.route("/api/notification", methods=["POST"])
def notification(request):
    displayQueue.append(DisplayTask('text', payload=request.data))
    return (json.dumps(dict(
        status=True,
        data=dict(),
        error=dict()
    )), 200, "application/json"

            @ server.route("/api/song", methods=["POST"]))


@server.route("/api/song", methods=["POST"])
def song(request):
    songQueue.append(SongTask(song=request.data.get("song", "")))
    return json.dumps(dict(
        status=True,
        data=dict(),
        error=dict()
    )), 200, "application/json"


@server.route("/api/config", methods=["POST"])
def update_config(request):
    displayQueue.append(DisplayTask('text', payload=request.data))
    for key, value in request.data.items():
        setattr(config, key, value)
    config.saveConfig()
    return json.dumps(dict(
        status=True,
        data=dict(),
        error=dict()
    )), 200, "application/json"


@server.catchall()
def catchall(request):
    return json.dumps(dict(
        status=False,
        data=dict(),
        error="Not found"
    )), 404, "application/json"


def song_thread(songQueue: list[SongTask]):
    buzzer_pin = Pin(4)

    while True:
        if len(songQueue):
            song = songQueue.pop(0)
            try:
                mySong = music(song.song, pins=[buzzer_pin], looping=False)
                while mySong.tick():
                    time.sleep(0.04)
            except Exception as e:
                print(e)
                pass
        time.sleep(1)


class ExponentialMovingAverage:
    def __init__(self, alpha: float):
        self.alpha = alpha  # 0 < alpha <= 1
        self.value = None

    def add(self, new_value: float) -> float:
        if self.value is None:
            self.value = new_value
        else:
            self.value = (
                    self.alpha * new_value
                    + (1 - self.alpha) * self.value
            )
        return self.value


def ntc_reader(temp: dict):
    therm = Thermistor(ADC(34, atten=ADC.ATTN_11DB), beta=3435, therm_ohm=50_000, divider_ohm=100_000)
    ema = ExponentialMovingAverage(alpha=0.1)
    while True:
        temp.__setitem__("current", ema.add(therm.read_temperature_celsius()))
        time.sleep(1)
    pass


_thread.start_new_thread(server.run, ())
_thread.start_new_thread(network_thread, ())
_thread.start_new_thread(song_thread, (songQueue,))
_thread.start_new_thread(ntc_reader, (temp,))
