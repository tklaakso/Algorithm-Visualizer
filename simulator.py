from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import imp
import sys
import time
from threading import Thread

class RealTimeSimulator(QtCore.QObject):
    update = QtCore.pyqtSignal()
    
    def __init__(self, code, fname, args, arrayName, variables, update, playbackSpeed):
        super(QtCore.QObject, self).__init__()
        self.module = imp.new_module('code')
        exec(code, self.module.__dict__)
        self.func = getattr(self.module, fname)
        self.args = args
        self.arrayName = arrayName
        self.variables = variables
        self.update.connect(update)
        self.playbackSpeed = playbackSpeed
    
    def start(self):
        self.running = True
        thread = Thread(target = self.run)
        thread.start()
    
    def stop(self):
        self.running = False
    
    def reset(self):
        self.running = False
    
    def run(self):
        sys.settrace(self.trace)
        self.func(*(self.args))
        sys.settrace(None)
        self.lines = []
        self.update.emit()
    
    def trace(self, frame, event, arg):
        if not self.running:
            return
        if event == 'line' and self.arrayName in frame.f_locals:
            self.lines = [frame.f_lineno]
            self.arr = frame.f_locals[self.arrayName]
            self.var = set()
            for v in self.variables:
                if type(v) == tuple:
                    x, y = v
                    if type(x) == int or (x in frame.f_locals and type(frame.f_locals[x]) == int and 0 <= frame.f_locals[x] <= len(self.arr) - 1):
                        if type(y) == int or (y in frame.f_locals and type(frame.f_locals[y]) == int and 0 <= frame.f_locals[y] <= len(self.arr[frame.f_locals[x]]) - 1):
                            self.var.add((x if type(x) == int else frame.f_locals[x], y if type(y) == int else frame.f_locals[y]))
                elif v in frame.f_locals and type(frame.f_locals[v]) == int and 0 <= frame.f_locals[v] <= len(self.arr) - 1:
                    self.var.add((frame.f_locals[v], 0))
            self.update.emit()
            time.sleep(self.playbackSpeed)
        return self.trace

class PlaybackSimulator(QtCore.QObject):
    update = QtCore.pyqtSignal()
    
    def __init__(self, code, fname, args, arrayName, variables, update, playbackSpeed):
        super(QtCore.QObject, self).__init__()
        self.module = imp.new_module('code')
        exec(code, self.module.__dict__)
        self.func = getattr(self.module, fname)
        self.args = args
        self.arrayName = arrayName
        self.variables = variables
        self.update.connect(update)
        self.playbackSpeed = playbackSpeed
        self.playbackPosition = 0
        self.frames = []
        self.generate()
    
    def start(self):
        self.running = True
        thread = Thread(target = self.run)
        thread.start()
    
    def stop(self):
        self.running = False
    
    def localUpdate(self):
        self.lines, self.arr, self.var = self.frames[self.playbackPosition]
        self.update.emit()
    
    def reset(self):
        self.running = False
        self.playbackPosition = 0
        self.localUpdate()
    
    def stepForward(self):
        self.playbackPosition = (self.playbackPosition + 1) % len(self.frames)
        self.localUpdate()
    
    def stepBack(self):
        self.playbackPosition = (self.playbackPosition - 1) % len(self.frames)
        self.localUpdate()
    
    def run(self):
        while self.playbackPosition < len(self.frames) - 1 and self.running:
            self.stepForward()
            time.sleep(self.playbackSpeed)
    
    def generate(self):
        self.frames = []
        sys.settrace(self.trace)
        self.func(*(self.args))
        sys.settrace(None)
    
    def trace(self, frame, event, arg):
        if event == 'line' and self.arrayName in frame.f_locals:
            lines = [frame.f_lineno]
            arr = [x if type(x) != list else [y for y in x] for x in frame.f_locals[self.arrayName]]
            var = set()
            for v in self.variables:
                if type(v) == tuple:
                    x, y = v
                    if type(x) == int or (x in frame.f_locals and type(frame.f_locals[x]) == int and 0 <= frame.f_locals[x] <= len(arr) - 1):
                        if type(y) == int or (y in frame.f_locals and type(frame.f_locals[y]) == int and 0 <= frame.f_locals[y] <= len(arr[frame.f_locals[x]]) - 1):
                            var.add((x if type(x) == int else frame.f_locals[x], y if type(y) == int else frame.f_locals[y]))
                elif v in frame.f_locals and type(frame.f_locals[v]) == int and 0 <= frame.f_locals[v] <= len(arr) - 1:
                    var.add((frame.f_locals[v], 0))
            self.frames.append((lines, arr, var))
        return self.trace