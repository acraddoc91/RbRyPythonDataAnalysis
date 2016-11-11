'''
Created on Nov 11, 2016

@author: Sandy
'''
import matplotlib as mpl
mpl.use('Agg')
from PyQt4.uic import loadUiType
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (FigureCanvasQTAgg as FigureCanvas)
import numpy as np

#This loads the UI we want to use
uiMainWindow, qMainWindow = loadUiType('matplotlibMemoryLeakTest.ui')

class Main(qMainWindow,uiMainWindow):
    def __init__(self):
        #Do the super initialisation and setup the UI
        super(Main,self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.newPlot)
        
        self.plotFigure = Figure()
        self.axes = self.plotFigure.add_subplot(111)
        x = np.linspace(0,2*np.pi,100)
        self.axes.plot(x,np.sin(x+np.random.random()*2*np.pi))
        self.plotCanvas = FigureCanvas(self.plotFigure)
        self.plotWidgetLayout.addWidget(self.plotCanvas)
        self.plotCanvas.draw()
        
    def newPlot(self):
        #self.plotWidgetLayout.removeWidget(self.plotCanvas)
        #self.plotCanvas.close()
        #self.plotFigure = Figure()
        #self.axes = self.plotFigure.add_subplot(111)
        x = np.linspace(0,2*np.pi,100)
        self.axes.cla()
        self.axes.plot(x,np.sin(x+np.random.random()*2*np.pi))
        #self.plotCanvas = FigureCanvas(self.plotFigure)
        #self.plotWidgetLayout.addWidget(self.plotCanvas)
        self.plotCanvas.draw()

if __name__=='__main__':
    import sys
    from PyQt4 import QtGui
    app = QtGui.QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())