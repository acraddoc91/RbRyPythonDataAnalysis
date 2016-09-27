'''
Created on Sep 21, 2016

@author: Sandy
'''
import fittingClasses
import h5py
import pandas as pd

def shotProcessor(filename,fitType):
    h5file = h5py.File(filename,'r')
    splitInformString = h5file.get('/Inform/Inform String').value.splitlines()
    currentVariableIndex = splitInformString.index('# Current Variables') + 2
    shotFrame = pd.DataFrame()
    while splitInformString[currentVariableIndex] != '#':
        currSplitLine = splitInformString[currentVariableIndex].split('=')
        shotFrame[currSplitLine[0]] = [float(currSplitLine[1])]
        currentVariableIndex = currentVariableIndex+1
    return shotFrame

shotProcessor('C:/Data/27/FleaZ_27Jun2016_0002.h5', 'absGaussFit')