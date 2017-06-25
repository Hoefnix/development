#!/usr/bin/python
import requests
from requests.auth import HTTPBasicAuth
#from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from http.server import BaseHTTPRequestHandler,HTTPServer
import subprocess
import json
import time

PORT_NUMBER = 1209

lichtpin = 4 # gpio4
prntrpin = 5 # gpio5

class gpioinit( object ):
	def write(self, pin, waarde):
		return 1 - subprocess.call("/usr/local/bin/gpio write %s %s"%(pin,waarde), shell=True )

	def read(self, pin):
		return 1 - int(subprocess.check_output("/usr/local/bin/gpio read %s"%pin, shell=True).decode("utf-8"))

def telegram(message="...", chat_id="12463680"):
#	Johannes_Smits	=  "12463680"
#	alarmsysteem	= "-24143102"
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage?chat_id=%s&text=%s" % (chat_id, message), timeout=5)
	return r.status_code
	
#This class will handles any incoming request from
#the browser 
class myHandler(BaseHTTPRequestHandler):
	
	#Handler for the GET requests
	def log_message(self, format, *args):
		return
		
	#Handler for the GET requests
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		
		command = self.requestline.replace("GET /","").replace("?","")
		command = command[:command.find("HTTP")].strip()

		# ?onderwerp:[aan/uit/flip]
		if	command.startswith("licht"):
			if command.endswith(("aan","uit","flip")):
				if command.endswith("flip"):
					waarde = 1 if gpio.read(lichtpin) else 0
				else:
					waarde = 0 if command[-3:] == "aan" else 1
				gpio.write(lichtpin, waarde)
			self.wfile.write(bytes("%s"%gpio.read(lichtpin), "utf-8"))

		elif command.startswith("printer"):
			if command.endswith(("aan","uit","flp")):
				if command.endswith("flip"):
					waarde = 1 if gpio.read(prntrpin) else 0
				else:
					waarde = 0 if command[-3:] == "aan" else 1
				gpio.write(prntrpin, waarde)				
			self.wfile.write(bytes("%s"%gpio.read(prntrpin), "utf-8"))

		else:
			print( "Opdracht niet begrepen: %s"%command)				
			self.wfile.write( bytes("Opdracht niet begrepen: %s"%command, "utf-8"))				
		return

gpio = gpioinit()

print ("\033[2JDuplicator HTTP server") 
print ("\033[3mControl-C om te stoppen\033[0m")

try:
	# Create a web server and define the handler to manage the incoming request
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	print ("\033[3mHTTPserver gestart op poort %d\n\033[0m"%PORT_NUMBER)
	
	# Wait forever for incoming http requests
	server.serve_forever()

except KeyboardInterrupt:
	print ('^C received, shutting down the web server')
	server.socket.close()
