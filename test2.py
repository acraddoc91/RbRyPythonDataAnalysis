'''
Created on Sep 21, 2016

@author: Sandy
'''
import fittingClasses
import h5py
import pandas as pd
import constants

def shotProcessor(filename,fitType):
    h5file = h5py.File(filename,'r')
    splitInformString = h5file.get('/Inform/Inform String').value.splitlines()
    currentVariableIndex = splitInformString.index('# Current Variables') + 2
    shotFrame = pd.DataFrame()
    while splitInformString[currentVariableIndex] != '#':
        currSplitLine = splitInformString[currentVariableIndex].split('=')
        shotFrame[currSplitLine[0].strip()] = [float(currSplitLine[1])]
        currentVariableIndex = currentVariableIndex+1
    fittingClass = fittingClasses.fittingClassFromString(fitType)
    fitObject = fittingClass(filename)
    fitObject.doFits(shotFrame)
    shotFrame = shotFrame.join(fitObject.getFitVars())
    return shotFrame

out = shotProcessor('C:/Data/27/FleaZ_27Jun2016_0003.h5', 'absGaussFit')
print out