'''
Created on Oct 14, 2016

@author: Sandy
'''
import requests
import json
import time
url = 'http://127.0.0.1:8000'
procList = []
for i in range(1,10):
    filename = 'C:/Data/27/FleaZ_27Jun2016_%04d.h5' %i
    procList.append({"filename":filename,"fitType":"absGaussFit"})
payload = {'process':procList}
requests.post(url,json.dumps(payload))