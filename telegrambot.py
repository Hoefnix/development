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

def tgGetUpdates( offset ):
	curlCmd = "/usr/bin/curl -s -X POST  https://api.telegram.org/bot"
	curlCmd += tgAPIcode 
	curlCmd += "/getUpdates "
	curlCmd += " -d offset=%s " % offset

	resultaat = subprocess.check_output(curlCmd, shell=True)
	terug = json.loads( resultaat.decode() )
	if ( type( terug ) is dict):
		return terug
	return json.loads('{"ok":false,"result":[]}')

def botUpdates( offset ):
	url = "https://api.telegram.org/bot%s/getUpdates"%tgAPIcode 
	payload = 'offset=%s&limit=1'%offset
	try:
		response = requests.post( url, params=payload, timeout=3)
		if (response.status_code == requests.codes.ok):
			if 'update_id' in response.text:
				bericht("offset %s, response %s"%(offset,response.json()))
				return response.json()
	except:
		bericht("botUpdates %s, %s"%(offset, url))
		pass
	return {"ok":"false","result":[]}

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

def telegramMsg(chatID, bericht = None):
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
	
	while (True):		
#		parsed_json_data = botUpdates(lastUpdateId)
		parsed_json_data = tgGetUpdates(lastUpdateId)		# lees de berichten in
		if parsed_json_data["ok"]:							# lees de berichten in5
			doorgaan = False
#			berich(parsed_json_data["result"])
			for element in parsed_json_data["result"]:		# voor het geval als er meerdere berichten staan te wachten
				search = "message"							# de bericht tekst kan staan in "message"
				if search not in element:
					search = "edited_message"				# of in "edited_message"
					if search not in element:
						continue							# niet geinteresseerd in andere berichten
#				bericht(search)
				for key in element[search]:					# wat voor een soort bericht is het
					if	 key == "group_chat_created":
						break
					elif key == "new_chat_participant":
						break
					elif key == "new_chat_photo":
						break
					elif key == "text":
						message = element[search]["text"].lower()
						if message[:1] == "/":
							message = message[1:]
							
						print (time.strftime("%a om %H:%M:%S ") + message)
						if	allin(message, ["licht", "aan", "woonkamer"]):
							telegramMsg(element[search]["from"]["id"], "Woonkamerverlichting wordt nu aangezet" )
							bericht(httpGet("http://192.168.178.50:1208?woonkamer:aan").url)
							bericht(httpGet("http://192.168.178.50:1208?bureaulamp:aan").url)
							
						elif allin(message, ["licht", "uit", "woonkamer"]):
							telegramMsg(element[search]["from"]["id"], "Woonkamerverlichting wordt nu uitgezet" )
							bericht(httpGet("http://192.168.178.50:1208?woonkamer:uit").url)
							bericht(httpGet("http://192.168.178.50:1208?bureaulamp:uit").url)
							
						elif message == "externalip":
							ipadres = httpGet("http://myexternalip.com/raw").content.decode("utf-8").strip(' \t\n\r')
							telegramMsg(element[search]["from"]["id"], ipadres)
							
						elif allin(message, ['bureaulamp', 'aan']):
							telegramMsg(element[search]["from"]["id"], "Bureaulamp wordt nu aangezet" )	
							bericht(httpGet("http://192.168.178.50:1208?bureaulamp:aan").url)
							
						elif allin(message, ['bureaulamp', 'uit']):
							telegramMsg(element[search]["from"]["id"], "Bureaulamp wordt nu uitgezet" )	
							bericht(httpGet("http://192.168.178.50:1208?bureaulamp:uit").url)
								
						elif	 message == "bureau aan":
							if (socket.gethostname().lower() == "serverpi"):
								telegramMsg(element[search]["from"]["id"], "Bureau en printer worden aangezet" )
								bericht(httpGet("http://192.168.178.50:1208?bureau:aan").url)

						elif	 message == "bureau uit":
							if (socket.gethostname().lower() == "serverpi"):
								telegramMsg(element[search]["from"]["id"], "Bureau en printer worden uitgezet" )
								bericht(httpGet("http://192.168.178.50:1208?bureau:uit").url)
		
						elif	 message == "sproeier aan":
							telegramMsg(element[search]["from"]["id"], "Sproeier wordt aangezet" )
							bericht(httpGet("http://192.168.178.50:1208?aan:2").url)
							
						elif	 message == "sproeier uit":
							telegramMsg(element[search]["from"]["id"], "Sproeier wordt uitgezet" )
							bericht(httpGet("http://192.168.178.50:1208?uit:2").url)		
		
						elif allin(message, ['licht', 'aan', 'keuken']):
							if (socket.gethostname().lower() == "serverpi"):
								telegramMsg(element[search]["from"]["id"], "Licht in de keuken wordt aangezet" )
								bericht(httpGet("http://192.168.178.50:1208?keuken:aan").url)

						elif allin(message, ['licht', 'uit', 'keuken']):
							if (socket.gethostname().lower() == "serverpi"):
								telegramMsg(element[search]["from"]["id"], "Licht in de keuken wordt uitgezet" )
								bericht(httpGet("http://192.168.178.50:1208?keuken:uit").url)
				
						elif allin(message, ['welterusten']):
							if (socket.gethostname().lower() == "serverpi"):
								telegramMsg(element[search]["from"]["id"], "Licht wordt overal uitgezet" )
								bericht(httpGet("http://192.168.178.50:1208?keuken:uit").url)
								bericht(httpGet("http://192.168.178.50:1208?woonkamer:uit").url)
								bericht(httpGet("http://192.168.178.50:1208?bureaulamp:uit").url)
								bericht(httpGet("http://192.168.178.210?uit" ).url) # bureau
				
						elif allin(message, ['reset', 'aanwezig']):
							udp.broadcast("reset aanwezigheid")

						elif 	message == "aanwezig":
							udp.broadcast("aanwezig")
				
						elif 	message[:5] == "alarm":
							commando =  message.replace("alarm", "").strip()
							if   commando == "aan":
								resultaat = httpGet("http://192.168.178.50:1208?alarmsysteem:arm")
								if (resultaat.status_code == requests.codes.ok):
									telegramMsg(element[search]["from"]["id"], "Alarm aan gezet" )
							elif commando == "uit":
								resultaat = httpGet("http://192.168.178.50:1208?alarmsysteem:disarm")
								if (resultaat.status_code == requests.codes.ok):
									telegramMsg(element[search]["from"]["id"], "Alarm uit gezet" )
							
						elif 	allin(message, ["foto", "kattenluik"]):
							if (socket.gethostname().lower() == "kattenpi"):
								udp.broadcast('{"kattenluik":"foto"}')

						elif 	allin(message, ["test", "kattenluik"]):
							if (socket.gethostname().lower() == "kattenpi"):
								#s.sendto(bytes('{"kattenluik":"test"}',"utf-8"), ('192.168.178.255', MYPORT))
								udp.broadcast('{"kattenluik":"test"}')

						elif	message[:11] == "temperatuur":
							if (socket.gethostname().lower() == "serverpi"):
								if  message.endswith("buiten"):
									metingen(element[search]["from"]["id"], "buiten")
								elif message.endswith("bureau"):
									metingen(element[search]["from"]["id"], "temperatuur")
								elif message.endswith("woonkamer"):
									resultaat = httpGet("http://192.168.178.201/?temperatuur")
									if (resultaat.status_code is requests.codes.ok):
										telegramMsg(element[search]["from"]["id"], "Temperatuur in de woonkamer %s graden"%resultaat.text)
								elif message.endswith("leanne"):
									resultaat = httpGet("http://192.168.178.50:1208?leanne:temperatuur")	# temp meter
									if (resultaat.status_code is requests.codes.ok):
										telegramMsg(element[search]["from"]["id"], "Het is %s graden in leannes kamer"%resultaat.text )
								else:
									telegramMsg(element[search]["from"]["id"], "gebruik: temperatuur [buiten/bureau/woonkamer/leanne]")
																		
						elif 	message[:6] == "re-boot":
							botUpdates(element["update_id"]+1)	# confirm last update andres blijft hij rebooten
							if (message[-8:] == socket.gethostname().lower()):
								telegramMsg(element[search]["from"]["id"], "restarting" )
								subprocess.call("/usr/bin/sudo /sbin/shutdown -r now", shell=True)
							elif (message[-8:] == "keukenpi"):
								telegramMsg(element[search]["from"]["id"], "restarting keukenPi" )
								subprocess.call("ssh root@192.168.178.46 /usr/bin/sudo /sbin/shutdown -r now", shell=True)
							elif (message[-11:] == "woonkamerpi"):
								telegramMsg(element[search]["from"]["id"], "restarting woonkamerPi" )
								subprocess.call("ssh root@192.168.178.13 /usr/bin/sudo /sbin/shutdown -r now", shell=True)

						elif message[:4] == "ping":
							telegramMsg(element[search]["from"]["id"], "pong" )
							
						else:
							telegramMsg(element[search]["from"]["id"], "%s"%message )
						
				lastUpdateId = element["update_id"] + 1
				
		time.sleep(4)	# om processor te ontlasten
			
except KeyboardInterrupt:
# , RuntimeError, TypeError, NameError, ValueError):
	print(time.strftime("%a om %H:%M:%S")+ " Shutting down...")
	tgGetUpdates( lastUpdateId )
	print("Done, bye bye...")
