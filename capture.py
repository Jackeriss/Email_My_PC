#coding=utf-8
import vidcap
from PIL import Image
class Device:
    def __init__(self, devnum = 0):
        self.dev = vidcap.new_Dev(devnum, 0)
    def quit(self):
        del self.dev
    def getDisplayName(self):
        return self.dev.getdisplayname()
    def getImage(self):
        buffer, width, height = self.dev.getbuffer()
        if buffer:
            im = Image.fromstring('RGB', (width, height), buffer, 'raw', 'BGR', 0, -1)
            return im
