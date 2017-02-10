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
import os
os.environ['PYQTGRAPH_QT_LIB']='PyQt5'
import pyqtgraph as pg

Ui_MainWindow,QMainWindow = loadUiType('mainGUI.ui')

class Main(QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(Main,self).__init__()
        self.setupUi(self)
        self.cosPlot.clicked.connect(self.cosPlotFunc)
        self.sinPlot.clicked.connect(self.sinPlotFunc)
        fig = Figure()
        self.addmpl(fig)
    def addmpl(self,fig):
        self.plotter = pg.PlotWidget()
        self.livePlotLay.addWidget(self.plotter)
    def cosPlotFunc(self):
        self.plotter.clear()
        x = np.linspace(0,2*np.pi,100)
        self.plotter.plot(x,np.cos(x),symbol='o',symbolSize=5,pen=None,clear=True)
        self.plotter.setLabel('bottom',text='x')
        self.plotter.setLabel('left',text='y')
    def sinPlotFunc(self):
        x = np.linspace(0,2*np.pi,1000)
        self.plotter.plot(x,np.sin(x),symbol='o',clear=True)
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