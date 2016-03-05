#coding = utf-8
from win32event import CreateMutex
from win32api import CloseHandle, GetLastError
from winerror import ERROR_ALREADY_EXISTS

#限制只能同时运行一个Email My PC程序
class singleinstance:

    def __init__(self):
        self.mutexname = "testmutex_{D0E858DF-985E-4907-B7FB-8D732C3FC3B9}"
        self.mutex = CreateMutex(None, False, self.mutexname)
        self.lasterror = GetLastError()
    
    def aleradyrunning(self):
        return (self.lasterror == ERROR_ALREADY_EXISTS)
        
    def __del__(self):
        if self.mutex:
            CloseHandle(self.mutex)
