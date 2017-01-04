'''
Created on Oct 5, 2016

@author: Alex
'''
from PyQt5.uic import loadUiType
from PyQt5 import QtGui
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import numpy as np
import pandas as pd
from processing import shotProcessor

Ui_MainWindow,QMainWindow = loadUiType('mainGUI.ui')

class Main(QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(Main,self).__init__()
        self.setupUi(self)
        self.cosPlot.clicked.connect(self.cosPlotFunc)
        self.sinPlot.clicked.connect(self.sinPlotFunc)
        self.loadData.clicked.connect(self.loadDataFunc)
        self.shotData = pd.DataFrame()
        
        fig = Figure()
        self.addmpl(fig)
    def addmpl(self,fig):
        self.canvas = FigureCanvas(fig)
        self.livePlotLay.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas,self,coordinates=True)
        self.livePlotLay.addWidget(self.toolbar)
    def rmmpl(self):
        self.livePlotLay.removeWidget(self.canvas)
        self.canvas.close()
        self.livePlotLay.removeWidget(self.toolbar)
        self.toolbar.close()
    def cosPlotFunc(self):
        self.rmmpl()
        fig = Figure()
        axes = fig.add_subplot(111)
        x = np.linspace(0,2*np.pi,1000)
        axes.plot(x,np.cos(x))
        self.addmpl(fig)
    def sinPlotFunc(self):
        self.rmmpl()
        fig = Figure()
        axes = fig.add_subplot(111)
        x = np.linspace(0,2*np.pi,1000)
        axes.plot(x,np.sin(x))
        self.addmpl(fig)
    def loadDataFunc(self):
        fileDialog = QtWidgets.QFileDialog(self)
        fileDialog.setFilters('*.h5')
        fileDialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        fileDialog.exec_()
        for fileName in fileDialog.selectedFiles():
            print(fileName)
            self.shotData = self.shotData.append(shotProcessor(str(fileName), 'absGaussFit'), ignore_index=True)
            print(self.shotData)

if __name__=='__main__':
    import sys
    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())