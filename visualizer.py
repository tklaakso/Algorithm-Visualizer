from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.style import Style
import ast
import json
from simulator import RealTimeSimulator, PlaybackSimulator

class Application:
    def textChanged(self):
        text = self.ui.textEdit.toPlainText()
        highlight_color = 'FFAAAA'
        formatting_info = '<style>' + HtmlFormatter(style = 'colorful').get_style_defs('.highlight') + '.highlight .hll { background-color: #' + highlight_color + ' }</style>'
        formatted = highlight(text, get_lexer_by_name('python', stripnl = False, ensurenl = False), HtmlFormatter(hl_lines = self.linesToHighlight)).replace('\n', '<br/>')
        cursor = self.ui.textEdit.textCursor()
        pos = cursor.position()
        self.ui.textEdit.blockSignals(True)
        self.ui.textEdit.setHtml(formatting_info + formatted)
        self.ui.textEdit.blockSignals(False)
        cursor.setPosition(pos)
        self.ui.textEdit.setTextCursor(cursor)
        self.realTime = False
    
    def getPlaybackSpeed(self):
        return 0.5 - self.ui.playbackSpeed.value() / 1000
    
    def speedChanged(self):
        if self.sim != None:
            self.sim.playbackSpeed = self.getPlaybackSpeed()
    
    def update(self):
        self.linesToHighlight = self.sim.lines
        self.textChanged()
        self.draw()
            
    
    def saveToFile(self, fileName):
        info = {'arguments': self.ui.arguments.text(),
                'variables': self.ui.variables.text(),
                'functionName': self.ui.functionName.text(),
                'arrayName': self.ui.arrayName.text(),
                'speed': self.ui.playbackSpeed.value(),
                'code': self.ui.textEdit.toPlainText()
                }
        with open(fileName, 'w') as file:
            json.dump(info, file)
    
    def close(self):
        self.ui.arguments.setText('')
        self.ui.variables.setText('')
        self.ui.functionName.setText('')
        self.ui.arrayName.setText('')
        self.ui.playbackSpeed.setValue(0)
        self.ui.textEdit.setPlainText('')
        self.savePath = None
    
    def save(self):
        if self.savePath == None:
            self.save_as()
        else:
            self.saveToFile(self.savePath)
    
    def open(self):
        fileName, _ = QFileDialog.getOpenFileName(None, "Open Configuration", "", "JSON Files (*.json)")
        if len(fileName) == 0:
            return
        with open(fileName, 'r') as file:
            info = json.load(file)
        self.ui.arguments.setText(info['arguments'])
        self.ui.variables.setText(info['variables'])
        self.ui.functionName.setText(info['functionName'])
        self.ui.arrayName.setText(info['arrayName'])
        self.ui.playbackSpeed.setValue(info['speed'])
        self.ui.textEdit.setPlainText(info['code'])
        self.savePath = fileName
    
    def save_as(self):
        fileName, _ = QFileDialog.getSaveFileName(None, "Save Configuration", "", "JSON Files (*.json)")
        if len(fileName) == 0:
            return
        self.saveToFile(fileName)
        self.savePath = fileName
    
    def play(self):
        arglist = self.ui.arguments.text()
        if not arglist.endswith(','):
            arglist += ','
        args = ast.literal_eval('(' + arglist + ')')
        array_name = self.ui.arrayName.text().strip()
        variables = ast.literal_eval('[' + self.ui.variables.text() + ']')
        function_name = self.ui.functionName.text().strip()
        if self.realTime:
            self.sim = RealTimeSimulator(self.ui.textEdit.toPlainText(), function_name, args, array_name, variables, self.update, self.getPlaybackSpeed())
        else:
            self.sim = PlaybackSimulator(self.ui.textEdit.toPlainText(), function_name, args, array_name, variables, self.update, self.getPlaybackSpeed())
        self.sim.start()
    
    def stepBack(self):
        if isinstance(self.sim, PlaybackSimulator):
            self.sim.stepBack()
    
    def stepForward(self):
        if isinstance(self.sim, PlaybackSimulator):
            self.sim.stepForward()
    
    def stop(self):
        self.sim.stop()
    
    def reset(self):
        self.sim.reset()
    
    def setRealTime(self):
        checked = self.ui.actionReal_Time.isChecked()
        self.ui.actionPlayback.setChecked(not checked)
        self.realTime = checked
    
    def setPlayback(self):
        checked = self.ui.actionPlayback.isChecked()
        self.ui.actionReal_Time.setChecked(not checked)
        self.realTime = not checked
    
    def draw(self):
        self.scene.clear()
        side = 80
        for i in range(len(self.sim.arr)):
            for j in range(1 if type(self.sim.arr[i]) != list else len(self.sim.arr[i])):
                text = self.scene.addText(str(self.sim.arr[i]) if type(self.sim.arr[i]) != list else str(self.sim.arr[i][j]))
                bound = text.boundingRect()
                text.setPos(i * side + int(side / 2) - int(bound.width() / 2), j * side + int(side / 2) - int(bound.height() / 2))
                if (i, j) in self.sim.var:
                    self.scene.addRect(i * side, j * side, side, side, pen = self.blackPen, brush = self.redBrush)
                else:
                    self.scene.addRect(i * side, j * side, side, side, pen = self.blackPen)
    
    def __init__(self, ui):
        self.savePath = None
        self.sim = None
        self.linesToHighlight = []
        self.ui = ui
        self.ui.play.clicked.connect(self.play)
        self.ui.stop.clicked.connect(self.stop)
        self.ui.reset.clicked.connect(self.reset)
        self.ui.actionSave_As.triggered.connect(self.save_as)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.stepBack.clicked.connect(self.stepBack)
        self.ui.stepForward.clicked.connect(self.stepForward)
        self.ui.actionReal_Time.triggered.connect(self.setRealTime)
        self.ui.actionPlayback.triggered.connect(self.setPlayback)
        font = QtGui.QFont('Consolas', 10)
        ui.stepBack.setIcon(QIcon('res/leftarrow.png'))
        ui.stepForward.setIcon(QIcon('res/rightarrow.png'))
        ui.textEdit.setFont(font)
        ui.textEdit.setCursorWidth(3)
        ui.textEdit.textChanged.connect(self.textChanged)
        ui.playbackSpeed.valueChanged.connect(self.speedChanged)
        self.scene = QtWidgets.QGraphicsScene()
        ui.graphicsView.setScene(self.scene)
        self.blackPen = QtGui.QPen(QtCore.Qt.black)
        self.redPen = QtGui.QPen(QtCore.Qt.red)
        self.blackBrush = QtGui.QBrush(QtCore.Qt.black)
        self.redBrush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 128))