'''
Created on Sep 2, 2016

@author: Sandy
'''
import h5py
import numpy as np
import scipy.optimize as optimise
import pandas as pd
import sys
import constants
from constants import isatSigma


def methodClassFromString(className):
    try:
        return getattr(sys.modules[__name__], className)
    except:
        raise Exception('className doesn\'t exist')

class baseMethod(object):
    def __init__(self,filename,shotFrameIn = pd.DataFrame()):
        self.shotFrame = shotFrameIn
        self.filename = filename

class setlistInformStringParser(baseMethod,object):
    def __init__(self,filename, shotFrameIn = pd.DataFrame()):
        super(setlistInformStringParser,self).__init__(filename,shotFrameIn)
    def doMethod(self):
        #Load file
        h5file = h5py.File(self.filename,'r')
        splitInformString = h5file.get('/Inform/Inform String').value.splitlines()
        currentVariableIndex = splitInformString.index(b'# Current Variables') + 2
        #Grab all the Setlist variables
        while splitInformString[currentVariableIndex] != b'#':
            currSplitLine = splitInformString[currentVariableIndex].split(b'=')
            self.shotFrame[str(currSplitLine[0].strip(),'utf-8')] = [float(currSplitLine[1])]
            currentVariableIndex = currentVariableIndex+1
        #Grab the FileNumber
        fileNumIndex = [i for i, elem in enumerate(splitInformString) if b'FileNumber' in elem]
        self.shotFrame['FileNumber'] = int(splitInformString[fileNumIndex[0]].split(b'=')[1])
        #And the filename
        self.shotFrame['Filename'] = str(self.filename)
    def getVars(self):
        return self.shotFrame
    
class shotFrameToFile(baseMethod,object):
    def __init__(self,filename, shotFrameIn = pd.DataFrame()):
        super(shotFrameToFile,self).__init__(filename,shotFrameIn)
    def doMethod(self):
        hdfFile = pd.HDFStore(self.filename)
        hdfFile.put('/shotFrame/testFrame',self.shotFrame,format='table',data_columns=True)
    def getVars(self):
        return self.shotFrame

class baseImageFitting(baseMethod,object):
    procIm = np.empty([0,0])
    roiPoints = None
    rotationAngle = 0
    magnification = 1.0
    pixelSize = 3.69
    def __init__(self,filename,shotFrameIn = pd.DataFrame()):
        super(baseImageFitting,self).__init__(filename,shotFrameIn)
    def setProcessedImage(self,processedImage):
        self.procIm = processedImage
        if not self.roiPoints:
            self.roiPoints = [1,1,self.procIm.shape[0],self.procIm.shape[1]]
    def getCutImage(self):
        return self.procIm[self.roiPoints[0]:self.roiPoints[0]+self.roiPoints[2],self.roiPoints[1]:self.roiPoints[1]+self.roiPoints[3]]
    def doMethod(self):
        pass
    def getVars(self):
        self.shotFrame['rotAngle'] = self.rotationAngle
        self.shotFrame['roi'] = self.roiPoints
        return self.shotFrame

class absorptionImage(baseImageFitting,object):
    atomNumber = 0
    def __init__(self,filename,shotFrameIn = pd.DataFrame()):
        super(absorptionImage,self).__init__(filename,shotFrameIn)
        dataFile = h5py.File(filename,'r')
        absIm = np.array(dataFile.get('/Images/Absorption'),dtype=float)
        probeIm = np.array(dataFile.get('/Images/Probe'),dtype=float)
        backIm = np.array(dataFile.get('/Images/Background'),dtype=float)
        self.setProcessedImage(-np.log(np.divide(absIm-backIm,probeIm-backIm)))
    def showImage(self,axes,figure):
        #fig = Figure()
        #axes = fig.add_subplot(111)
        #x=axes.imshow(self.getCutImage(),cmap='plasma',clim=(0,np.amax(self.procIm)))
        #divider = make_axes_locatable(axes)
        #cax = divider.append_axes("right", size="5%", pad=0.05)
        #fig.colorbar(x,cax)
        #figure.clf()
        #axes = figure.add_subplot(111)
        axes.cla()
        dummy = axes.imshow(self.getCutImage(),cmap='plasma',clim=(0,np.amax(self.procIm)))
        return axes
    def calculateAtomNumber(self,imagingDetuning,imagingIntensity):
        sigma = constants.sig0Sigma/(1+4*(2*np.pi*imagingDetuning*10**6/constants.gam)**2+(imagingIntensity/isatSigma)) * 10**(-4)
        self.atomNumber = np.sum(self.getCutImage())*(self.pixelSize*10**(-6)/self.magnification)**2/sigma
    def doMethod(self):
        imagingDetuning = 0
        imagingIntensity = 0
        if 'ImagingDetuning' in self.shotFrame.columns:
            imagingDetuning = self.shotFrame['ImagingDetuning']  
        if 'ImagingIntensity' in self.shotFrame.columns:
            imagingIntensity = self.shotFrame['ImagingIntensity']
        self.calculateAtomNumber(imagingDetuning, imagingIntensity)
        super(absorptionImage,self).doMethod()
    def getVars(self):
        self.shotFrame['N_atoms'] = self.atomNumber
        return self.shotFrame
        
class absGaussFit(absorptionImage,object):
    centreX = 0
    centreY = 0
    xCoffs = [0,1,900,300]
    yCoffs = [0,1,500,300]
    def __init__(self,filename,shotFrameIn = pd.DataFrame()):
        super(absGaussFit,self).__init__(filename,shotFrameIn)
    def findCentreCoordinate(self):
        self.centreX = np.argmax(np.sum(self.getCutImage(),axis=0))
        self.centreY = np.argmax(np.sum(self.getCutImage(),axis=1))
    def gaussian(self,x,a,b,c,d):
        return a+b*np.exp(-(x-c)**2/(2*d**2))
    def runXFit(self):
        xVec = np.sum(self.getCutImage()[self.centreY-10:self.centreY+10],axis=0)/21
        xpix = np.arange(0,len(xVec))
        self.xCoffs = optimise.curve_fit(self.gaussian, xpix, xVec, p0=self.xCoffs)[0]
    def runYFit(self):
        yVec = np.sum(self.getCutImage()[:][self.centreX-10:self.centreX+10],axis=0)/21
        ypix = np.arange(0,len(yVec))
        self.yCoffs = optimise.curve_fit(self.gaussian, ypix, yVec, p0=self.yCoffs)[0]
    def doMethod(self):
        self.findCentreCoordinate()
        self.runXFit()
        self.runYFit()
        super(absGaussFit,self).doMethod()
    def getVars(self):
        self.shotFrame['sigma_x'] = self.xCoffs[3]*self.pixelSize/self.magnification
        self.shotFrame['sigma_y'] = self.yCoffs[3]*self.pixelSize/self.magnification
        self.shotFrame['centreX'] = self.xCoffs[2]
        self.shotFrame['centreY'] = self.yCoffs[2]
        return self.shotFrame
        