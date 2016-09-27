'''
Created on Sep 2, 2016

@author: Sandy
'''
import h5py
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as optimise
import pandas as pd
import sys

def fittingClassFromString(className):
    print sys.modules[__name__]
    return getattr(sys.modules[__name__], className)

class baseImageFitting:
    procIm = np.empty([0,0])
    roiPoints = None
    rotationAngle = 0
    magnification = 1.0
    pixelSize = 3.69
    def setProcessedImage(self,processedImage):
        self.procIm = processedImage
        if not self.roiPoints:
            self.roiPoints = [1,1,self.procIm.shape[0],self.procIm.shape[1]]
    def getCutImage(self):
        return self.procIm[self.roiPoints[0]:self.roiPoints[0]+self.roiPoints[2],self.roiPoints[1]:self.roiPoints[1]+self.roiPoints[3]]

class absorptionImage(baseImageFitting):
    atomNumber = 0
    def __init__(self,filename):
            dataFile = h5py.File(filename,'r')
            absIm = np.array(dataFile.get('/Images/Absorption'),dtype=float)
            probeIm = np.array(dataFile.get('/Images/Probe'),dtype=float)
            backIm = np.array(dataFile.get('/Images/Background'),dtype=float)
            self.setProcessedImage(-np.log(np.divide(absIm-backIm,probeIm-backIm)))
    def showImage(self):
        plt.imshow(self.getCutImage(),cmap='plasma',clim=(0,np.amax(self.procIm)))
        plt.colorbar()
        plt.show()
        
class absGaussFit(absorptionImage):
    centreX = 0
    centreY = 0
    xCoffs = [0,1,900,300]
    yCoffs = [0,1,500,300]
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
    def doFits(self):
        self.findCentreCoordinate()
        self.runXFit()
        self.runYFit()
    def getFitVars(self):
        return pd.DataFrame({'sigma_x':[self.xCoffs[3]],'sigma_y':[self.yCoffs[3]],'N_atoms':self.atomNumber,'centreX':self.xCoffs[2],'centreY':self.yCoffs[2],'rotAngle':self.rotationAngle})
        