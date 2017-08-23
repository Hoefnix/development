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

jsonstring  =	'{'
jsonstring +=		'"bureau":0,'
jsonstring +=	'"ventilatie":0,'
jsonstring +=	    '"leanne":0'
jsonstring +=	'}'
schakelaars =	json.loads( jsonstring )

jsonstring  =	'{'
jsonstring += '"bijburtemp":0,'
jsonstring += '"bijburhumi":0,'
jsonstring += '"bijburlcht":0,'
jsonstring +=  '"geveltemp":0,'
jsonstring += '"leannetemp":0'
jsonstring +=	'}'
sensoren	=	json.loads( jsonstring )

thread = None # voor getstatus() thread


class octoprint():
	def __init__(self):
		self.hotend = 0
		self.bed = 0
		self.operational = False
		self.printing = 0		
		self.apikey = {'X-Api-Key': '5A56D03925A2480EA68D6B40AAAC0B17'}
		self.interval = randint(275,325)
		self.resultaat = None
		self.percentage = 0
		
		self.check()
		
	def check(self):
		self.thread = threading.Timer(self.interval, self.check)
		self.thread.start()

		self.hotend = 0
		self.bed = 0
		self.operational = False
		self.printing = 0
		self.percentage = 0

		self.resultaat = requests.get('http://192.168.178.125:5000/api/printer', headers=self.apikey)
		bericht("octoprint (printer) %s"%(self.resultaat.text))
		if "not operational" not in self.resultaat.text:
			self.bed = float(self.resultaat.json()["temperature"]["bed"]["actual"])
			self.hotend = int(float(self.resultaat.json()["temperature"]["tool0"]["actual"])/10)
			self.operational = self.resultaat.json()["state"]["flags"]["operational"]
			self.printing = "1" if self.resultaat.json()["state"]["flags"]["printing"] else "0"
		
			self.resultaat = requests.get('http://192.168.178.125:5000/api/job', headers=self.apikey)
			bericht("%s\n"%int(float(self.resultaat.json()["progress"]["completion"])))
			self.percentage = int(float(self.resultaat.json()["progress"]["completion"]))
				
	def stop(self):
		bericht("Octoprint wordt gestopt...")
		self.thread.cancel()

	
def thingspeak(veld="field6",waarde=None, omschrijving = ""):
	bericht("Thingspeak update %s, %s = %s"%(omschrijving, veld, waarde))

	if not waarde is None:
		httpGet("https://api.thingspeak.com/update?key=0Y0TM8Y14DTM54P1&%s=%s"%(veld, waarde))
		
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
        
def weerbericht():
	resultaat = httpGet("http://api.openweathermap.org/data/2.5/weather?q=capelle%20aan%20den%20ijssel,nl&units=metric&lang=nl&APPID=2799a7fec820a086d91e60e3b48fac5a")

	berichtje("Het weer nu %s %s"%(weather["main"], weather["description"]) )
	
#	{"coord":{"lon":139,"lat":35},
#	 "sys":{"country":"JP","sunrise":1369769524,"sunset":1369821049},
#	 "weather":[{"id":804,"main":"clouds","description":"overcast clouds","icon":"04n"}],
#	 "main":{"temp":289.5,"humidity":89,"pressure":1013,"temp_min":287.04,"temp_max":292.04},
#	 "wind":{"speed":7.31,"deg":187.002},
#	 "rain":{"3h":0},
#	 "clouds":{"all":92},
#	 "dt":1369824698,
#	 "id":1851632,
#	 "name":"Shuzenji",
#	 "cod":200}

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

class aanuit(object):
	#	url moet 'kale'url zijn waarvoor geldt:
	#	- zonder toevoegingen de status van wordt teruggeven, laatste character resultaatstring is 0 of 1
	#	- schakelt met additionele "=aan" of "=uit"
	
	def __init__(self, url):
		self.aanuit = 0
		self.deviceurl = url
		self.interval = randint(275,325)		
		self.check()
		bericht("Object (%s) is gereed, waarde is %s"%(self.deviceurl, self.aanuit))
			
	def schakel(self, aanofuit):
		if aanofuit == "flp":
			aanofuit = "uit" if self.aanuit == 1 else "aan"
			
		if (self.aanuit == 1 and aanofuit == "uit") or (self.aanuit == 0 and aanofuit == "aan"):
			bericht("%s=%s"%(self.deviceurl,aanofuit))
			resultaat = httpGet("%s=%s"%(self.deviceurl,aanofuit))
			if (resultaat.status_code == requests.codes.ok):
				self.aanuit = int(resultaat.text[-1:])
		return self.aanuit

	def check(self):
		self.thread = threading.Timer(self.interval, self.check)
		self.thread.start()
		
		resultaat = httpGet("%s"%self.deviceurl)
		if (resultaat.status_code == requests.codes.ok):
			self.aanuit = int(resultaat.text[-1:])
		return self.aanuit

	def stop(self):
		bericht("%s check wordt gestopt..."%self.deviceurl)
		self.thread.cancel()

class Tuinhuis(object):
	def __init__(self):
		self.temperatuur = 0
		self.aanuit = 0
		self.deur = 0
		self.interval = randint(275,325)
		self.check()

	def schakel(self, aanofuit):
		resultaat = httpGet("http://192.168.178.70:1208?schakelaar:%s"%aanofuit, 4, "Tuinhuis: ")
		if (resultaat.status_code == requests.codes.ok):
			self.aanuit = resultaat.json()["schakelaar"]	
		return self.aanuit
		
	def check(self):
		self.thread = threading.Timer(self.interval, self.check)
		self.thread.start()
		
		resultaat = httpGet("http://192.168.178.70:1208", 4, "Tuinhuis: ")
		if (resultaat.status_code == requests.codes.ok):
			self.aanuit = resultaat.json()["schakelaar"]
			self.deur 	= resultaat.json()["deur"]			
			if not int(resultaat.json()["temperatuur"]) is int(self.temperatuur):
				self.temperatuur = resultaat.json()["temperatuur"]
				if self.temperatuur > -127:
					thingspeak("field6", self.temperatuur, "temperatuur tuinhuis")					
		httpGet("http://127.0.0.1:51828/?accessoryId=schuurdeur&state=%s"%("true" if self.deur == 0 else "false"))

		resultaat = httpGet("http://192.168.178.70:1208?temperatuur", 4, "Tuinhuis: ")
		if (resultaat.status_code == requests.codes.ok):
			self.temperatuur = resultaat.json()["temperatuur"]
			if self.temperatuur > -127:
				thingspeak("field6", self.temperatuur, "temperatuur tuinhuis")					
		
		return self.aanuit
		
	def stop(self):
		bericht("Tuinhuis check wordt gestopt...")
		self.thread.cancel()

class woonveilig(object):
	def __init__(self):
		self.ip		= "192.168.178.3"
		self.user	= "admin"
		self.pwrd	= "admin1234"
		self.status = 3
		self.interval = randint(275,325)
		self.check()

	def instellen(self, mode):
		aanofuit = 2 if mode == "disarm" else 1 if mode == "armhome" else 0  
		bericht("%s aanofuit wordt: %s"%(mode, aanofuit))
		try:
			resultaat = requests.get('http://%s/action/panelCondPost?mode=%s'%(self.ip, aanofuit), auth=HTTPBasicAuth(self.user, self.pwrd), timeout=2)
		except requests.Timeout as e:
			bericht("Woonveilig - %s: url=%s, timeout=%s"%(e, httpCall, wachten))
			return self.status
		except:
			bericht("Woonveilig - Fout: url=%s, timeout=%s"%(httpCall,wachten))
			return self.status
				
		if (resultaat.status_code == requests.codes.ok):
			bericht("Alarm ingesteld\n%s"%resultaat.text)
		else:
			bericht("Alarm NIET ingesteld\n%s"%resultaat.text)
		return self.check()

	def check(self):
		self.thread = threading.Timer(self.interval, self.check)
		self.thread.start()
		
		#	Opvragen instelling
		try:
			resultaat = requests.get("http://%s/action/panelCondGet"%self.ip, auth=HTTPBasicAuth(self.user, self.pwrd), timeout=2)
		except requests.Timeout as e:
			bericht("Woonveilig - %s"%e)
			return self.status
		except:
			bericht("Woonveilig - Fout" )
			return self.status

		if (resultaat.status_code == requests.codes.ok):
			if    "Disarm" in resultaat.text:
				self.status = 3
			elif "Armhome" in resultaat.text:
				self.status = 0
			elif     "Arm" in resultaat.text:
				self.status = 1
		bericht("Status alarmsysteem is %s"%self.status)
		return self.status

	def stop(self):
		bericht("Woonveilig check wordt gestopt...")
		self.thread.cancel()

class Woonkamer(object):
	def __init__(self):
		self.temperatuur = 0
		self.staandelamp = 0
		self.ledstrip = 0
		self.aanuit = 0
		self.lichtaan = zononder()-5400
		self.lichtuit = self.uittijd()
		
	def uittijd(self):
		
		today = datetime.date.today() # wanneer is het
		# hoeveel seconden zijn er al verstreken vandaag
		seconds_since_midnight = time.time() - time.mktime(today.timetuple())
		# hoeveel zijn er nog over... 24x60x60 seconden in een dag minus 
		seconden_tot_middernacht = 86400 - seconds_since_midnight 
		# tel er not wat seconden er bij
		return time.time() + seconden_tot_middernacht + randint(900,2700)
			
	def schakel(self, aanofuit):
		if aanofuit == "flp":
			aanofuit = "uit" if self.aanuit == 1 else "aan"

		while (self.aanuit == 1 and aanofuit == "uit") or (self.aanuit == 0 and aanofuit == "aan"):		
			resultaat = httpGet("http://192.168.178.201?%s"%aanofuit, 1)
			if (resultaat.status_code == requests.codes.ok):
				self.staandelamp	= 1 if resultaat.text == "aan" else 0
				bericht("staandelamp %s"%resultaat.text)
			
			resultaat = httpGet("http://192.168.178.204/aanuit=%s"%aanofuit, 1)
			if (resultaat.status_code == requests.codes.ok):
				self.ledstrip	= int(json.loads( resultaat.text )["aanuit"])
				bericht("LED strip %s"%self.ledstrip)
			
			resultaat = httpGet("http://192.168.178.208?gpio2=%s"%aanofuit, 1)
			if (resultaat.status_code == requests.codes.ok):
				self.aanuit = int(resultaat.text)
				
			self.aanuit = self.aanuit * self.ledstrip * self.staandelamp
		return self.aanuit
		
	def automatisch(self):
		if time.time() > self.lichtaan:
			if keuken.licht < 90 and self.aanuit == 0:
				if self.schakel("aan"):
					bericht("Woonkamerlicht automatisch aan (%s)"%keuken.licht, viaPushover = True)
		elif time.time() > self.lichtuit:
		#	alleen als we niet thuis zijn (alarmsysteem staat aan) dan moet licht automatisch uit
			if alarmsysteem.status != 3 and self.aanuit == 1:	
				if not self.schakel("uit"):
					bericht("Woonkamerlicht automatisch uitgedaan", viaPushover = True)

		if	time.time() > self.lichtaan:
		#	is het licht al aan, kan nog aan het wachten zijn op voldoende donker
			if self.aanuit == 1:		
				self.lichtaan = zononder()-3600
		elif time.time() > self.lichtuit:
		#	is het licht al uit, zoniet nog even laten anders gaat het nooit uit
			if self.aanuit == 0:		
				self.lichtuit = self.uittijd()

	def check(self):

		#	Staande lamp
		resultaat = httpGet("http://192.168.178.201/?status")
		if (resultaat.status_code == requests.codes.ok):
			self.staandelamp = int(resultaat.text[-1])

		#	Led strip
		resultaat = httpGet("http://192.168.178.204")
		if (resultaat.status_code == requests.codes.ok):
			self.ledstrip = int(json.loads( resultaat.text )["aanuit"])

		#	Schemerlamp
		resultaat = httpGet("http://192.168.178.208/gpio2")
		if (resultaat.status_code == requests.codes.ok):
			self.aanuit = int(resultaat.text)
			
		#	Temperatuur
		resultaat = httpGet("http://192.168.178.201/?temperatuur")
		if (resultaat.status_code == requests.codes.ok):
			self.temperatuur = resultaat.text		

		self.aanuit = self.aanuit * self.ledstrip * self.staandelamp

		return self.aanuit

class Keuken(object):
	def __init__(self):
		self.deur = 0
		self.verlichting = 0
		self.stopcontact = 0
		self.licht = 0
		self.interval = randint(275,325)
		self.check()
			
	def lampen(self, aanofuit):
		if aanofuit == "flp":
			aanofuit = "uit" if self.verlichting == 1 else "aan" 
		felheid = "000" if aanofuit == "uit" else "099"

		resultaat = httpGet("http://192.168.178.100/broadcast.php?port=1208\&dimmer=@%s"%felheid)
		resultaat = httpGet("http://192.168.178.203/%s:1"%aanofuit)	
		if (resultaat.status_code == requests.codes.ok):
			if not empty(resultaat.text):
				self.verlichting = int(resultaat.json()["aanuit1"])
		return self.verlichting

	def schakelaar(self, aanofuit):
		if aanofuit == "flp":
			aanofuit = "uit" if self.stopcontact == 1 else "aan" 
		resultaat = httpGet("http://192.168.178.203/%s:2"%aanofuit)	
		if (resultaat.status_code == requests.codes.ok):
			if not empty(resultaat.text):
				self.stopcontact = int(resultaat.json()["aanuit2"])
		return self.stopcontact
		
	def opendicht(self, opendicht):
		bericht("keukendeur is %s wordt %s"%(self.deur, opendicht))
		if opendicht == 0 or opendicht == 1:
			self.deur = opendicht
#		update de webhook module
		httpGet("http://127.0.0.1:51828/?accessoryId=achterdeur&state=%s"%("true" if self.deur == 0 else "false"))

	def check(self):
		self.thread = threading.Timer(self.interval, self.check)
		self.thread.start()
		
		resultaat = httpGet("http://192.168.178.203")
		if (resultaat.status_code == requests.codes.ok):
			if not empty(resultaat.text):
				self.verlichting	= int(resultaat.json()["aanuit1"])
				self.stopcontact	= int(resultaat.json()["aanuit2"])
				self.opendicht(int(resultaat.json()["keukendeur"]))			
				bericht("keukendeur is %s"%self.deur)
		'''
		resultaat = httpGet("http://192.168.178.50/lichtsterkte.json")
		if (resultaat.status_code == requests.codes.ok):
			if not empty(resultaat.text):
				if not int(resultaat.json()["licht"]) is self.licht:
					self.licht = int(resultaat.json()["licht"])
					thingspeak("field1", self.licht)		
		'''		
		resultaat = httpGet("http://192.168.178.34:1964?lichtsterkte")
		if (resultaat.status_code == requests.codes.ok):
			if not empty(resultaat.text):
				if not int(resultaat.json()["licht"]) is self.licht:
					self.licht = int(resultaat.json()["licht"])
					thingspeak("field1", self.licht, "lichtsterkte")			
		return
		
	def stop(self):
		bericht("Keukencheck wordt gestopt...")
		self.thread.cancel()
				
class Badkamer(object):
	def __init__(self):
		self.temperatuur = 0
		self.luchtvochtigheid = 0
		self.drempelwaarde = 0
		self.interval = randint(275,325)
		self.check()
			
	def drempelwaarde(self, waarde):
		return self.drempelwaarde

	def check(self):
		self.thread = threading.Timer(self.interval, self.check)
		self.thread.start()
	
		resultaat = httpGet("http://192.168.178.24/status", label="Badkamer: ")
		if (resultaat.status_code == requests.codes.ok):
#			{"naam":"badkamer","temperatuur":22.00,"luchtvochtigheid":41.00,"drempelwaarde":51}
			try:
				self.temperatuur		 = waarde(resultaat.json()["temperatuur"])
				self.luchtvochtigheid = waarde(resultaat.json()["luchtvochtigheid"])
				self.drempelwaarde	 = waarde(resultaat.json()["drempelwaarde"])
			
				bericht("Badkamer: %s, %s\% (%s\%)"%(self.temperatuur,self.luchtvochtigheid,self.drempelwaarde))
			except:
				pass
		return
		
	def stop(self):
		bericht("%s wordt gestopt..."%self.__class__.__name__.capitalize())
		self.thread.cancel()

def getstatus():
	global schakelaars, sensoren, thread
	
	thread = threading.Timer(randint(275,325), getstatus)
	thread.start()

	woonkamer.check()

	#	Bureau
	resultaat = httpGet("http://192.168.178.210/status")
	if (resultaat.status_code == requests.codes.ok):
		if not empty(resultaat.text):
			schakelaars["bureau"] = int(resultaat.text[-1:])

	#	Ventilatie
	resultaat = httpGet("http://192.168.178.205/status")
	if (resultaat.status_code == requests.codes.ok):
		schakelaars["ventilatie"] = resultaat.text
			
	#	Sensoren bij bureau
	resultaat = httpGet("http://192.168.178.202?metingen")
	if (resultaat.status_code == requests.codes.ok):
	#	{ "temperatuur":"24","luchtvochtigheid":"19","lichtsterkte":"181","buiten":"16.9375"}
		if not empty(resultaat.text):
			sensoren["bijburtemp"] = resultaat.json()["temperatuur"]
			sensoren["bijburhumi"] = resultaat.json()["luchtvochtigheid"]
			sensoren["bijburlcht"] = resultaat.json()["lichtsterkte"]
			sensoren[ "geveltemp"] = 0 if empty(resultaat.json()["buiten"]) else resultaat.json()["buiten"]
		else:
			bericht("Response sensoren bij bureau (192.168.178.202) is leeg")

	woonkamer.automatisch()
	
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
		
#		Aan, Uit, Toggle /?onderwerp:[aan/uit]
#		Homebridge.Httpeverything verwacht een json {"value":<waarde>}

		if "status" == command:
			self.respond("Status wordt bijgewerkt")
			threading.Thread(target=getstatus).start()
			# getstatus()
			
		elif "getpid" == command:
			self.respond( "%s"%os.getpid() )
			
		elif command.startswith("keukendeur"):
			if command.endswith(("open","dicht")):
				keuken.opendicht(1 if command.endswith("open") else 0)
			self.respond( "{\"value\":%s}"%keuken.deur)
			
		elif command.startswith("achterdeur"):
			self.respond( "%s"%keuken.deur )
			
		elif command.startswith("lux"):
			self.respond( "{\"lightlevel\":%s}"%(keuken.licht*10) )
			
		elif command.startswith("schuurdeur"):
			if command.endswith(("open","dicht")):
				tuinhuis.deur = 1 if command.endswith("open") else 0
			self.respond( "{\"value\":%s}"%tuinhuis.deur )
			
		elif command.startswith("keukenverlichting"):
			if command.endswith(("aan","uit","flp")):
				keuken.lampen(command[-3:])
			self.respond( "%s"%keuken.verlichting )

		elif command.startswith("stopcontact"):
			if command.endswith(("aan","uit","flp")):
				keuken.schakelaar(command[-3:])
			self.respond("%s"%keuken.stopcontact)

		elif command.startswith("ventilatie"):
			if command.endswith(("aan","uit")):
				resultaat = httpGet("http://192.168.178.205?%s"%command[-3:])
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["ventilatie"] = resultaat.text
			self.respond("%s"%schakelaars["ventilatie"])
											
		elif command.startswith("woonkamer"):
			if	command.endswith("temperatuur"):
				self.respond("{\"temperature\":%s}"%(woonkamer.temperatuur) )
			else:
				if command.endswith(("aan","uit","flp")):
					woonkamer.schakel(command[-3:])
				self.respond("%s"%woonkamer.aanuit)
			
		elif command.startswith("bureaulamp"):
			if command.endswith(("aan","uit","flp")):
				bureaulamp.schakel(command[-3:]) 
			self.respond("%s"%bureaulamp.aanuit)
			
		elif command.startswith("gevellamp"):
			if	command.endswith(("aan","uit","flp")):
				gevellamp.schakel(command[-3:]) 
			self.respond("%s"%gevellamp.aanuit)

		elif command.startswith("tuinhuis"):
			if command.endswith("temperatuur"):
				self.respond("{\"temperature\":%s}"%tuinhuis.temperatuur)
			elif command.endswith(("aan","uit","flp")):
				self.respond("%s"%tuinhuis.schakel(command[-3:]))
			elif command.endswith("lamp"):
				self.respond("%s"%tuinhuis.aanuit)
			elif command.startswith("tuinhuisupdate"):
				tuinhuis.temperatuur = float(command[command.find(":")+1:])
				self.respond("{\"temperature\":%s}"%tuinhuis.temperatuur)
				
		elif command.startswith("schuurtemperatuur"):
			if "schuurtemperatuur" != command:
				tuinhuis.temperatuur = float(command[command.find(":")+1:])
			self.respond("%s"%tuinhuis.temperatuur)
				
		elif command.startswith("badkamer"):
			if command.endswith("temphum"):
				self.respond( "{\"temperature\":%s,\"humidity\":%s}"%(badkamer.temperatuur, badkamer.luchtvochtigheid))

		elif command.startswith("bijbureau"):
			if command.endswith("temphum"):
				self.respond("{\"temperature\":%s,\"humidity\":%s}"%(sensoren["bijburtemp"],sensoren["bijburhumi"]))
			elif command.endswith("licht"):
				self.respond("{\"value\": %s}"%sensoren["bijburlcht"])
			elif command.endswith("status"):
				self.respond("{\"temperatuur\":%s,\"luchtvochtigheid\":%s,\"buiten\":%s,\"lichtsterkte\":%s}"%(sensoren["bijburtemp"],sensoren["bijburhumi"],sensoren["geveltemp"],sensoren["bijburlcht"]))

		elif command.startswith("gevel"):
			if	command.endswith("temperatuur"):
				self.respond( "{\"temperature\":%s}"%(sensoren["geveltemp"]) )

		elif command.startswith("leanne"):
			if	command.endswith("temperatuur"):
				self.respond( "{\"temperature\":%s}"%(sensoren["leannetemp"]) )
			elif command.endswith(("aan","uit","flp")):
				aanofuit = command[-3:]
				if command.endswith("flp"):
					aanofuit = "uit" if schakelaars["leanne"] == 1 else "aan"
				resultaat = httpGet("http://192.168.178.211?%s"%aanofuit)
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["leanne"] = 1 if "aan" in resultaat.text else 0
				self.respond( "{\"value\":%s}"%(schakelaars["leanne"]))			
			else:	
				self.respond( "{\"value\":%s}"%(schakelaars["leanne"]) )

		elif command.startswith("bureau"):
			aanofuit = ""
			if command.endswith(("piraan","piruit")):
				aanofuit = command[-3:]
			elif command.endswith(("aan","uit")):
				aanofuit = command[-3:]
			elif command.endswith("flp"):
				aanofuit = "uit" if schakelaars["bureau"] == 1 else "aan"
				
			# als aan/uit dan niet nog eens aan/uitzetten	
			if (aanofuit == "aan" and schakelaars["bureau"] == 0) or (aanofuit == "uit" and schakelaars["bureau"] == 1):
				bericht("Bureau gaat %s"%aanofuit)
				resultaat = httpGet("http://192.168.178.210?%s"%aanofuit)
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["bureau"] = 1 if "aan" in resultaat.text else 0
			self.respond("%s"%schakelaars["bureau"] )
			
		elif command.startswith("alarmsysteem"):
			if	command.endswith(("arm","disarm","armhome")):
				alarmsysteem.instellen(command.replace("alarmsysteem:", ""))
			self.respond("%s"%alarmsysteem.status)
			
		elif command.startswith("duplicator"):
			#if command.endswith(("aan","uit","flp")):
				#duplicator.schakel(command[-3:]) 
			#self.respond("%s"%duplicator.aanuit)
			self.respond("0")
			
		elif command.startswith("duplilicht"):
			#if command.endswith(("aan","uit","flp")):
				#duplilicht.schakel(command[-3:]) 
			#self.respond("%s"%duplilicht.aanuit)
			self.respond("0")

		elif command.startswith("octoprint"):
			if command.endswith("bed"):
				self.respond( "{\"temperature\":%s}"%duplicator.bed )
			elif command.endswith("hotend"):
				self.respond("{\"temperature\":%s,\"humidity\":%s}"%(duplicator.hotend,duplicator.percentage) )
			elif command.endswith("printing"):
				self.respond( duplicator.printing )
			elif command.endswith("operational"):
				self.respond("%s"%duplicator.operational)
			elif command.endswith(("aan","uit","flp")):
				if not duplicator.printing:
					self.respond("printer wordt %s gezet"%command[-3:])
				else:
					self.respond("printer is bezig")
			else:
				self.respond("gebruik [bed|hotend|printing|operational|aan|uit|flp]")
			
		else:
			bericht( "Opdracht niet begrepen: %s"%command)				
			self.respond("Opdracht niet begrepen: %s"%command)				
		return
		
def httpGet( httpCall, wachten = 4, label=""):
	bericht( "\033[33mhttpGet: %s"%httpCall )
	resultaat = requests.Response
	try:
		resultaat = requests.get(httpCall, timeout=wachten)
	except requests.Timeout as e:
		bericht("%s\033[31m%s: url=%s, timeout=%s"%(label, e, httpCall, wachten))
		resultaat.status_code = 999
	except:
		bericht("%s\033[31mFout: url=%s, timeout=%s"%(label,httpCall,wachten))
		resultaat.status_code = 999
	return resultaat
			
try:
#	Create a web server and define the handler to manage the incoming request
	bericht ("Initialisatie...\n" )

	gevellamp	 = aanuit("http://192.168.178.208?gpio0")
	bureaulamp	 = aanuit("http://192.168.178.34:1964?bureaulamp")
	badkamer		 = Badkamer()
	alarmsysteem = woonveilig()
	duplicator	 = octoprint()
	woonkamer 	 = Woonkamer()
	keuken		 = Keuken()
	tuinhuis		 = Tuinhuis()
	
	getstatus()
	
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	with open('/var/tmp/httplistner.pid', 'w') as myfile:
		data = myfile.write( '{"pid":%s}'%os.getpid() )
	bericht("Actief op poort %d"%PORT_NUMBER, viaPushover = True)
	
	server.serve_forever() # Wait forever for incoming http requests

except KeyboardInterrupt:
	bericht("ctrl-c ontvangen, webserver wordt opnieuw gestart", viaPushover = True)
	server.socket.close()
	thread.cancel()
	
	gevellamp.stop()
	bureaulamp.stop()
	keuken.stop()
	tuinhuis.stop()
	alarmsysteem.stop()
	duplicator.stop()
	badkamer.stop()
	
	os.remove('/var/tmp/httplistner.pid')
	subprocess.call("/usr/bin/screen -dmS schakelaars python3 /opt/development/httplistner.py", shell=True)