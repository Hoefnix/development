#!/usr/bin/python3

# monitor voor aantal zaken
# - UDP poort 5005 

import datetime
import json
import os
import requests
import socket
import subprocess
import time

extrnip = requests.get("http://myexternalip.com/raw").content.strip()

# telegram adressen
Johannes_Smits	=  "12463680"
alarmsysteem	= "-24143102"
deurbel			=  "12463680" # -15033899
kattenluikID 	= "-12086796"

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
			berichtje("Sending: %s\n"%message)
			self.s.sendto(bytes(message,"UTF-8"),('<broadcast>',self.port))
			
def nachtlicht(iplamp = "http://192.168.178.203"):
	if nacht():
		if (int(json.loads(requests.get(iplamp).content)["aanuit1"]) == 0):
			print("We gaan schakelen")
			with open('/var/tmp/ledstrip.sh', 'w') as script:			
				script.write("curl -m1 -ss %s?aan:1 > /dev/null 2>&1\nsleep 60\ncurl -m1 -ss %s?uit:1 > /dev/null 2>&1\n"%(iplamp,iplamp))
			os.chmod("/var/tmp/ledstrip.sh", 775)
			subprocess.call("/var/tmp/ledstrip.sh & > /dev/null 2>&1", shell=True)
		else:
			print("al aan, we doen niks")
	return
	
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
	#				berichtje ("%s de deur van het tuinhuis staat nog open"%kreten[random.randrange(6)])

	def updatestatus(self, openofdicht = 0):
	#	berichtje("Update deur %d"%openofdicht)
		if openofdicht in range(2): # check of de waarde is 0 of 1
			if openofdicht != self.laatstestatus:
				tekst = "open" if (openofdicht == 1) else "dicht"
				telegramMsg ("12463680", "Tuinhuisdeur is %s"%tekst) # laat het de wereld weten
				try:
					requests.get("http://192.168.178.100:1208?schuurdeur:%s"%tekst, timeout=2)	# update de status in homebridge
				except:				
					print("\033[3m%s\033[0m - probleem bij deurstatus update"%time.strftime("%H:%M:%S"))
				self.laatstestatus = openofdicht	# update de status voor de volgende controle
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
			p = subprocess.Popen('/usr/bin/arp-scan -q --interface=eth0 192.168.178.0/24', shell=True, stdout=subprocess.PIPE)
			# zet alle gevonden devices in dictionary
			self.devices = {}
			for line in p.stdout:
				regel = line.decode("utf8").strip()
				if regel.startswith('192'):
					self.devices.update({regel[regel.find("\t"):].strip():regel[:regel.find("\t")]})
					
			# zoek voor alle bekende mac's in lijst
			for naam, macid in self.macids.items():
				if macid in self.devices:
					berichtje("iPhone %s is op het netwerk (%s)"%(naam,macid))
					self.gezien = naam
					self.gevonden = time.time()
					#break
		return int((time.time()-self.gevonden)/60)
					
def telegramMsg(chat_id="12463680", message="..."):
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage?chat_id=%s&text=%s" % (chat_id, message) )
	return r.status_code
	
def tgSendPhoto( chat_id="12463680", imagePath="" ):
	data	= {'chat_id': chat_id}
	files	= {'photo': (imagePath, open(imagePath, "rb"))}
	r = requests.post("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendPhoto", data=data, files=files)
	return r.status_code
	
def standvanzaken():
	if not os.path.isfile("/var/tmp/huisstatus.json"):
		with open("/var/tmp/huisstatus.json", "w") as bestand:
			bestand.write( '{"keukendeur":0, "woonveilig":3}' )
	with open('/var/tmp/huisstatus.json', 'r') as bestand:
		huisstatus = json.loads(bestand.read())
	return huisstatus 			

# Instellen UDP listener
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.setblocking(0)
sock.settimeout(1)
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
			berichtje("Sending: %s\n"%message)
			self.s.sendto(bytes(message,"UTF-8"),('<broadcast>',self.port))

print ("\033[2JMonitor UDP/5005")
print ("\033[1m\033[36mControl-C om te stoppen\033[0m")
if not os.path.exists("/opt/433Utils/RPi_utils/codesend"):
	print ("\033[33m - Geen 433Mhz commando's (/opt/433Utils/RPi_utils/codesend missend)\033[0m")
	
try:
	while True:
		huisstatus = standvanzaken()

		try :
			jsonstr, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			jsonstr = jsonstr.decode('utf-8')
			print ("[%s] UDP: %s (%s)" % (time.strftime("%a om %H:%M:%S"), jsonstr.strip(), addr) )
				
			if "tuinhuis" in jsonstr:
#				Nieuwe status wegschrijven voor de affediening
				with open("/var/tmp/tuinhuis.json", "w") as text_file:
					text_file.write( jsonstr )
        
			elif "kerstverlichting" in jsonstr:
				if os.path.exists("/opt/433Utils/RPi_utils/codesend"):
					try:
						code = json.loads(jsonstr.strip())["kerstverlichting"]
						subprocess.call("sudo /opt/433Utils/RPi_utils/codesend %s" % code, shell=True)	
						print ("\033[32mKerstverlichting verstuur code: %s\033[0m" % code )				
					except:
						continue
				
				if os.path.exists("/usr/bin/codesend"):
					try:
						code = json.loads(jsonstr.strip())["kerstverlichting"]
						subprocess.call("sudo /usr/bin/codesend %s" % code, shell=True)	
						print ("\033[32mKerstverlichting verstuur code: %s\033[0m" % code )				
					except:
						continue
						
			elif "keukendeur" in jsonstr:
				openofdicht = int(json.loads(jsonstr.strip())["keukendeur"])
				nachtlicht() if (openofdicht == 1) else None	#lampje in de keuken aan doen
				if (openofdicht != huisstatus["keukendeur"]):
					opendicht = "open" if (openofdicht == 1) else "dicht"
					requests.get("http://192.168.178.120:1208?keukendeur:%s"%opendicht)
					huisstatus["keukendeur"] = openofdicht
					with open("/var/tmp/huisstatus.json", "w") as bestand:
						bestand.write( json.dumps( huisstatus ))

		except socket.timeout:
			continue

except (KeyboardInterrupt):#, RuntimeError, TypeError, NameError, ValueError):
	print(time.strftime("%a om %H:%M:%S")+ " Shutting down...")
	sock.close()
	print("Done")