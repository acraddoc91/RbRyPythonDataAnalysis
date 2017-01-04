'''
Created on Sep 9, 2016

@author: Sandy
'''
from http.server import (BaseHTTPRequestHandler,HTTPServer)
import socket
from PyQt5.QtCore import (QThread,pyqtSignal)
import threading
import time

#This class will handle requests sent to the data server
class requestHandler(BaseHTTPRequestHandler):
    #This will contain any text we want to store on the server
    out = ''
    #I've had to overload some of these functions from the parent classes to allow me to pass what was read by the handler to the server loop. I've noted modified lines below
    def __init__(self,request,client_address,server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.setup()
        try:
            #Modified to feedback out value
            self.out = self.handle()
        finally:
            self.finish()
    def handle_one_request(self):
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(501, "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            #Modified to grab return from method
            retVal = method()
            self.wfile.flush() #actually send the response if not already done.
            return retVal
        except socket.timeout as e:
            retVal = ''
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = 1
            return retVal
    def handle(self):
        """Handle multiple requests if necessary."""
        self.close_connection = 1
        #Modified all the below to return value from handle_one_request() method
        retVal = self.handle_one_request()
        while not self.close_connection:
            retVal = self.handle_one_request()
        return retVal
    #Added to prevent log message being send to terminal everytime a command is sent
    def log_message(self, format, *args):
        return
    
    #This function is called when a POST request is made to the server. Currently just passes whatever is received to the server
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        postString = self.rfile.read(int(self.headers['Content-Length']))
        self.dummy = postString
        return postString

#This class is designed to take what is obtained by the request
class requestServer(HTTPServer):
    out = ''
    update = False
    #I've overloaded the method from the parent class to update some variables stored by the server
    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        dummyHandler = self.RequestHandlerClass(request, client_address, self)
        self.out = dummyHandler.out
        self.update = True

class serverThread(QThread):
    trigger = pyqtSignal(int)
    def __init__(self):
        QThread.__init__(self)
        self.threadExiting = False
        self.text = ''
    def __del__(self):
        self.wait()
        self.threadExiting = True
    def run(self):
        server_address = ('127.0.0.1',8000)
        self.server = requestServer(server_address,requestHandler)
        threading.Thread(target=self.server.serve_forever).start()
        while not self.threadExiting:
            if self.server.update:
                self.text = self.server.out
                self.server.update = False
                self.emit(SIGNAL("update"))
            time.sleep(0.1)