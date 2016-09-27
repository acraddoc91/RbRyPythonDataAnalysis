'''
Created on Sep 9, 2016

@author: Sandy
'''
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import fittingClasses

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if format == 'html':
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-type", 'text-html')
            self.end_headers()
            self.wfile.write("body")
        elif format == 'json':
            self.request.sendall(json.dumps({'path':self.path}))
        else:
            self.request.sendall("%s\t%s" %('path',self.path))
        return
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        if self.headers['Content-type'] == 'application/json':
            postString = self.rfile.read(int(self.headers['Content-Length']))
            print postString
            postJSON = json.loads(postString)
            if 'doFit' in postJSON:
                for i in range(len(postJSON['doFit'])):
                    print postJSON['doFit'][i]['fitType']
                    print postJSON['doFit'][i]['fitParameters']   
        return
    
    
def run(port=8000):
    print 'http server is starting'
    server_address = ('127.0.0.1',port)
    httpd = HTTPServer(server_address,Handler)
    print('http server is running')
    httpd.serve_forever()
    
if __name__ == '__main__':
    run()