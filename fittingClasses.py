'''
Created on Sep 2, 2016

@author: Sandy
'''
import h5py
import numpy as np
from matplotlib.figure import Figure
import scipy.optimize as optimise
import pandas as pd
import sys
import constants
from constants import isatSigma
from mpl_toolkits.axes_grid1 import make_axes_locatable


def fittingClassFromString(className):
    return getattr(sys.modules[__name__], className)

class baseImageFitting(object):
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
    def doFits(self,expParams):
        pass
    def getFitVars(self):
        return pd.DataFrame({'rotAngle':self.rotationAngle,'roi':[self.roiPoints]})

class absorptionImage(baseImageFitting,object):
    atomNumber = 0
    def __init__(self,filename):
            dataFile = h5py.File(filename,'r')
            absIm = np.array(dataFile.get('/Images/Absorption'),dtype=float)
            probeIm = np.array(dataFile.get('/Images/Probe'),dtype=float)
            backIm = np.array(dataFile.get('/Images/Background'),dtype=float)
            self.setProcessedImage(-np.log(np.divide(absIm-backIm,probeIm-backIm)))
    def showImage(self):
        fig = Figure()
        axes = fig.add_subplot(111)
        x=axes.imshow(self.getCutImage(),cmap='plasma',clim=(0,np.amax(self.procIm)))
        divider = make_axes_locatable(axes)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        fig.colorbar(x,cax)
        return fig
    def calculateAtomNumber(self,imagingDetuning,imagingIntensity):
        sigma = constants.sig0Sigma/(1+4*(2*np.pi*imagingDetuning*10**6/constants.gam)**2+(imagingIntensity/isatSigma)) * 10**(-4)
        self.atomNumber = np.sum(self.getCutImage())*(self.pixelSize*10**(-6)/self.magnification)**2/sigma
    def doFits(self,expParams):
        imagingDetuning = 0
        imagingIntensity = 0
        if 'ImagingDetuning' in expParams.columns:
            imagingDetuning = expParams['ImagingDetuning']  
        if 'ImagingIntensity' in expParams.columns:
            imagingIntensity = expParams['ImagingIntensity']
        self.calculateAtomNumber(imagingDetuning, imagingIntensity)
        super(absorptionImage,self).doFits(expParams)
    def getFitVars(self):
        childFrame = pd.DataFrame({'N_atoms':[self.atomNumber]})
        return childFrame.join(super(absorptionImage,self).getFitVars())
        
class absGaussFit(absorptionImage,object):
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
    def doFits(self,expParams):
        self.findCentreCoordinate()
        self.runXFit()
        self.runYFit()
        super(absGaussFit,self).doFits(expParams)
    def getFitVars(self):
        childFrame = pd.DataFrame({'sigma_x':[self.xCoffs[3]*self.pixelSize/self.magnification],'sigma_y':[self.yCoffs[3]*self.pixelSize/self.magnification],'centreX':self.xCoffs[2],'centreY':self.yCoffs[2]})
        return childFrame.join(super(absGaussFit,self).getFitVars())
        