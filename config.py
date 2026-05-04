import json


class Config:

    def __init__(self):
        f = open('config.json')
        config = json.loads(f.read())
        self.wifiSSID = config.get("wifiSSID", '')
        self.wifiPassword = config.get("wifiPassword", '')
        self.color = Color(*config.get("color", [1, 0, 0]))
        self.hostname = config.get("hostname", '')
        f.close()

    def saveConfig(self):
        f = open('config.json', "w")
        f.write(json.dumps(self.__dict__))
        f.close()


class Color(tuple):
    def __new__(self, r, g, b):
        if (((r < 0) or (r > 255)) or ((g < 0) or (g > 255)) or ((b < 0) or (b > 255))):
            raise ValueError("Invalid Color value, it must be between 0 and 255")
        return (r, g, b)


class DisplayTask:
    def __init__(self, type, payload):
        self.type = type
        self.payload = payload
        pass


class SongTask:
    def __init__(self, song: str):
        self.song = song
        pass
