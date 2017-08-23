#!/usr/bin/env python3


'''
GPIO METHODS
============

init() - Make initialization of the module. Always must be called first.
getcfg() - Read current configuration of gpio.
setcfg() - Write configuration to gpio.
input() - Return current value of gpio.
output() - Set output value.
pullup() - Set pull-up/pull-down.


The available constants are:

NAME - EQUALS TO
==== =========
HIGH -> 1
LOW -> 0
INPUT -> 0
OUPTUT -> 1
PULLUP -> 1
PULLDOWN -> 2
'''

import subprocess
import signal
import requests
import os
import time
import threading
from http.server import BaseHTTPRequestHandler,HTTPServer
from random import randint

from pyA20.gpio import gpio
from pyA20.gpio import port
from pyA20.gpio import connector

# telegram adressen
Johannes_Smits	=  "12463680"
alarmsysteem	= "-24143102"
deurbel			= "-15033899"

def bericht(message=None, Telegram=False, viaPushover=False):
	if not message is None:
		print("\033[3m%s\033[0m - %s"%(time.strftime("%H:%M:%S"),message))
		if Telegram:
			telegram(message=message)
		if viaPushover:
			pushover( bericht = message )
	
def pushover(titel = "Tuinhuis", bericht = "" ):
	try:
		r = requests.post('https://api.pushover.net/1/messages.json', 
			data = {	'token'	:'aYs6YxK8qV1KnGV1LEHzQQtFTrCutk', 
						'user'	:'udEe5uL7YjuyYLyhQXBjvjnqiGGsf8', 
						'title'	:titel,
						'message':bericht})
	except requests.Timeout as e:
		bericht("Pushover - %s"%e)
	except:
		bericht("Pushover - Fout")
	return

def telegram( chat_id="12463680", message = None, image = None ):
	#	johannes_smits	=  "12463680"
	#	alarmsysteem	= "-24143102"
	if not message is None:
		url = "https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage"
		payload = {"chat_id":chat_id, "text":message, "parse_mode":"HTML"}
		r = requests.get(url, params=payload)	
		return (r.json()["ok"])
		
	elif not image is None:
		url	= "https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendPhoto"
		data	= {'chat_id': chat_id}
		files	= {'photo': (image, open(image, "rb"))}
		r = requests.post(url, data=data, files=files)
		return (r.json()["ok"])
		
class ds18b20(object):
	def __init__(self):
		self.file = "/sys/bus/w1/devices/28-800000036068/w1_slave"
		self.waarde = 0
		self.interval = randint(275,325)
		self.check()
		bericht("Temperatuur wordt iedere %i seconden opgehaald. Het is %s graden"%(self.interval,self.waarde))
	
	def check(self):
		self.thread = threading.Timer(self.interval, self.check)
		self.thread.start()
		
		try:
			with open(self.file, 'r') as content_file:
				content = content_file.read()
			self.waarde = int(content[content.find("t=")+2:])/1000
		except:
			bericht("Fout bij ophalen temperatuur")
			
	def stop(self):
		bericht("Temperatuur check wordt gestopt..."%self.gpio)
		self.thread.cancel()

		return self.waarde

class aanuit(object):
	def __init__(self, pin):
		self.aanuit = 0
		self.gpio = pin
		gpio.setcfg(self.gpio, gpio.OUTPUT)	# Configure for use with relais
		self.interval = randint(275,325)		
		self.check()
		bericht("Waarde GPIO(%s) wordt iedere %i seconden opgehaald. Waarde is nu %s"%(self.gpio, self.interval, self.aanuit))
			
	def schakel(self, aanofuit):
		if aanofuit == "flp":
			aanofuit = "uit" if self.aanuit == 1 else "aan"
			
		self.aanuit = gpio.HIGH if aanofuit == "aan" else gpio.LOW
		bericht("GPIO%s is %s wordt %s (%s)"%(self.gpio, gpio.input(self.gpio), self.aanuit, aanofuit))

		gpio.output(self.gpio, self.aanuit)
		self.aanuit = gpio.input(self.gpio) # doublecheck
		return self.aanuit

	def check(self):
		self.thread = threading.Timer(self.interval, self.check)
		self.thread.start()
		self.aanuit = gpio.input(self.gpio)
		return self.aanuit

	def stop(self):
		bericht("GPIO%s check wordt gestopt..."%self.gpio)
		self.thread.cancel()
		
class deursensor(object):
	def __init__(self, pin):
		self.interval = 2
		self.gpio = pin
		gpio.setcfg(self.gpio, gpio.INPUT)	# Configure for deursensor
		self.waarde = gpio.input(self.gpio)	
		self.check()
		self.waarschuwing()
		bericht("Waarde deursensor wordt iedere %i seconden opgehaald. Waarde is nu %s"%(self.interval, self.waarde))

	def check(self):
		self.thread = threading.Timer(self.interval, self.check)
		self.thread.start()
		
		if self.waarde != gpio.input(self.gpio):
			self.waarde = gpio.input(self.gpio)
			tekst = "open" if (self.waarde == 1) else "dicht"
			telegram(message = "Tuinhuisdeur is %s"%tekst) # laat het de wereld weten
			try:
				requests.get("http://192.168.178.50:1208?schuurdeur:%s"%tekst, timeout=2)	# update de status in homebridge
			except:				
				print("\033[3m%s\033[0m - probleem bij deurstatus update"%time.strftime("%H:%M:%S"))
		return self.waarde

	def waarschuwing(self, uren = [22,23]):
		self.thread2 = threading.Timer(900, self.waarschuwing)
		self.thread2.start()

		if (int(time.strftime("%H")) in uren):
			if self.waarde: #  de deur is open
				telegram(alarmsysteem, "De deur van het tuinhuis staat nog open")

	def stop(self):
		bericht("GPIO(%s) check wordt gestopt..."%self.gpio)
		self.thread.cancel()
		self.thread2.cancel()
		
#	this class will handles any incoming request from the browser 
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

	def do_GET(self):
		command = self.requestline.replace("GET /","").replace("?","")
		command = command[:command.find("HTTP")].strip()
		
		if "update" == command:
			self.respond("Status wordt bijgewerkt")
			threading.Thread(target=temperatuur.check).start()

		elif command.startswith("schakelaar"):
			if command.endswith(("aan","uit","flp")):
				schakelaar.schakel(command[-3:])
			self.respond('{"schakelaar":%s}'%schakelaar.aanuit)
			
		elif command.startswith("deur"):
			self.respond('{"deur":%s}'%deur.waarde)

		elif command.startswith("temperatuur"):
			self.respond('{"temperatuur":%s}'%temperatuur.waarde)

		else:
			with open("/sys/class/thermal/thermal_zone1/temp" , 'r') as content_file:
				cputemp = int(content_file.read())
				 
			self.respond('{"temperatuur":%s,"deur":%s,"schakelaar":%s,"cpu":%s}'%(temperatuur.waarde,deur.waarde,schakelaar.aanuit,cputemp))
		return

gpio.init() #Initialize module. Always called first
#gpio.setcfg(10, gpio.INPUT)	# Configure GPIO10 as input DS18B20

bericht("Gestart op de %s"%os.uname()[1],viaPushover=True)
try:
	deur	= deursensor(11)	#	reed-schakelaar op GPIO11
	schakelaar	= aanuit(port.PA14)	#	relais voor verlichting
	temperatuur	= ds18b20() 
	
#	-------
	server = HTTPServer(('', 1208), myHandler)
	server.serve_forever() # Wait forever for incoming http requests
#	-------

except KeyboardInterrupt:
	bericht ('ctrl-C ontvangen, tuinhuis wordt gestopt')
	deur.stop()
	schakelaar.stop()
	
	subprocess.call("/usr/bin/screen -dmLS tuinhuis sudo python3 %s"%__file__, shell=True)
