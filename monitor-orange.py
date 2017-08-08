# monitor voor aantal zaken
# - deurbel
# - geluidssensor (voor het alarm)
# - UDP poort 5005 
# - scannen bekende mac-adressen en waarschuwen als niemand thuis is 
# - stuurt broadcast iedere vijf minuten voor licht bij kattenluik

import datetime
import json
import os
import requests
import socket
import subprocess
import time
import ephem
import random
import threading

geluidpin =  4
deurblpin = 24

slapen	= 2200
opstaan	=  700
extrnip = requests.get("http://myexternalip.com/raw").text.strip()

vorigecontrole = time.time()

# telegram adressen
Johannes_Smits	=  "12463680"
alarmsysteem	= "-24143102"
deurbel			= "-15033899"
		
def touch(path):
    with open(path, 'a'):
        os.utime(path, None)

def telegramMsg(chat_id="12463680", message="..."):
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage?chat_id=%s&text=%s" % (chat_id, message) )
	print( message )
	return r.status_code
	
def telegram( chat_id="12463680", message = None, image = None ):
	if not message is None: 
#		print("telegram bericht %s"%message)
		url = "https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage"
		payload	= {"chat_id":chat_id, "text":message, "parse_mode":"HTML"}
#		r = requests.get("https://api.telegram.org/bot328955454:AAEmupBEwE0D7V1vsoB8Xo5YY1wGIFpu6AE/sendMessage", params=payload)	
		r = requests.get(url, params=payload)	
		return (r.json()["ok"])
		
	elif not image is None:
#		print("telegam foto %s"%image)
		url	= "https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendPhoto"
		data	= {'chat_id': chat_id}
		files	= {'photo': (image, open(image, "rb"))}
		r	= requests.post(url , data=data, files=files)
		return (r.json()["ok"])
			
def tgSendPhoto( chat_id="12463680", imagePath="" ):
	data	= {'chat_id': chat_id}
	files	= {'photo': (imagePath, open(imagePath, "rb"))}
	r = requests.post("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendPhoto", data=data, files=files)
	return r.status_code

def nachtlicht(iplamp = "http://192.168.178.203"):
	if nacht():
		if (int(json.loads(requests.get(iplamp).text)["aanuit1"]) == 0):
			# start een timer thread om de lamp na x seconden weer uit te zetten
			threading.Timer(120, requests.get, ["%s?uit:1"%iplamp]).start()
			requests.get("%s?aan:1"%iplamp) # zet de lamp aan
		else:
			print("al aan, we doen niks")
	return
	
def nacht():
#	Latitude en Longitude van sibeliusweg 66, capelle
	home_lat  = '51.916905'
	home_long =  '4.563472'
	
	# where am i 
	o = ephem.Observer()
	o.lat  = home_lat
	o.long = home_long
		
	# define sun as object of interest
	s = ephem.Sun()
	sunrise = o.next_rising(s)
	sunset  = o.next_setting(s)

	sr_next = ephem.localtime(sunrise)
	ss_next = ephem.localtime(sunset)		
	
	return 1 if (sr_next < ss_next) else 0			

class tuinhuis:	
	def __init__(self):
		self.laatstestatus	= 0
		self.vorigecontrole = time.time()    # instance variable unique to each instance
	
	def waarschuwing(self, interval = 600, uren = [22,23]):
		if ((time.time() - self.vorigecontrole) > interval):
			self.vorigecontrole = time.time()
			if (int(time.strftime("%H")) in uren):
				self.vorigecontrole = time.time()
				if not self.laatstestatus: #  de deur is dicht
					print (time.strftime("%H:%M:%S ") + "De deur van het tuinhuis is dicht")
				elif self.laatstestatus: #  de deur is open
					kreten = ['Ter info;','Hey','Hi', 'Christie,', 'Wist je...', 'Bij Toutatis!', 'Allemachtig,', 'Hallo is daar iemand,']
					telegramMsg(alarmsysteem, "%s de deur van het tuinhuis staat nog open"%kreten[random.randrange(6)])

	def updatestatus(self, openofdicht = 0):
		if openofdicht in range(2): # check of de waarde is 0 of 1
			if openofdicht != self.laatstestatus:
				tekst = "open" if (openofdicht == 1) else "dicht"
				telegramMsg ("12463680", "Tuinhuisdeur is %s"%tekst) # laat het de wereld weten
				try:
					requests.get("http://192.168.178.50:1208?schuurdeur:%s"%tekst, timeout=2)	# update de status in homebridge
				except:				
					print("\033[3m%s\033[0m - probleem bij deurstatus update"%time.strftime("%H:%M:%S"))
				self.laatstestatus = openofdicht	# update de status voor de volgende controle
				
def bericht(tekst = "", viaTelegram=False, viaPushover=False):
	print("\033[3m%s\033[0m - %s"%(time.strftime("%H:%M:%S"),tekst))
	if viaTelegram:
		telegram( message=tekst )
	if viaPushover:
		pushover( bericht=tekst )
		
def pushover( bericht = "", titel = None ):
	titel = "oPi-monitor" if titel is None else titel 
	try:
		r = requests.post('https://api.pushover.net/1/messages.json', data = {'token':'aYs6YxK8qV1KnGV1LEHzQQtFTrCutk', 'user':'udEe5uL7YjuyYLyhQXBjvjnqiGGsf8', 'title':titel, 'message':bericht})
	except requests.Timeout as e:
		bericht("Pushover - %s"%e)
	except:
		bericht("Pushover - Fout")
	return
		
class arpscanner:
	def __init__(self, interval=60):
		self.devices = {}
		self.gevonden = time.time()
		self.interval = interval
		self.gezien = ""
		self.vorigecontrole	= 0
		self.macids =		 {  "Leanne":"70:ec:e4:ce:d8:5e"}
		self.macids.update({"Christie":"d0:25:98:2c:a7:df"})
		self.macids.update({     "Rik":"bc:6c:21:0c:b4:6b"})
		self.macids.update({    "Hans":"e0:5f:45:3f:df:d1"})
		self.macids.update({   "Sjors":"cc:25:ef:11:52:3e"})
		
	def scan(self):
		if ((time.time() - self.vorigecontrole) > self.interval):
			self.vorigecontrole = time.time()
			bericht("arp-scan wordt gestart...")
			p = subprocess.Popen('sudo /usr/bin/arp-scan -q --interface=eth0 192.168.178.0/24', shell=True, stdout=subprocess.PIPE)
			# zet alle gevonden devices in dictionary
			self.devices = {}
			for line in p.stdout:
				regel = line.decode("utf8").strip()
				if regel.startswith('192'):
					self.devices.update({regel[regel.find("\t"):].strip():regel[:regel.find("\t")]})
					
			# zoek voor alle bekende mac's in lijst
			for naam, macid in self.macids.items():
				if macid in self.devices:
					bericht("iPhone %s is op het netwerk (%s)"%(naam,macid))
					self.gezien = naam
					self.gevonden = time.time()
					#break
		return int((time.time()-self.gevonden)/60)

# Instellen UDP listener
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.setblocking(0)
sock.settimeout(0.5)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', UDP_PORT)) # udp port 5005

class udpinit(object):
	def __init__(self, myport = 5005, seconden = 0):
		self.port = myport
		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self.start = time.time()
		self.interval = seconden

	def broadcast(self, message = ""):
		if self.interval is 0:
			return
		elif time.time()-self.start > self.interval:
			self.start = time.time()
#			bericht("Sending: %s\n"%message)
			self.s.sendto(bytes(message,"UTF-8"),('<broadcast>',self.port))
			
bericht("%s gestart\n"%__file__, viaPushover = True)

tuinhuisdeur = tuinhuis()
arp = arpscanner(300)

try:
	startijd = time.time()
	huisstatus = {"keukendeur":0}
	
	while True:

	#	check de status van het alarmsysteem
		try:
			if ((time.time()-startijd)/60>5):	# om de vijf minuten
				startijd = time.time()				# reset timer
				w = requests.get("http://admin:admin1234@192.168.178.3/action/panelCondGet", timeout=5)
				if (w.status_code == requests.codes.ok):	
					age = arp.scan()
					if (w.text.find("Disarm")>0):
						if not nacht() and (age > 45):
							bericht  = "Al %s minuten niemand gevonden.\n"%age
							bericht += "http://%s:1208?alarmsysteem:arm\n"%extrnip
							telegramMsg(Johannes_Smits, bericht)
				elif (w.text.find(    "Arm")>0):
					arp.gevonden = time.time()
				elif (w.text.find("Armhome")>0):
					arp.gevonden = time.time()
	
		except Exception as e:	
			bericht("Exception bij status alarmsysteem (%s)"%e)
			pass

		tuinhuisdeur.waarschuwing(600)

		try :
			jsonstr, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			jsonstr = jsonstr.decode("utf8")
			
			bericht("ontvangen via UDP: %s (%s)" % (jsonstr.strip(), addr) )
			
			if "tuinhuis" in jsonstr:
				tuinhuisdeur.updatestatus( int(json.loads(jsonstr.strip())["deur"]) )
				# nu we toch bezig zijn, update de status van de temperatuur ook gelijk even in homebridge 
				temperatuur = json.loads(jsonstr.strip())["temperatuur"]
				if int(temperatuur) in range(-20,50): # simpel error checking, is de waarde is tussen -19 en 49
					try:
						r=requests.get("http://192.168.178.50:1208?tuinhuisupdate:%s"%temperatuur, timeout=5)
						bericht(r.text)
					except requests.Timeout:				
						bericht("Time-out bij temperatuur update")
					except:				
						bericht("Temperatuur update mislukt")
									
			elif "reset aanwezigheid" in jsonstr:
				arp.gevonden = time.time()
				telegramMsg(Johannes_Smits, "Aanwezigheidstimer gereset")

			elif "aanwezig" in jsonstr:
				telegramMsg(Johannes_Smits, "%s, %s seconden geleden gezien"%(arp.gezien, int((time.time()-arp.gevonden)/60)) )
				
			elif "deurbel" in jsonstr:
				telegramMsg(Johannes_Smits, "Deurbel")
								
			elif "keukendeur" in jsonstr:
				try:
					openofdicht = int(json.loads(jsonstr.strip())["keukendeur"])
				except:
					continue
					
				nachtlicht() if (openofdicht == 1) else None	#lampje in de keuken aan doen
				if (openofdicht != huisstatus["keukendeur"]):
					opendicht = "open" if (openofdicht == 1) else "dicht"
					try:
						requests.get("http://192.168.178.50:1208?keukendeur:%s"%opendicht, timeout=1)
					except requests.Timeout:				
						bericht("Time-out bij update deurstatus (192.168.178.50)")
					except:				
						bericht("Fout bij update deurstatus")

					huisstatus["keukendeur"] = openofdicht

					opendicht = "true" if openofdicht == 0 else "false"
					requests.get("http://127.0.0.1:51828/?accessoryId=achterdeur&state=%s"%opendicht)

					bericht(huisstatus["keukendeur"])
					
			elif "alarmsysteem" in jsonstr and "reset" in jsonstr:
				arp.gevonden = time.time()

		except socket.timeout:
			continue

except (KeyboardInterrupt):#, RuntimeError, TypeError, NameError, ValueError):
	bericht (time.strftime("%a om %H:%M:%S")+ " Restarting...")
	sock.close()
	subprocess.call("screen -dmLS monitor python3 %s"%__file__, shell=True)
	