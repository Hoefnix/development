#!/usr/bin/python
import requests
from requests.auth import HTTPBasicAuth
import json
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import socket
from urlparse import urlparse, parse_qs

PORT_NUMBER = 1209

woonveilig_ip = "192.168.178.3"
woonveilig_us = "admin"
woonveilig_pw = "admin1234"

jsonstring  = '{'
jsonstring += '"schaarlamp":0,'
jsonstring += '"rgbledstrip":0,'
jsonstring += '"woonkamer":0,'
jsonstring += '"bureau":0,'
jsonstring += '"bureaulamp":0,'
jsonstring += '"stopcontact":0,'
jsonstring += '"ventilatie":0,'
jsonstring += '"alarmsysteem":0,'
jsonstring += '"keukendeur":0,'
jsonstring += '"schuurdeur":0,'
jsonstring += '"gevellamp":0'
jsonstring += '}'
schakelaars =	json.loads( jsonstring )

jsonstring  = '{'
jsonstring += '"schuurtemperatuur":0,'
jsonstring += '"badkmrtmp":0,'
jsonstring += '"badkmrlvh":0,'
jsonstring += '"badkmrdpl":0'
jsonstring += '}'
sensoren	=	json.loads( jsonstring )

def ipaddress():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]
    
def rgbbrightness( udpport ):
	udpport = 1208
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
	sock.setblocking(0) 
	sock.settimeout(5.0) 
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
	sock.bind(('', udpport)) 
	
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	sock.sendto("dimmer", ("192.168.178.255", udpport))
				
	helderheid = ""
	while True:
		try:
			helderheid, addr = sock.recvfrom(100) # buffer size is 100 bytes
			if addr[0] != ipaddress(): # filter out self-sent messages
				break
		except socket.timeout:
			print("socket timeout")
			break
	sock.close()				
	return int(helderheid[1:])

def udpbroadcast( bericht, poort=5005 ):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 	
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	
#	print("verzenden via udp: %s"%commando)
	sock.sendto(bericht, ("192.168.178.255", poort))
	sock.close()
	return 

def telegram(message="...", chat_id="12463680"):
#	Johannes_Smits	=  "12463680"
#	alarmsysteem	= "-24143102"
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage?chat_id=%s&text=%s" % (chat_id, message) )
	return r.status_code
	
def getstatus():
	global schakelaars, sensoren
	
	schakelaars["rgbledstrip"] = 1 if rgbbrightness( 1208 ) > 0 else 1
	
	# keuken
	resultaat = requests.get("http://192.168.178.203", timeout=1)
	if (resultaat.status_code == requests.codes.ok):
		schakelaars["keukenverlichting"] = json.loads( resultaat.text )["aanuit1"]
		schakelaars["stopcontact"] = json.loads( resultaat.text )["aanuit2"]
		schakelaars["keukendeur"] = json.loads( resultaat.text )["keukendeur"]

	# woonkamer
	resultaat = requests.get("http://192.168.178.208?gpio2", timeout=1)
	if (resultaat.status_code == requests.codes.ok):
		schakelaars["woonkamer"] = json.loads( resultaat.text )
		
	# bureau
	resultaat = requests.get("http://192.168.178.210", timeout=1)
	if (resultaat.status_code == requests.codes.ok):
		if "aan" in resultaat.text:
			schakelaars["bureau"] = 1
		elif "uit" in resultaat.text:
			schakelaars["bureau"] = 0
			
	# bureaulamp
	resultaat = requests.get("http://192.168.178.202?gpio04", timeout=1)
	if (resultaat.status_code == requests.codes.ok):
		schakelaars["bureaulamp"] = resultaat.text[-1]

	# ventilatie
	resultaat = requests.get("http://192.168.178.205/status", timeout=1)
	if (resultaat.status_code == requests.codes.ok):
		schakelaars["ventilatie"] = resultaat.text

	# badkamer
	resultaat = requests.get("http://192.168.178.17/status", timeout=1)
	if (resultaat.status_code == requests.codes.ok):
		sensoren["badkmrtmp"] = resultaat.json()["temperatuur"]
		sensoren["badkmrlvh"] = resultaat.json()["luchtvochtigheid"]
		sensoren["badkmrdpl"] = resultaat.json()["drempelwaarde"]
		
	# alarmsysteem
	resultaat = requests.get("http://%s/action/panelCondGet"%woonveilig_ip, auth=HTTPBasicAuth(woonveilig_us, woonveilig_pw), timeout=1)
	if (resultaat.status_code == requests.codes.ok):
		if	resultaat.text.find("Disarm"):
			schakelaars["alarmsysteem"] = 3
		elif resultaat.text.find("Armhome"):
			schakelaars["alarmsysteem"] = 0
		elif resultaat.text.find("Arm"):
			schakelaars["alarmsysteem"] = 1
			
	status = "Status \033[3m%s\033[0m - "%time.strftime("om %H:%M:%S")
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
		
		_get = dict(item.split("=") for item in urlparse(self.path).query.split("&"))
		for item in _get:
			print ( "{%s=%s}"%(item, _get[item]) )
		
		if 'opdracht' in _get.keys():
			print(_get["opdracht"])
			if _get["opdracht"] == "udpbroadcast":
				if 'bericht' in _get.keys() and 'udppoort' in _get.keys():
					udpbroadcast(_get["bericht"], int(_get["udppoort"]))
					
			if _get["opdracht"] == "status":
				print("Ophalen status")
				getstatus()
				
		elif 'accessoire' in _get.keys():
# -----		rgbledstrip
			if _get["accessoire"] == "rgbledstrip":
				if 'kleur' in _get.keys():
					print(_get["kleur"])
					
				if 'dimmer' in _get.keys():
					print(_get["dimmer"])
					
# -----		stopcontact
			elif _get["accessoire"] == "stopcontact":
				if 'aanofuit' in _get.keys():
					resultaat = requests.get("http://192.168.178.203/%s:2"%_get["aanofuit"], timeout=5)
					if (resultaat.status_code == requests.codes.ok):
						schakelaars["stopcontact"] = json.loads( resultaat.text )["aanuit2"]
				self.wfile.write( schakelaars["stopcontact"] )

# -----		ventilatie
			elif _get["accessoire"] == "ventilatie":
				if 'aanofuit' in _get.keys():
					resultaat = requests.get("http://192.168.178.205?%s"%_get["aanofuit"], timeout=5)
					if (resultaat.status_code == requests.codes.ok):
						schakelaars["ventilatie"] = resultaat.text
				self.wfile.write( schakelaars["ventilatie"] )
			
# -----		schaarlamp
			elif _get["accessoire"] == "schaarlamp":
				if 'aanofuit' in _get.keys():
					resultaat = requests.get("http://192.168.178.203/%s:1"%_get["aanofuit"], timeout=5)
					if (resultaat.status_code == requests.codes.ok):
						schakelaars["schaarlamp"] = json.loads( resultaat.text )["aanuit1"]
				self.wfile.write( schakelaars["schaarlamp"] )
				
# -----		woonkamer
			elif _get["accessoire"] == "woonkamer":
				if 'aanofuit' in _get.keys():
					resultaat = requests.get("http://192.168.178.201?%s"%_get["aanofuit"], timeout=5)
					resultaat = requests.get("http://192.168.178.204/aanuit=%s"%_get["aanofuit"], timeout=5)
					resultaat = requests.get("http://192.168.178.208?gpio2=%s"%_get["aanofuit"], timeout=5)
					if (resultaat.status_code == requests.codes.ok):
						schakelaars["woonkamer"] = json.loads( resultaat.text )
				self.wfile.write( schakelaars["woonkamer"] )

# -----		bureaulamp
			elif _get["accessoire"] == "bureaulamp":
				if 'aanofuit' in _get.keys():
					resultaat = requests.get("http://192.168.178.202?gpio04=%s"%_get["aanofuit"], timeout=5)
					if (resultaat.status_code == requests.codes.ok):
						schakelaars["bureaulamp"] = resultaat.text[-1]
				self.wfile.write( schakelaars["bureaulamp"] )
				
# -----		gevellamp
			elif _get["accessoire"] == "gevellamp":
				if 'aanofuit' in _get.keys():
					resultaat = requests.get("http://192.168.178.208?gpio0=%s"%_get["aanofuit"], timeout=5)
					if (resultaat.status_code == requests.codes.ok):
						schakelaars["gevellamp"] = resultaat.text[-1]
				self.wfile.write( schakelaars["gevellamp"] )
				
# -----		bureau
			elif _get["accessoire"] == "bureau":
				if 'aanofuit' in _get.keys():
					resultaat = requests.get("http://192.168.178.210?%s"%_get["aanofuit"], timeout=5)
					if (resultaat.status_code == requests.codes.ok):
						if any(s in resultaat.text for s in ("aan","uit")):
							schakelaars["bureau"] = 1 if "aan" in resultaat.text else 0
				self.wfile.write( schakelaars["bureau"] )
							
# -----		alarmsysteem				
			elif _get["accessoire"] == "alarmsysteem":
				if 'aanofuit' in _get.keys():
					aanofuit = 0 if _get["aanofuit"] else 2
					# instellen systeem
					requests.get('http://%s/action/panelCondPost?mode=%s'%(woonveilig_ip, aanofuit), auth=HTTPBasicAuth(woonveilig_us, woonveilig_pw), timeout=5)
					# opvragen instelling
					resultaat = requests.get("http://%s/action/panelCondGet"%woonveilig_ip, auth=HTTPBasicAuth(woonveilig_us, woonveilig_pw), timeout=5)
					if (resultaat.status_code == requests.codes.ok):
						if	  "Disarm" in resultaat.text:
							schakelaars["alarmsysteem"] = 3
						elif "Armhome" in resultaat.text:
							schakelaars["alarmsysteem"] = 0
						elif	 "Arm" in resultaat.text:
							schakelaars["alarmsysteem"] = 1
					tekst = "uit" if "Disarm" in resultaat.text else "actief"
					telegram( "Alarmsysteem is %s"%tekst )
				self.wfile.write( schakelaars["alarmsysteem"] )	
				
			elif _get["accessoire"] == "badkamer":
				self.wfile.write( "{\"temperature\":%s,\"humidity\":%s}"%(sensoren["badkmrtmp"],sensoren["badkmrlvh"]) )

			elif _get["accessoire"] == "tuinhuis":
			   self.wfile.write( "{\"temperature\":%s}"%(sensoren["schuurtemperatuur"]) )
		return
		
try:
	# Create a web server and define the handler to manage the incoming request
	print ("\033[2J(%s) Ophalen actuele status\n"%ipaddress() )
	getstatus()
	print ("(%s) Huidige status geladen\n"%ipaddress() )
	
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	print ("\033[3mHTTPserver gestart op poort %d\033[0m\n"%PORT_NUMBER)
	
	# Wait forever for incoming http requests
	server.serve_forever()

except KeyboardInterrupt:
	print ('^C received, shutting down the web server')
	server.socket.close()
	