'''
Created on Oct 5, 2016

@author: Alex
'''

import methodClasses
import h5py
import pandas as pd

def shotProcessor(filename,methods):
    shotFrame = pd.DataFrame()
    for method in methods:
        try:
            methodClass = methodClasses.methodClassFromString(method)
        except:
            print('\"%s\" method name wasn\'t recognised' % (str(method)))
            continue
        methodObject = methodClass(filename,shotFrame)
        methodObject.doMethod()
        shotFrame = methodObject.getVars()
    return shotFrame

def grabImage(filename,fitType,axes,figure):
    fittingClass = methodClasses.methodClassFromString(fitType)
    fitObject = fittingClass(filename)
    image = fitObject.showImage(axes,figure)
    del fitObject
    return image