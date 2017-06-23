#!/usr/bin/python3

import RPi.GPIO as GPIO
import requests
import time
import socket
from PIL import Image, ImageStat, ImageDraw, ImageFont
import subprocess
from http.server import BaseHTTPRequestHandler,HTTPServer
import threading

PORT_NUMBER = 1964

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

def bericht(message=None):
	if not message is None:
		print("\033[3m%s\033[0m - %s\033[0m"%(time.strftime("%H:%M:%S"),message))
		
class lichtsterkte(object):
	def __init__(self, seconden=300):
		self.start = 0
		self.interval = seconden
		self.lichtsterkte = 0
		bericht ("Class lichtsterkte is gereed, interval is %s seconden"%self.interval)
		self.check()
							
	def check(self):
		self.thread = threading.Timer(self.interval, self.check)
		self.thread.start()
		
		if time.time()-self.start < self.interval:
			return self.lichtsterkte
		self.start = time.time()
		
		subprocess.call("/usr/bin/fswebcam -c /home/pi/bureauPi.cfg", shell=True)
		try:
			im = Image.open( '/var/tmp/bureauPi.jpg' )
			stat = ImageStat.Stat(im)
			self.lichtsterkte = int(stat.mean[0])
			# Average (arithmetic mean) pixel level for each band in the image.
	
			with open('/var/www/html/lichtsterkte.json', 'w') as myfile:
				data = myfile.write('{"licht":%s}'%int(self.lichtsterkte)) 
					
			bericht ("Lichtsterkte is %s"%(self.lichtsterkte))

			return self.lichtsterkte
		except:
			return self.lichtsterkte
			
	def stop(self):
		bericht("Lichtsterkte wordt gestopt...")
		self.thread.cancel()
			
class schakelaar(object):
	def __init__(self, nummer, initialstate = 0):
		self.pin	= nummer
		self.status = initialstate
		
		GPIO.setup(self.pin, GPIO.OUT)
		GPIO.output(self.pin, self.status)
		bericht("pin %s is ingesteld, status is %s"%(self.pin, self.status))

	def schakel(self, aanofuit): # waarden: aan/uit/flp
		self.status = GPIO.input(self.pin)
		if aanofuit == "flp":
			self.status = not GPIO.input(self.pin)
		else:
			self.status = 0 if aanofuit == "aan" else 1 
		GPIO.output(self.pin, self.status)
		return "aan" if self.status == 0 else "uit"

	def check(self):
		self.status = GPIO.input(self.pin)
		return self.status
			
class myHandler(BaseHTTPRequestHandler):
	def log_message(self, format, *args):
		return

	def do_HEAD(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def respond(self, response=None):
		bericht("\033[12G\033[35mResponse: %s\033[K\033[F"%response)
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		
		if not response is None:
			try:
				self.wfile.write( bytes(response,"utf-8")  )
			except Exception as e:
				bericht("\033[31m%s bij %s"%(e, response))
				pass

#	Handler for the GET requests
	def do_GET(self):		
		command = self.requestline.replace("GET /","").replace("?","")
		command = command[:command.find("HTTP")].strip()
		
#		Aan, Uit, Toggle /?onderwerp:[aan/uit/flp]

		if "status" == command:
			antwoord  =	"{"
			antwoord +=	"\"lichtsterkte\":%s, "%licht.lichtsterkte
			antwoord += "\"bureau\":%s, "%bureau.status
			antwoord += "\"bureaulamp\":%s, "%bureaulamp.status
			antwoord += "\"printer\":%s"%printer.status
			antwoord += "}"
			
			self.respond( antwoord )
			
		elif command.startswith("printer"):
			if	command.endswith(("aan","uit","flp")):
				bericht("printer is %s gezet"%printer.schakel(command[-3:]) )
			self.respond("%s"%printer.status)
			
		elif command.startswith("bureaulamp"):
			if	command.endswith(("aan","uit","flp")):
				bericht("bureaulamp is %s gezet"%bureaulamp.schakel(command[-3:]) )
			self.respond("%s"%bureaulamp.status)
			
		elif command.startswith("bureau"):
			if	command.endswith(("aan","uit","flp")):
				bericht("bureau is %s gezet"%bureau.schakel(command[-3:]) )
			self.respond("%s"%bureau.status)
			
		elif command.startswith("relais"):
			if	command.endswith(("aan","uit","flp")):
				bericht("relais is %s gezet"%relais.schakel(command[-3:]) )
			self.respond("%s"%relais.status)
		else:
			self.respond("BureauPi luistert naar [status|printer|bureaulamp|bureau|relais]")
		return

try:
	bericht("Bureaupi start op...")
	licht		= lichtsterkte(300) # iedere vijf minuten lichtsterkte checken
	server		= HTTPServer(('', PORT_NUMBER), myHandler)
	
	printer		= schakelaar(29,1)	# (gpio  5)
	bureau		= schakelaar(31,1)	# (gpio  6)
	bureaulamp	= schakelaar(32,1)	# (gpio 12)
	relais		= schakelaar(33,1)	# (gpio 13)

	bericht("Luistert naar poort %d"%PORT_NUMBER)	
	server.serve_forever()

except KeyboardInterrupt:
	bericht("ctrl-c ontvangen, bureaupi wordt opnieuw gestart")
	licht.stop()
							
	subprocess.call("screen -dmLS bureauPi python3 /opt/development/bureauPi.py", shell=True)