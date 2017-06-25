#!/usr/bin/python

import json
import subprocess
import sys
import time
import os
from datetime import datetime
import socket
import requests

# Send UDP broadcast packets

MYPORT = 5005

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('', 0))
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

tgAPIcode = "112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU"
JSONresult= "/var/tmp/result.json"
Johannes_Smits = "12463680"  
Werk_in_de_straat = "-4417251"

def allin( zin, lijst ):
	waarde = True
	for woord in lijst:
		if woord not in zin:
			waarde = False
			break
	return waarde

def strtonum(str):
	try: 
		return int(str) 
	except ValueError: 
		return 0

def metingen( tgID, watte):
	resultaat = requests.get("http://192.168.178.202/?metingen")
	if (resultaat.status_code == requests.codes.ok):
		telegramMsg(tgID, "%s is het zo'n %d graden" % (watte, round(float(resultaat.json()[watte]))) )
	return (resultaat.status_code == requests.codes.ok)

def respond(chatID, bericht = None):
	if not bericht is None:
		bericht = socket.gethostname() + " zegt: <i>'"+bericht+"'</i>"
		payload = {'chat_id':chatID, 'text':bericht, 'parse_mode':'HTML'}
		r = httpGet("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage", params=payload)
	return 0

def telegram( chatID = "12463680", bericht = None):
	if not bericht is None:
		bericht = socket.gethostname() + " zegt: <i>'"+bericht+"'</i>"
		payload = {'chat_id':chatID, 'text':bericht, 'parse_mode':'HTML'}
		r = httpGet("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage", params=payload)
	return

def httpGet( url, auth = None, params = ""):
	resultaat = requests.Response
	resultaat.status_code = -1
	try:
		resultaat = requests.get( url, params=params, auth=auth )
	except:
		bericht("fout bij aanroep %s"%url)
	return resultaat
	
def bericht(message=None):
	if not message is None:
		print("\033[3m%s\033[0m - %s"%(time.strftime("%H:%M:%S"),message))

def doSomething( string ):
	global udp
	
	message = string["text"].lower()

	if	allin(message, ["licht", "aan", "woonkamer"]):
		respond(string["from"]["id"], "Woonkamerverlichting wordt nu aangezet" )
		bericht(httpGet("http://192.168.178.100:1208?woonkamer:aan").url)
		bericht(httpGet("http://192.168.178.100:1208?bureaulamp:aan").url)
							
	elif allin(message, ["licht", "uit", "woonkamer"]):
		respond(string["from"]["id"], "Woonkamerverlichting wordt nu uitgezet" )
		bericht(httpGet("http://192.168.178.100:1208?woonkamer:uit").url)
		bericht(httpGet("http://192.168.178.100:1208?bureaulamp:uit").url)
		
	elif allin(message, ['welterusten']):
		respond(string["from"]["id"], "Licht wordt overal uitgezet" )
		bericht(httpGet("http://192.168.178.100:1208?keuken:uit").url)
		bericht(httpGet("http://192.168.178.100:1208?woonkamer:uit").url)
		bericht(httpGet("http://192.168.178.100:1208?bureaulamp:uit").url)
		bericht(httpGet("http://192.168.178.210?uit" ).url) # bureau
		
	elif allin(message, ["foto", "kattenluik"]):
		udp.broadcast('{"kattenluik":"foto"}')
		
	elif allin(message, ["test", "kattenluik"]):
		udp.broadcast('{"kattenluik":"test"}')
		
	elif message == "externalip":
		ipadres = httpGet("http://myexternalip.com/raw").content.decode("utf-8").strip(' \t\n\r')
		respond(string["from"]["id"], ipadres)
		
	elif	 message == "bureau aan":
		respond(string["from"]["id"], "Bureau en printer worden aangezet" )
		bericht(httpGet("http://192.168.178.100:1208?bureau:aan").url)

	elif	 message == "bureau uit":
		respond(string["from"]["id"], "Bureau en printer worden uitgezet" )
		bericht(httpGet("http://192.168.178.100:1208?bureau:uit").url)
		
	elif message[:4] == "ping":
		respond(string["from"]["id"], "pong" )
		
	else:
		respond(string["from"]["id"], "%s"%message )
	
class udpinit(object):
	def __init__(self, myport = 5005):
		self.port = myport
		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

	def broadcast(self, message = ""):
		bericht("Sending: %s\n"%message)
		self.s.sendto(bytes(message,"UTF-8"),('<broadcast>',self.port))

subproc_output = subprocess.check_output("/usr/bin/curl -s -X POST https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/getMe", shell=True)
parsed_json_data = json.loads(subproc_output.decode())
if parsed_json_data["ok"]:
	print ( "[%s] %s (%s) is gestart op "% (socket.gethostname(), parsed_json_data["result"]["username"], parsed_json_data["result"]["first_name"]) + time.strftime("%a om %H:%M:%S") )
	telegram( bericht = "@%s (<i>%s</i>) op de <b>%s</b> is gestart "% (parsed_json_data["result"]["username"], parsed_json_data["result"]["first_name"], socket.gethostname()) + time.strftime("om %H:%M:%S") )

lastUpdateId = 0	
try:
	udp = udpinit()
	offset = 0
	url = "https://api.telegram.org/bot%s/getUpdates"%tgAPIcode 
	
	while (True):		
		payload = 'offset=%s'%offset
		try:
			response = requests.post( url, params=payload, timeout=3)
		except requests.Timeout as e:
			bericht("Time-out getupdates %s"%e)
			continue
		except:
			bericht("No updates %s, %s"%(offset, url))
			continue

		if (response.status_code == requests.codes.ok):
			if response.json()["ok"]:					# lees de berichten in
				for element in response.json()["result"]:		# voor het geval als er meerdere berichten staan te wachten
					msge = "message"
					if msge not in element:
						msge = "edited_message" 
						if msge not in element:
							continue						# niet geinteresseerd in andere berichten

					for key in element[msge]:		# wat voor een soort bericht is het
						if	 key == "group_chat_created":
							break
						elif key == "new_chat_participant":
							break
						elif key == "new_chat_photo":
							break
						elif key == "text":
							doSomething(element[msge])
							offset = element["update_id"] + 1
		time.sleep(1)						# om processor te ontlasten
			
except KeyboardInterrupt:
# , RuntimeError, TypeError, NameError, ValueError):
	print(time.strftime("%a om %H:%M:%S")+ " Shutting down...")
	print("Done, bye bye...")
