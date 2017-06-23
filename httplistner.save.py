#!/usr/bin/python
import requests
from requests.auth import HTTPBasicAuth
#from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import time

PORT_NUMBER = 1208

woonveilig_ip = "192.168.178.3"
woonveilig_us = "admin"
woonveilig_pw = "admin1234"

jsonstring  = '{'
jsonstring += '"keukenverlichting":0,'
jsonstring += '"woonkamer":0,'
jsonstring += '"bureau":0,'
jsonstring += '"bureaulamp":0,'
jsonstring += '"stopcontact":0,'
jsonstring += '"ventilatie":0,'
jsonstring += '"alarmsysteem":3,'
jsonstring += '"keukendeur":0,'
jsonstring += '"schuurdeur":0,'
jsonstring += '"schuuraanuit":0,'
jsonstring += '"gevellamp":0'
jsonstring += '}'
schakelaars =	json.loads( jsonstring )

jsonstring  = '{'
jsonstring += '"schuurtemperatuur":0,'
jsonstring += '"badkmrtmp":0,'
jsonstring += '"badkmrlvh":0,'
jsonstring += '"badkmrdpl":0,'
jsonstring += '"bijburtemp":0,'
jsonstring += '"bijburhumi":0,'
jsonstring += '"bijburlcht":0,'
jsonstring += '"wnkamrtemp":0,'
jsonstring += '"geveltemp":0'
jsonstring += '}'
sensoren	=	json.loads( jsonstring )

def telegram(message="...", chat_id="12463680"):
#	Johannes_Smits	=  "12463680"
#	alarmsysteem	= "-24143102"
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage?chat_id=%s&text=%s" % (chat_id, message), timeout=5)
	return r.status_code
	
class bureaulampinit( object ):
	def __init__(self):
		self.status = 0
			
	def schakel(self, aanofuit):
		if aanofuit == "flp":
			aanofuit = "uit" if self.status == 1 else "aan" 
		try:
			resultaat = requests.get("http://192.168.178.202?gpio04=%s"%aanofuit, timeout=2)
			if (resultaat.status_code == requests.codes.ok):
				self.status = int(resultaat.text[-1])
		except requests.Timeout:
			print("bureaulamp timed out")
		return self.status

	def check(self):
		try:
			resultaat = requests.get("http://192.168.178.202?gpio04", timeout=2)
			if (resultaat.status_code == requests.codes.ok):
				self.status = int(resultaat.text[-1])
		except requests.Timeout:
			print("bureaulamp timed out")
		return self.status
	
def getstatus():
	global schakelaars, sensoren
	
	# tuinhuis
	try:
		resultaat = requests.get("http://192.168.178.13/status", timeout=2)
		if (resultaat.status_code == requests.codes.ok):
			sensoren["schuurtemperatuur"] = json.loads( resultaat.text )["temperatuur"]
			schakelaars["schuuraanuit"] = json.loads( resultaat.text )["aanuit"]
			schakelaars["schuurdeur"] = json.loads( resultaat.text )["deur"]
	except requests.Timeout:
		print("Tuinhuis timed out")
	
	# keuken
	try:
		resultaat = requests.get("http://192.168.178.203", timeout=2)
		if (resultaat.status_code == requests.codes.ok):
			schakelaars["keukenverlichting"] = json.loads( resultaat.text )["aanuit1"]
			schakelaars["stopcontact"] = json.loads( resultaat.text )["aanuit2"]
			schakelaars["keukendeur"] = json.loads( resultaat.text )["keukendeur"]
	except requests.Timeout:
		print("Keuken timed out")
				
	# woonkamer
	try:
		resultaat = requests.get("http://192.168.178.208?gpio2", timeout=2)
		if (resultaat.status_code == requests.codes.ok):
			schakelaars["woonkamer"] = json.loads( resultaat.text )
	except requests.Timeout:
		print("Woonkamer timed out")
		
	# bureau
	try:
		resultaat = requests.get("http://192.168.178.210", timeout=2)
		if (resultaat.status_code == requests.codes.ok):
			if "aan" in resultaat.text:
				schakelaars["bureau"] = 1
			elif "uit" in resultaat.text:
				schakelaars["bureau"] = 0
	except requests.Timeout:
		print("Bureau timed out")
			
	schakelaars["bureaulamp"] = bureaulamp.check()

#	bureaulamp
#	try:
#		resultaat = requests.get("http://192.168.178.202?gpio04", timeout=2)
#		if (resultaat.status_code == requests.codes.ok):
#			schakelaars["bureaulamp"] = resultaat.text[-1]
#	except requests.Timeout:
#		print("Bureaulamp timed out")
		
	# ventilatie
	try:
		resultaat = requests.get("http://192.168.178.205/status", timeout=2)
		if (resultaat.status_code == requests.codes.ok):
			schakelaars["ventilatie"] = resultaat.text
	except requests.Timeout:
		print("Ventilatie timed out")
		
	# badkamer
	try:
		resultaat = requests.get("http://192.168.178.17/status", timeout=2)
		if (resultaat.status_code == requests.codes.ok):
			sensoren["badkmrtmp"] = resultaat.json()["temperatuur"]
			sensoren["badkmrlvh"] = resultaat.json()["luchtvochtigheid"]
			sensoren["badkmrdpl"] = resultaat.json()["drempelwaarde"]
	except requests.Timeout:
		print("Badkamer timed out")
		
	# badkamer
	try:
		resultaat = requests.get("http://192.168.178.201/?temperatuur", timeout=2)
		if (resultaat.status_code == requests.codes.ok):
			sensoren["wnkamrtemp"] = resultaat.text
	except requests.Timeout:
		print("Woonkamertemperatuur timed out")
		
	# alarmsysteem
	try:
		resultaat = requests.get("http://%s/action/panelCondGet"%woonveilig_ip, auth=HTTPBasicAuth(woonveilig_us, woonveilig_pw), timeout=2)
		if (resultaat.status_code == requests.codes.ok):
			if	resultaat.text.find("Disarm"):
				schakelaars["alarmsysteem"] = 3
			elif resultaat.text.find("Armhome"):
				schakelaars["alarmsysteem"] = 0
			elif resultaat.text.find("Arm"):
				schakelaars["alarmsysteem"] = 1
	except requests.Timeout:
		print("Woonveilig timed out")
	#sensoren bij bureau
	try:
		resultaat = requests.get("http://192.168.178.202?metingen", timeout=2)
		if (resultaat.status_code == requests.codes.ok):
			sensoren["bijburtemp"] = resultaat.json()["temperatuur"]
			sensoren["bijburhumi"] = resultaat.json()["luchtvochtigheid"]
			sensoren["bijburlcht"] = resultaat.json()["lichtsterkte"]
			sensoren["geveltemp"] = resultaat.json()["buiten"]
	except requests.Timeout:
		print("Bij bureau timed out")
			
	status = "\033[3m%s\033[0m - "%time.strftime("%H:%M:%S")
	for item in schakelaars:
		status += "%s(%s) "%(item,schakelaars[item])
	for item in sensoren:
		status += "%s(%s) "%(item,sensoren[item])
	print (status)
	return 
	
#This class will handles any incoming request from
#the browser 
class myHandler(BaseHTTPRequestHandler):
	
	#Handler for the GET requests
	def log_message(self, format, *args):
		return
		
	#Handler for the GET requests
	def do_GET(self):
		global schakelaars
		
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		
		command = self.requestline.replace("GET /","").replace("?","")
		command = command[:command.find("HTTP")].strip()
		# opdracht = command.split("&")

		# aan, uit, toggle /?onderwerp:[aan/uit]
		aanofuit = ""
		if "status" == command:
			getstatus()
						
		elif command.startswith("keukendeur"):
			if command.endswith("open"):
				schakelaars["keukendeur"] = 1
			elif command.endswith("dicht"):
				schakelaars["keukendeur"] = 0
#			homebridge.Httpeverything verwacht een json {"value":<waarde>}
			self.wfile.write( bytes( "{\"value\":%s}"%schakelaars["keukendeur"], "utf-8"))
			
		elif command.startswith("schuurdeur"):
			if command.endswith("open"):
				schakelaars["schuurdeur"] = 1
			elif command.endswith("dicht"):
				schakelaars["schuurdeur"] = 0
#			homebridge.Httpeverything verwacht een json {"value":<waarde>}																							
			self.wfile.write(bytes("{\"value\":%s}"%schakelaars["schuurdeur"] , "utf-8"))
			
		elif command.startswith("keukenverlichting"):
			if	command.endswith("aan"):
				requests.get("http://192.168.178.100/broadcast.php?port=1208\&dimmer=@099", timeout=2)
				resultaat = requests.get("http://192.168.178.203/aan:1", timeout=2)
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["keukenverlichting"] = json.loads( resultaat.text )["aanuit1"]
			elif command.endswith("uit"):
				requests.get("http://192.168.178.100/broadcast.php?port=1208\&dimmer=@000", timeout=2)
				resultaat = requests.get("http://192.168.178.203/uit:1", timeout=2)
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["keukenverlichting"] = json.loads( resultaat.text )["aanuit1"]
			self.wfile.write(bytes("%s"%schakelaars["keukenverlichting"], "utf-8"))

		elif command.startswith("stopcontact"):
			if command.endswith(("aan","uit")):
				resultaat = requests.get("http://192.168.178.203/%s:2"%command[-3:], timeout=2)
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["stopcontact"] = json.loads( resultaat.text )["aanuit2"]
			self.wfile.write(bytes("%s"%schakelaars["stopcontact"], "utf-8"))

		elif command.startswith("ventilatie"):
			if command.endswith(("aan","uit")):
				resultaat = requests.get("http://192.168.178.205?%s"%command[-3:], timeout=2)
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["ventilatie"] = resultaat.text
			self.wfile.write( bytes("%s"%schakelaars["ventilatie"], "utf-8"))
											
		elif command.startswith("woonkamer"):
			if	command.endswith("temperatuur"):
				self.wfile.write(bytes("{\"temperature\":%s}"%(sensoren["wnkamrtemp"]), "utf-8") )
			else:
				if command.endswith(("aan","uit")):
					requests.get("http://192.168.178.201?%s"%command[-3:], timeout=1)
					requests.get("http://192.168.178.204/aanuit=%s"%command[-3:], timeout=1)
					resultaat = requests.get("http://192.168.178.208?gpio2=%s"%command[-3:], timeout=1)
					if (resultaat.status_code == requests.codes.ok):
						schakelaars["woonkamer"] = json.loads( resultaat.text )
				self.wfile.write(bytes("%s"%schakelaars["woonkamer"], "utf-8"))
			
		elif command.startswith("bureaulamp"):
			if command.endswith(("aan","uit","flp")):
				bureaulamp.schakel(command[-3:]) 
			self.wfile.write(bytes("%s"%bureaulamp.status, "utf-8"))

		elif command.startswith("bureaulamp"):
			if	command.endswith(("aan","uit")):
				resultaat = requests.get("http://192.168.178.202?gpio04=%s"%command[-3:], timeout=2)
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["bureaulamp"] = resultaat.text[-1]
			self.wfile.write( bytes("%s"%schakelaars["bureaulamp"], "utf-8") )
			
		elif command.startswith("gevellamp"):
			if	command.endswith(("aan","uit")):
				resultaat = requests.get("http://192.168.178.208?gpio0=%s"%command[-3:], timeout=2)
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["gevellamp"] = resultaat.text[-1]
			self.wfile.write(bytes("%s"%schakelaars["gevellamp"], "utf-8"))

		elif command.startswith("tuinhuis"):
			if	command.endswith("temperatuur"):
				self.wfile.write(bytes("{\"temperature\":%s}"%(sensoren["schuurtemperatuur"]),"utf-8"))

			elif command.endswith(("aan","uit")):
				resultaat = requests.get("http://192.168.178.13/%s"%command[-3:], timeout=3)
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["schuuraanuit"] = json.loads(resultaat.text)["aanuit"]
				self.wfile.write(bytes("%s"%schakelaars["schuuraanuit"], "utf-8"))

			elif command.endswith("lamp"):
				self.wfile.write(bytes("%s"%schakelaars["schuuraanuit"], "utf-8"))
			
		elif command.startswith("schuurtemperatuur"):
			if "schuurtemperatuur" != command:
				sensoren["schuurtemperatuur"] = float(command[command.find(":")+1:])
			self.wfile.write(bytes("%s"%sensoren["schuurtemperatuur"], "utf-8"))
			
		elif command.startswith("woonkamer"):
			if	command.endswith("temperatuur"):
				self.wfile.write( bytes("{\"temperature\":%s}"%(sensoren["wnkamrtemp"]) , "utf-8"))
				
		elif command.startswith("badkamer"):
			if command.endswith("temphum"):
				self.wfile.write(bytes( "{\"temperature\":%s,\"humidity\":%s}"%(sensoren["badkmrtmp"],sensoren["badkmrlvh"]), "utf-8") )
			elif command.endswith("status"):
				self.wfile.write( bytes("{\"temperatuur\":%s,\"luchtvochtigheid\":%s,\"drempelwaarde\":%s}"%(sensoren["badkmrtmp"],sensoren["badkmrlvh"],sensoren["badkmrdpl"]), "utf-8") )

		elif command.startswith("bijbureau"):
			if command.endswith("temphum"):
				self.wfile.write( bytes("{\"temperature\":%s,\"humidity\":%s}"%(sensoren["bijburtemp"],sensoren["bijburhumi"]) , "utf-8"))
			elif command.endswith("licht"):
				self.wfile.write( bytes("{\"value\": %s}"%sensoren["bijburlcht"] , "utf-8"))
			elif command.endswith("status"):
				self.wfile.write( bytes("{\"temperatuur\":%s,\"luchtvochtigheid\":%s,\"buiten\":%s,\"lichtsterkte\":%s}"%(sensoren["bijburtemp"],sensoren["bijburhumi"],sensoren["geveltemp"],sensoren["bijburlcht"]) , "utf-8"))

		elif command.startswith("gevel"):
			if	command.endswith("temperatuur"):
				self.wfile.write(bytes( "{\"temperature\":%s}"%(sensoren["geveltemp"]), "utf-8") )

		elif command.startswith("bureau"):
			if	command.endswith(("aan","uit")):
				resultaat = requests.get("http://192.168.178.210?%s"%command[-3:], timeout=2)
				if (resultaat.status_code == requests.codes.ok):
					if "aan" in resultaat.text:
						schakelaars["bureau"] = 1
					elif "uit" in resultaat.text:
						schakelaars["bureau"] = 0

			elif	command.endswith("flip"):
				aanofuit = "uit" if schakelaars["bureau"] else "aan"
				resultaat = requests.get("http://192.168.178.210?%s"%aanofuit, timeout=2)
				if (resultaat.status_code == requests.codes.ok):
					schakelaars["bureau"] = 1 if "aan" in aanofuit else 0
	
			self.wfile.write( bytes("%s"%schakelaars["bureau"], "utf-8") )
			
		elif command.startswith("alarmsysteem"):
			if	command.endswith(("aan","uit")):
				aanofuit = 0 if command.endswith("aan") else 2
				# instellen systeem
				requests.get('http://%s/action/panelCondPost?mode=%s'%(woonveilig_ip, aanofuit), auth=HTTPBasicAuth(woonveilig_us, woonveilig_pw), timeout=2)
				# opvragen instelling
				resultaat = requests.get("http://%s/action/panelCondGet"%woonveilig_ip, auth=HTTPBasicAuth(woonveilig_us, woonveilig_pw), timeout=2)
				if (resultaat.status_code == requests.codes.ok):
					# print(resultaat.text)
					if	  "Disarm" in resultaat.text:
						schakelaars["alarmsysteem"] = 3
					elif "Armhome" in resultaat.text:
						schakelaars["alarmsysteem"] = 0
					elif	 "Arm" in resultaat.text:
						schakelaars["alarmsysteem"] = 1
						
				tekst = "uit" if "Disarm" in resultaat.text else "actief"
				telegram( "Alarmsysteem is %s"%tekst )

			self.wfile.write( bytes("%s"%schakelaars["alarmsysteem"],"utf-8" ))
		else:
			print( "Opdracht niet begrepen: %s"%command)				
			self.wfile.write( bytes("Opdracht niet begrepen: %s"%command, "utf-8"))				
		return
		
try:
	# Create a web server and define the handler to manage the incoming request
	bureaulamp = bureaulampinit()
	
	print ("Huidige status wordt opgehaald\n" )
	getstatus()
	print ("Huidige status geladen\n" )
	
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	print ("\033[3mHTTPserver gestart op poort %d\n\033[0m"%PORT_NUMBER)
	
	# Wait forever for incoming http requests
	server.serve_forever()

except KeyboardInterrupt:
	print ('^C received, shutting down the web server')
	server.socket.close()
	