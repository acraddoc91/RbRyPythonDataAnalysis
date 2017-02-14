'''
Created on Oct 11, 2016

@author: Sandy
'''
import matplotlib as mpl
from PyQt5.Qt import QWidget
mpl.use('Agg')
from PyQt5.uic import loadUiType
from PyQt5.QtCore import (QThread, pyqtSignal)
from dataServer import (requestServer,requestHandler)
from processing import (shotProcessor,grabImage)
from PyQt5.QtWidgets import (QListWidgetItem,QTableWidgetItem, QComboBox, QCheckBox,QFileDialog)
import pandas as pd
import threading
import time
import json
from PyQt5.QtGui import QFont
import os
os.environ['PYQTGRAPH_QT_LIB']='PyQt5'
import pyqtgraph as pg

#This loads the UI we want to use
uiMainWindow, qMainWindow = loadUiType('dataAnalysis.ui')    

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
LabelStyle = {'color': '#000', 'font-size': '24px'}

#This is a server class that will be started as a thread which will sit there and wait for HTTP commands then perform them. It wraps the server itself and allows it to interact with the GUI
class serverThread(QThread):
    #This allows us to trigger actions from the main thread
    trigger = pyqtSignal(int)
    #This holds any newly processed data till it gets grabbed by the main thread
    newData = pd.DataFrame()
    
    newDataSignal = pyqtSignal()
    showDataSignal = pyqtSignal()
    
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
                self.commandString = str(self.server.out,'utf-8')
                #Try and parse the JSON from the command and run the command
                try:
                    command = json.loads(self.commandString)
                    self.runCommand(command)
                #Generally the try block is going to fail because the JSON is fucked up
                except:
                    print('shitty JSON')
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
                    print('Bad request')
            #If data has been processed let the main thread know it needs to update it's data
            if len(self.newData) != 0:
                #self.emit(SIGNAL('newData'))
                self.newDataSignal.emit()
        if 'showData' in command:
            #self.emit(SIGNAL('showData'))
            self.showDataSignal.emit()

#This thread will allow us to asynchonously process files     
class processorThread(QThread):
    #This allows us to trigger actions from the main thread
    trigger = pyqtSignal(int)
    #This holds any newly processed data till it gets grabbed by the main thread
    newData = pd.DataFrame()
    newDataSignal = pyqtSignal()
    showDataSignal = pyqtSignal()
    filenames = []
    methods = []
    processData = True
    
    def __init__(self):
        QThread.__init__(self)
        self.threadExiting = False
    def __del__(self):
        self.wait()
        self.threadExiting = True
    def run(self):
        #This loop keeps the thread going till we want it to die taking commands from HTTP and performing the appropriate actions
        while not self.threadExiting:
            if len(self.filenames) != 0 & self.processData:
                for file in self.filenames[0]:
                    self.newData = self.newData.append(shotProcessor(file, self.methods[0]))
                del self.filenames[0]
                del self.methods[0]
                self.processData = False
                self.newDataSignal.emit()
    def setFilesToProcess(self,filenames,methods):
        self.filenames.append(filenames)
        self.methods.append(methods)
        print(len(self.filenames))

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
        
        #Start processor thread
        self.procThread = processorThread()
        self.procThread.start()
        
        #Setup the data and image figures
        self.dataPlot = pg.PlotWidget()
        self.dataPlotLayout.addWidget(self.dataPlot)
        
        #Connect everything to their relevant functions
        self.procThread.newDataSignal.connect(self.grabNewData)
        self.xAxis.itemClicked.connect(self.plotData)
        self.yAxis.itemClicked.connect(self.plotData)
        self.indexList.itemClicked.connect(self.showImage)
        self.addCut.clicked.connect(self.addCutFunc)
        self.delCut.clicked.connect(self.delCutFunc)
        self.setCuts.clicked.connect(self.setCutsFunc)
        self.addShotMethod.clicked.connect(self.addShotMethodFunc)
        self.removeShotMethod.clicked.connect(self.removeShotMethodFunc)
        self.actionLoad_files.triggered.connect(self.loadFiles)
        
        #Setup cutTable
        self.cutTable.setHorizontalHeaderLabels(['Field','Cut Type','Cut Value','Active'])
    
    #Function called to plot data to the graph in tab 1
    def plotData(self):
        if not self.data.empty:
            xAxisVarName = self.xAxis.currentItem().text()
            yAxisVarname = self.yAxis.currentItem().text()
            try:
                self.dataPlot.plot(self.data[self.grabTruthTable()][str(xAxisVarName)],self.data[self.grabTruthTable()][str(yAxisVarname)],symbol='o',symbolSize=7,pen=None,clear=True)
                self.dataPlot.setLabel('bottom',text=str(xAxisVarName),**LabelStyle)
                self.dataPlot.setLabel('left',text=str(yAxisVarname),**LabelStyle)
            except:
                print('Data type not valid for plotting')
            
    #Function called to update image in tab 2
    def showImage(self):
        pass
        #dummy = self.data[self.data['FileNumber'] == int(str(self.indexList.currentItem().text()))]
        #self.imageFig.clear()
        #self.imageFig = grabImage(dummy['Filename'].values[-1],dummy['FitType'].values[-1])
        #grabImage(dummy['Filename'].values[-1],dummy['FitType'].values[-1],self.imageAxes,self.imageFig)
        #if hasattr(self, 'imageCanvas'):
        #    self.imageIndexLayout.removeWidget(self.imageCanvas)
        #    self.imageCanvas.close()
        #self.imageCanvas = FigureCanvas(self.imageFig)
        #self.imageIndexLayout.addWidget(self.imageCanvas)
        #self.imageCanvas.draw()
        
        #self.imageDataTable.clear()
        #self.imageDataTable.setRowCount(len(self.varNames))
        #for i in range(0,len(self.varNames)):
        #    self.imageDataTable.setItem(i,0,QTableWidgetItem(str(self.varNames[i])))
        #    self.imageDataTable.setItem(i,1,QTableWidgetItem(str(dummy[self.varNames[i]].values[-1])))
        #del dummy
        
    #Function called when data is available in the server thread
    def grabNewData(self):
        self.data = self.data.append(self.procThread.newData,ignore_index=True)
        newNames = [x for x in self.data.columns.values.tolist() if x not in self.varNames]
        for name in newNames:
            self.xAxis.addItem(QListWidgetItem(name))
            self.yAxis.addItem(QListWidgetItem(name))
        for index in self.procThread.newData['FileNumber']:
            self.indexList.addItem(QListWidgetItem(str(index)))
        if self.varNames == []:
            self.xAxis.setCurrentRow(0)
            self.yAxis.setCurrentRow(0)
            self.indexList.setCurrentRow(0)
            self.plotData()
        self.varNames = self.varNames+newNames
        self.procThread.newData = pd.DataFrame() 
        self.procThread.processData = True
        print('new data acquired')
    #Adds a line to the cut table    
    def addCutFunc(self):
        self.cutTable.insertRow(self.cutTable.rowCount())
        numRows = self.cutTable.rowCount()
        varNameComboBox = QComboBox()
        cutTypeComboBox = QComboBox()
        operators = ['==','<','<=','>','>=','!=']
        for name in self.varNames:
            varNameComboBox.addItem(name)
        for operator in operators:
            cutTypeComboBox.addItem(operator)
        self.cutTable.setCellWidget(numRows-1,0,varNameComboBox)
        self.cutTable.setCellWidget(numRows-1,1,cutTypeComboBox)
        self.cutTable.setCellWidget(numRows-1,3,QCheckBox())
    #Removes line from the cut table
    def delCutFunc(self):
        dummy = self.cutTable.selectionModel()
        delRows = []
        for selectObj in dummy.selectedRows():
            delRows.append(selectObj.row())
        del dummy
        delRows = list(reversed(delRows))
        for row in delRows:
            self.cutTable.removeRow(row)
    #Replots when the cut table has been adjusted
    def setCutsFunc(self):
        self.plotData()
    #Returns the truth table for which data points pass the parameters of the cut table
    def grabTruthTable(self):
        rowCount = self.cutTable.rowCount()
        #This should return a truth table that is all true elements
        truthTable = pd.Series([True]*len(self.data))
        for i in range(0,rowCount):
            if self.cutTable.cellWidget(i,3).isChecked():
                field = str(self.cutTable.cellWidget(i,0).currentText())
                cutType = str(self.cutTable.cellWidget(i,1).currentText())
                try:
                    cutValue = float(self.cutTable.item(i,2).text())
                    if cutType == '==':
                        truthTable = truthTable & (self.data[field] == cutValue)
                    elif cutType == '<':
                        truthTable = truthTable & (self.data[field] < cutValue)
                    elif cutType == '>':
                        truthTable = truthTable & (self.data[field] > cutValue)
                    elif cutType == '>=':
                        truthTable = truthTable & (self.data[field] >= cutValue)
                    elif cutType == '<=':
                        truthTable = truthTable & (self.data[field] <= cutValue)
                    elif cutType == '!=':
                        truthTable = truthTable & (self.data[field] != cutValue)
                except:
                    self.cutTable.cellWidget(i,3).setCheckState(0)
                    self.cutTable.cellWidget(i,2).item(i,2).setText('Invalid Cut Value')
        return truthTable
    #Adds a processing method to the shot method table
    def addShotMethodFunc(self):
        self.singleShotMethodsTable.insertRow(self.singleShotMethodsTable.rowCount())
    #Removes a processing method from the shot method table
    def removeShotMethodFunc(self):
        dummy = self.singleShotMethodsTable.selectionModel()
        delRows = []
        for selectObj in dummy.selectedRows():
            delRows.append(selectObj.row())
        del dummy
        delRows = list(reversed(delRows))
        for row in delRows:
            self.singleShotMethodsTable.removeRow(row)
    def loadFiles(self):
        dummy = QWidget()
        filenames = QFileDialog.getOpenFileNames(dummy,'Open File',filter="*.h5")[0]
        methods = self.getMethodListFromTable()
        self.procThread.filenames.append(filenames)
        self.procThread.methods.append(methods)
    def getMethodListFromTable(self):
        rowCount = self.singleShotMethodsTable.rowCount()
        methods = []
        for i in range(0,rowCount):
            methods.append(str(self.singleShotMethodsTable.item(i,0).text()))
        return methods
if __name__=='__main__':
    import sys
    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())