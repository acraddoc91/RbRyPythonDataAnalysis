'''
Created on Oct 11, 2016

@author: Sandy
'''

from PyQt4.uic import loadUiType
from PyQt4.QtCore import (QThread, pyqtSignal,SIGNAL)
from dataServer import (requestServer,requestHandler)
from processing import shotProcessor
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
    def __init__(self):
        super(Main,self).__init__()
        self.setupUi(self)
        self.servThread = serverThread()
        self.servThread.start()
        self.connect(self.servThread, SIGNAL("showData"),self.showData)
        self.connect(self.servThread,SIGNAL('newData'),self.grabNewData)
    def showData(self):
        self.textBox.setText(str(self.data))
    def grabNewData(self):
        self.data = self.data.append(self.servThread.newData,ignore_index=True)
        self.servThread.newData = pd.DataFrame()
        
if __name__=='__main__':
    import sys
    from PyQt4 import QtGui
    app = QtGui.QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())