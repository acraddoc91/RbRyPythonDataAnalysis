'''
Created on Sep 2, 2016

@author: Sandy
'''
import h5py
import numpy as np
import matplotlib.pyplot as plt

class baseImageFitting:
    procIm = np.empty([0,0])
    roiPoints = None
    rotationAngle = 0
    magnification = 0
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