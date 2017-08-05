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
import RPi.GPIO as GPIO
import socket
import subprocess
import time
import ephem
import random

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

def erWordtGebeld(channel):
	berichtje( "De deurbel %s"%GPIO.input(deurblpin))
	telegram(deurbel, image = "/var/tmp/deurbel.jpg")		
#	returncode = subprocess.Popen("/usr/bin/fswebcam -c /opt/developmt/deurcam.cfg", shell=True)
		
def alarmGaatAf(pin):
	# alleen een bericht sturen als het alarmsysteem ingeschakeld is
	if (requests.get("http://admin:admin1234@192.168.178.3/action/panelCondGet").text.find("Arm")>0):
		telegramMsg(alarmsysteem, "%s - Alarmsysteem gaat af" % time.strftime("%a om %H:%M:%S") )
		time.sleep(60) # minuutje pauze, teveel berichten is ook niet goed
	return

def telegramMsg(chat_id="12463680", message="..."):
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage?chat_id=%s&text=%s" % (chat_id, message) )
	print( message )
	return r.status_code
	
def telegram( chat_id="12463680", message = None, image = None ):
	if not message is None: 
		print("telegram bericht %s"%message)
		payload	= {"chat_id":chat_id, "text":message, "parse_mode":"HTML"}
		r = requests.get("https://api.telegram.org/bot328955454:AAEmupBEwE0D7V1vsoB8Xo5YY1wGIFpu6AE/sendMessage", params=payload)	
		return (r.json()["ok"])
		
	elif not image is None:
		print("telegam foto %s"%image)
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
		if (int(json.loads(requests.get(iplamp).content)["aanuit1"]) == 0):
			print("We gaan schakelen")
			with open('/var/tmp/ledstrip.sh', 'w') as script:			
				script.write("curl -m1 -ss %s?aan:1 > /dev/null 2>&1\nsleep 60\ncurl -m1 -ss %s?uit:1 > /dev/null 2>&1\n"%(iplamp,iplamp))
			os.chmod("/var/tmp/ledstrip.sh", 775)
			subprocess.call("/var/tmp/ledstrip.sh & > /dev/null 2>&1", shell=True)
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

def magstoren(bericht=False):
	try:
		with open('/var/www/html/remote.json') as remote:
			data = json.load(remote)

		slapen	= int(data["start"].replace(":",""))
		opstaan = int(data["einde"].replace(":",""))
		extrnip	= data["extip"]
	
		uurnu	= int( "%02d%02d"% (datetime.datetime.now().hour, datetime.datetime.now().minute))
		if bericht:
			print ("\033[32m\033[KNiet storen tussen %04d en %04d, het is nu %04d, extern ip is %s\033[0m\n"%(slapen, opstaan, uurnu, extrnip))
	
		if slapen > opstaan:
			if uurnu < slapen and uurnu > opstaan:
				return 1 # mag storen
			else:
				return 0
		else:
			if uurnu > slapen and uurnu < opstaan:
				return 0 # niet storen
			else:
				return 1 # mag storen
	except:
		return 0
		
def standvanzaken():
	huisstatus = json.loads('{"keukendeur":0}')
	return huisstatus 			

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
				
def berichtje(tekst = ""):
	print("\033[3m%s\033[0m - %s"%(time.strftime("%H:%M:%S"),tekst))
	
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
						
GPIO.setmode(GPIO.BCM)

GPIO.setup(geluidpin, GPIO.IN, GPIO.PUD_DOWN)
GPIO.add_event_detect(geluidpin, GPIO.RISING, callback=alarmGaatAf)

GPIO.setup(deurblpin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(deurblpin, GPIO.FALLING, callback=erWordtGebeld)

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
			berichtje("Sending: %s\n"%message)
			self.s.sendto(bytes(message,"UTF-8"),('<broadcast>',self.port))

print ("\033[2JMonitor geluid, deurbel, UDP/5005")
print ("\033[3mControl-C om te stoppen\033[0m")

magstoren(True)	# even om te testen of de instellingen goed ingelezen worden
tuinhuisdeur = tuinhuis()
arp = arpscanner(300)

licht = udpinit(seconden=120)

try:
	startijd = time.time()
	huisstatus = {"keukendeur":0}
	
	while True:
		licht.broadcast('{"kattenluik":"licht"}')

	#	check de status van het alarmsysteem
		w = requests.get("http://admin:admin1234@192.168.178.3/action/panelCondGet")
		if (w.status_code == requests.codes.ok):	
			age = arp.scan()
			if (w.text.find("Disarm")>0):
				if magstoren() and (age > 45):
					if ((time.time()-startijd)/60>5): # om de vijf minuten
						startijd = time.time() # reset timer
						bericht  = "Al %s minuten niemand gevonden.\n"%age
						bericht += "http://%s:1208?alarmsysteem:arm\n"%extrnip
						telegramMsg(Johannes_Smits, bericht)
			elif (w.text.find(    "Arm")>0):
				arp.gevonden = time.time()
			elif (w.text.find("Armhome")>0):
				arp.gevonden = time.time()

		tuinhuisdeur.waarschuwing(600)

		try :
			jsonstr, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			jsonstr = jsonstr.decode("utf8")
			berichtje("\033[33mUDP: %s (%s)" % (jsonstr.strip(), addr) )
			
			if "tuinhuis" in jsonstr:
				tuinhuisdeur.updatestatus( int(json.loads(jsonstr.strip())["deur"]) )
				# nu we toch bezig zijn, update de status van de temperatuur ook gelijk even in homebridge 
				temperatuur = json.loads(jsonstr.strip())["temperatuur"]
				if int(temperatuur) in range(-20,50): # simpel error checking, is de waarde is tussen -19 en 49
					try:
						requests.get("http://192.168.178.50:1208?tuinhuisupdate:%s"%temperatuur, timeout=5)
					except requests.Timeout:				
						print("\033[3m%s\033[0m - serverPi timed out bij temperatuur update"%time.strftime("%H:%M:%S"))
					except:				
						print("\033[3m%s\033[0m - temperatuur update mislukt"%time.strftime("%H:%M:%S"))

			elif "kerstverlichting" in jsonstr:
				codesend = "/opt/433Utils/RPi_utils/codesend"
				if not os.path.exists(codesend):
					codesend = "/usr/bin/codesend"
					if not os.path.exists(codesend):
						continue
				try:
					code = json.loads(jsonstr.strip())["kerstverlichting"]
					subprocess.call("sudo %s %s" % (codesend, code), shell=True)	
					print ("\033[32mKerstverlichting verstuur code: %s\033[0m" % code )				
				except:
					continue
									
			elif "reset aanwezigheid" in jsonstr:
				arp.gevonden = time.time()
				telegramMsg(Johannes_Smits, "Aanwezigheidstimer gereset")

			elif "aanwezig" in jsonstr:
				telegramMsg(Johannes_Smits, "%s, %s seconden geleden gezien"%(arp.gezien, int((time.time()-arp.gevonden)/60)) )
				
			elif "deurbel" in jsonstr:
				erWordtGebeld(0)
								
			elif "keukendeur" in jsonstr:
				openofdicht = int(json.loads(jsonstr.strip())["keukendeur"])
				nachtlicht() if (openofdicht == 1) else None	#lampje in de keuken aan doen
				if (openofdicht != huisstatus["keukendeur"]):
					opendicht = "open" if (openofdicht == 1) else "dicht"
					requests.get("http://192.168.178.50:1208?keukendeur:%s"%opendicht)
					huisstatus["keukendeur"] = openofdicht					
					with open("/var/tmp/huisstatus.json", "w") as bestand:
						bestand.write( json.dumps( huisstatus ))			
					
			elif "alarmsysteem" in jsonstr and "reset" in jsonstr:
				arp.gevonden = time.time()

		except socket.timeout:
			continue

except (KeyboardInterrupt):#, RuntimeError, TypeError, NameError, ValueError):
	print (time.strftime("%a om %H:%M:%S")+ " Shutting down...")
	sock.close()
	GPIO.remove_event_detect(geluidpin)
	GPIO.remove_event_detect(deurblpin)
	GPIO.cleanup()
	print ("Done")