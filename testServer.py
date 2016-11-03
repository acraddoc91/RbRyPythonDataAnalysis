'''
Created on Oct 11, 2016

@author: Sandy
'''
import matplotlib as mpl
mpl.use('Agg')
from PyQt4.uic import loadUiType
from PyQt4.QtCore import (QThread, pyqtSignal,SIGNAL,Qt)
from dataServer import (requestServer,requestHandler)
from processing import (shotProcessor,grabImage)
from PyQt4.QtGui import (QListWidgetItem,QTableWidgetItem, QComboBox, QCheckBox,
    QWidget, QHBoxLayout)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (FigureCanvasQTAgg as FigureCanvas)
import pandas as pd
import threading
import time
import json

#This loads the UI we want to use
uiMainWindow, qMainWindow = loadUiType('testServer.ui')    

#This is a server class that will be started as a thread which will sit there and wait for HTTP commands then perform them. It wraps the server itself and allows it to interact with the GUI
class serverThread(QThread):
    #This allows us to trigger actions from the main thread
    trigger = pyqtSignal(int)
    #This holds any newly processed data till it gets grabbed by the main thread
    newData = pd.DataFrame()
    def __init__(self):
        QThread.__init__(self)
        self.threadExiting = False
    def __del__(self):
        self.wait()
        self.threadExiting = True
    #This code is called when the thread is run
    def run(self):
        #Here we set up a server in it's own thread so it is non-blocking
        server_address = ('127.0.0.1',8000)
        self.server = requestServer(server_address,requestHandler)
        threading.Thread(target=self.server.serve_forever).start()
        #This loop keeps the thread going till we want it to die taking commands from HTTP and performing the appropriate actions
        while not self.threadExiting:
            #Check if anything has updated on server
            if self.server.update:
                #Grab command string from the server
                self.commandString = self.server.out
                #Try and parse the JSON from the command and run the command
                try:
                    command = json.loads(self.commandString)
                    self.runCommand(command)
                #Generally the try block is going to fail because the JSON is fucked up
                except:
                    print 'shitty JSON'
                #Reset the server update status
                self.server.update = False
            #Sleep for a bit so we're not constantly looping
            time.sleep(0.1)
    #If a command comes in this parses that command and executes it
    def runCommand(self,command):
        #Check to see if we're being asked to process a file
        if 'process' in command:
            #Grab the filename(s) and fittype(s) and process them
            for procRequest in command['process']:
                try:
                    filename = procRequest['filename']
                    fitType = procRequest['fitType']
                    self.newData = self.newData.append(shotProcessor(filename, fitType), ignore_index=True)
                except:
                    print 'Bad request'
            #If data has been processed let the main thread know it needs to update it's data
            if len(self.newData) != 0:
                self.emit(SIGNAL('newData'))
        if 'showData' in command:
            self.emit(SIGNAL('showData'))

class Main(qMainWindow,uiMainWindow):
    #This is our main data frame. It will hold all our data, equivalent to the main workspace in Matlab
    data = pd.DataFrame()
    varNames = []
    def __init__(self):
        #Do the super initialisation and setup the UI
        super(Main,self).__init__()
        self.setupUi(self)
        
        #Start the server thread to grab our data and whatnot
        self.servThread = serverThread()
        self.servThread.start()
        
        #Setup the data and image figures
        self.dataFig = Figure()
        self.imageFig = Figure()
        
        #Connect everything to their relevant functions
        self.connect(self.servThread,SIGNAL('newData'),self.grabNewData)
        self.xAxis.itemClicked.connect(self.plotData)
        self.yAxis.itemClicked.connect(self.plotData)
        self.indexList.itemClicked.connect(self.showImage)
        self.addCut.clicked.connect(self.addCutFunc)
        self.delCut.clicked.connect(self.delCutFunc)
        self.setCuts.clicked.connect(self.setCutsFunc)
        
        #Setup cutTable
        self.cutTable.setHorizontalHeaderLabels(['Field','Cut','Active'])
    
    #Function called to plot data to the graph in tab 1
    def plotData(self):
        if not self.data.empty:
            xAxisVarName = self.xAxis.currentItem().text()
            yAxisVarname = self.yAxis.currentItem().text()
            self.dataFig.clear()
            axes = self.dataFig.add_subplot(111)
            axes.plot(self.data[str(xAxisVarName)],self.data[str(yAxisVarname)],'.')
            axes.set_xlabel(str(xAxisVarName))
            axes.set_ylabel(str(yAxisVarname))
            if hasattr(self, 'plotCanvas'):
                self.dataPlotLayout.removeWidget(self.plotCanvas)
                self.plotCanvas.close()
            self.plotCanvas = FigureCanvas(self.dataFig)
            self.dataPlotLayout.addWidget(self.plotCanvas)
            self.plotCanvas.draw()
            del axes
            
    #Function called to update image in tab 2
    def showImage(self):
        dummy = self.data[self.data['FileNumber'] == int(str(self.indexList.currentItem().text()))]
        self.imageFig.clear()
        self.imageFig = grabImage(dummy['Filename'].values[-1],dummy['FitType'].values[-1])
        if hasattr(self, 'imageCanvas'):
            self.imageIndexLayout.removeWidget(self.imageCanvas)
            self.imageCanvas.close()
        self.imageCanvas = FigureCanvas(self.imageFig)
        self.imageIndexLayout.addWidget(self.imageCanvas)
        self.imageCanvas.draw()
        
        self.imageDataTable.clear()
        self.imageDataTable.setRowCount(len(self.varNames))
        for i in xrange(0,len(self.varNames)):
            self.imageDataTable.setItem(i,0,QTableWidgetItem(str(self.varNames[i])))
            self.imageDataTable.setItem(i,1,QTableWidgetItem(str(dummy[self.varNames[i]].values[-1])))
        del dummy
        
    #Function called when data is available in the server thread
    def grabNewData(self):
        self.data = self.data.append(self.servThread.newData,ignore_index=True)
        newNames = [x for x in self.data.columns.values.tolist() if x not in self.varNames]
        for name in newNames:
            self.xAxis.addItem(QListWidgetItem(name))
            self.yAxis.addItem(QListWidgetItem(name))
        for index in self.servThread.newData['FileNumber']:
            self.indexList.addItem(QListWidgetItem(str(index)))
        if self.varNames == []:
            self.xAxis.setCurrentRow(0)
            self.yAxis.setCurrentRow(0)
            self.indexList.setCurrentRow(0)
            self.plotData()
        self.varNames = self.varNames+newNames
        self.servThread.newData = pd.DataFrame()  
    def addCutFunc(self):
        self.cutTable.insertRow(self.cutTable.rowCount())
        numRows = self.cutTable.rowCount()
        newComboBox = QComboBox()
        for name in self.varNames:
            newComboBox.addItem(name)
        self.cutTable.setCellWidget(numRows-1,0,newComboBox)
        self.cutTable.setCellWidget(numRows-1,2,QCheckBox())
    def delCutFunc(self):
        dummy = self.cutTable.selectionModel()
        delRows = []
        for selectObj in dummy.selectedRows():
            delRows.append(selectObj.row())
        del dummy
        delRows = list(reversed(delRows))
        for row in delRows:
            self.cutTable.removeRow(row)
    def setCutsFunc(self):
        rowCount = self.cutTable.rowCount()
        for i in xrange(0,rowCount):
            if self.cutTable.cellWidget(i,2).isChecked():
                field = str(self.cutTable.cellWidget(i,0).currentText())
                cutText = str(self.cutTable.item(i,1).text())
                andSplitCutText = cutText.split('&&')
                for andSplitString in andSplitCutText:
                    orSplitString = andSplitString.split('||')
                    print orSplitString
        
if __name__=='__main__':
    import sys
    from PyQt4 import QtGui
    app = QtGui.QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())