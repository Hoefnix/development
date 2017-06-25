#!/usr/bin/python
import requests
from requests.auth import HTTPBasicAuth
from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import time
import socket
import os
import ephem
import datetime
import subprocess
import threading

from random import randint

PORT_NUMBER = 1208

lichtpin = 4 # gpio4
prntrpin = 5 # gpio5

thread = None # voor getstatus() thread

class gpioinit( object ):
	def write(self, pin, waarde):
		return 1 - subprocess.call("/usr/local/bin/gpio write %s %s"%(pin,waarde), shell=True )

	def read(self, pin):
		return 1 - int(subprocess.check_output("/usr/local/bin/gpio read %s"%pin, shell=True).decode("utf-8"))
		
def empty(myString):
	if myString == "nil":
		return True
	elif myString and myString.strip():	#	myString is not None AND myString is not empty or blank
		return False
	return True
	
def isnumeric( waarde ):
    try:
        float( waarde )
        return True
    except ValueError:
        return False

def bericht(message=None, viaTelegram=False, viaPushover=False):
	if not message is None:
		print("\033[3m%s\033[0m - %s\033[0m"%(time.strftime("%H:%M:%S"),message))
		if viaTelegram:
			telegram(message)
		if viaPushover:
			pushover(message)
			
def telegram(message="...", chat_id="12463680"):
	#	johannes_smits	=  "12463680"
	#	alarmsysteem	= "-24143102"
	try:
		r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage?chat_id=%s&text=%s" % (chat_id, message), timeout=5)
	except requests.Timeout as e:
		bericht("Telegram - %s"%e)
	except:
		bericht("Telegram - Fout")
	return

def pushover( bericht = "" ):
	try:
		r = requests.post('https://api.pushover.net/1/messages.json', data = {'token':'aYs6YxK8qV1KnGV1LEHzQQtFTrCutk', 'user':'udEe5uL7YjuyYLyhQXBjvjnqiGGsf8', 'title':'httplistner', 'message':bericht})
	except requests.Timeout as e:
		bericht("Pushover - %s"%e)
	except:
		bericht("Pushover - Fout")
	return

def getstatus():
	global schakelaars, sensoren, thread
	
	thread = threading.Timer(randint(275,325), getstatus)
	thread.start()
		
	bericht("Status bijgewerkt, licht aan tussen %s en %s"%(showtime(woonkamer.lichtaan),showtime(zononder())))
	return 
	
def showtime(tijd):
	lokaletijd = time.localtime(tijd)
	weekdagen = {0:"zondag",1:"maandag",2:"dinsdag",3:"woensdag",4:"donderdag",5:"vrijdag",6:"zaterdag"}
	dag = weekdagen[int(time.strftime("%w", lokaletijd))]
	return "%s %s"%(dag, time.strftime("%H:%M", lokaletijd))

def waarde( w ):
	if type(w) is float:
		return w
	elif type(w) is int:
		return w
	else:
		return -99
		
def zononder():
	capijs		= ephem.Observer()
	capijs.lat	= '51.916905'
	capijs.long	=  '4.563472'
		
	sun = ephem.Sun() # define sun as object of interest
#	sun.compute(capijs)
	return ephem.localtime(capijs.next_setting(sun)).timestamp()
		
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

#	Handler for the GET requests
	def do_GET(self):
		global schakelaars
		
		command = self.requestline.replace("GET /","").replace("?","")
		command = command[:command.find("HTTP")].strip()
		
		bericht( "%s\n"%command )
		
		if "status" == command:
			self.respond("Status wordt bijgewerkt")
			threading.Thread(target=getstatus).start()
			# getstatus()
			
		elif "getpid" == command:
			self.respond( "%s"%os.getpid() )
			
		elif command.startswith("duplicator"):
			if command.endswith(("aan","uit","flp")):
				if command.endswith("flp"):
					waarde = 1 if gpio.read(prntrpin) else 0
				else:
					waarde = 0 if command[-3:] == "aan" else 1
				gpio.write(prntrpin, waarde)
			self.respond("%s"%gpio.read(prntrpin))
			
		elif command.startswith("duplilicht"):
			if command.endswith(("aan","uit","flp")):
				if command.endswith("flp"):
					waarde = 1 if gpio.read(lichtpin) else 0
				else:
					waarde = 0 if command[-3:] == "aan" else 1
				gpio.write(lichtpin, waarde)
			self.respond("%s"%gpio.read(lichtpin))
			
		else:
			bericht( "Opdracht niet begrepen: %s"%command)				
			self.respond("Opdracht niet begrepen: %s"%command)				
		return
		
def httpGet( httpCall, wachten = 4):
	bericht( "\033[33mhttpGet: %s"%httpCall )
	resultaat = requests.Response
	try:
		resultaat = requests.get(httpCall, timeout=wachten)
	except requests.Timeout as e:
		bericht("\033[31m%s: url=%s, timeout=%s"%(e, httpCall, wachten))
		resultaat.status_code = 999
	except:
		bericht("\033[31mFout: url=%s, timeout=%s"%(httpCall,wachten))
		resultaat.status_code = 999
	return resultaat
			
try:
#	Create a web server and define the handler to manage the incoming request
	gpio = gpioinit()
	
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	with open('/var/tmp/dupllistner.pid', 'w') as myfile:
		data = myfile.write( '{"pid":%s}'%os.getpid() )
	bericht("%s luistert naar poort %d"%(__file__, PORT_NUMBER), viaPushover = True)
	
#	Wait forever for incoming http requests
	server.serve_forever()

except KeyboardInterrupt:
	bericht("ctrl-c ontvangen, dupllistner wordt opnieuw gestart", viaPushover = True)
	server.socket.close()
	os.remove('/var/tmp/dupllistner.pid')
	subprocess.call("/usr/bin/screen -dmS schakelaars python3 %s"%__file__, shell=True)