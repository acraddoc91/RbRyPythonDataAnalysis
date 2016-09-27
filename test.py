'''
Created on Sep 2, 2016

@author: Sandy
'''
from fittingClasses import absorptionImage

import testGUI
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
from matplotlib.figure import Figure
import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

class Mainwindow(QMainWindow,testGUI.Ui_MainWindow):
    def __init__(self):
        super(Mainwindow,self).__init__()
        self.setupUi(self)
        self.assignWidgets()
        self.fig1 = Figure()
        self.ax1f1 = self.fig1.add_subplot(111)
        self.appmpl(self.fig1)
        
    def assignWidgets(self):
        self.pushButton.clicked.connect(self.buttPushed)
        
    def buttPushed(self):
        test = absorptionImage('C:/Data/2016/July/20/FleaZ_20Jul2016_0091.h5')
        self.ax1f1.clear()
        self.ax1f1.imshow(test.getCutImage(),cmap='plasma',clim=(0,np.amax(test.procIm)))
        self.canvas.draw()
        
    def appmpl(self,fig):
        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = Mainwindow()
    main.show()
    sys.exit(app.exec_())
    