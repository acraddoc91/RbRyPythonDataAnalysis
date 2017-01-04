'''
Created on Oct 5, 2016

@author: Alex
'''

import fittingClasses
import h5py
import pandas as pd

def shotProcessor(filename,fitType):
    #Load file
    h5file = h5py.File(filename,'r')
    splitInformString = h5file.get('/Inform/Inform String').value.splitlines()
    currentVariableIndex = splitInformString.index(b'# Current Variables') + 2
    #Create a dataFrame to store our variables
    shotFrame = pd.DataFrame()
    #Grab all the Setlist variables
    while splitInformString[currentVariableIndex] != b'#':
        currSplitLine = splitInformString[currentVariableIndex].split(b'=')
        shotFrame[str(currSplitLine[0].strip(),'utf-8')] = [float(currSplitLine[1])]
        currentVariableIndex = currentVariableIndex+1
    #Grab the FileNumber
    fileNumIndex = [i for i, elem in enumerate(splitInformString) if b'FileNumber' in elem]
    shotFrame['FileNumber'] = int(splitInformString[fileNumIndex[0]].split(b'=')[1])
    #And the filename
    shotFrame['Filename'] = str(filename)
    #And the fittype
    shotFrame['FitType'] = str(fitType)
    fittingClass = fittingClasses.fittingClassFromString(fitType)
    fitObject = fittingClass(filename)
    fitObject.doFits(shotFrame)
    shotFrame = shotFrame.join(fitObject.getFitVars())
    return shotFrame

def grabImage(filename,fitType,axes,figure):
    fittingClass = fittingClasses.fittingClassFromString(fitType)
    fitObject = fittingClass(filename)
    image = fitObject.showImage(axes,figure)
    del fitObject
    return image