# monitor voor twee zaken
# - deurbel (nog niet aangesloten)
# - geluidssensor (voor het alarm)
# - UDP poort 5005 
# - waarschuwen als niemand thuis is 

import datetime
import json
import os
import requests
import RPi.GPIO as GPIO
import socket
import subprocess
import time
import ephem

geluidpin =  4
deurblpin = 24

slapen	= 2200
opstaan	= 0700
extrnip = requests.get("http://myexternalip.com/raw").content.strip()

# telegram adressen
Johannes_Smits	=  "12463680"
alarmsysteem	= "-24143102"
deurbel 		=  "12463680" # -15033899

def touch(path):
    with open(path, 'a'):
        os.utime(path, None)

def erWordtGebeld(channel):
	# maken en verzenden van de foto wordt door fswebcam geregeld
	returncode = subprocess.Popen("/usr/bin/fswebcam -c /opt/develop/deurcam.cfg", shell=True)
	print ( returncode )
	print('\033[31mDeurbel werd ingedrukt op ' + time.strftime("%a om %H:%M:%S")+"\033[0m\n")
	return
		
def alarmGaatAf(pin):
	# alleen een bericht sturen als het alarmsysteem ingeschakeld is
	if (requests.get("http://admin:admin1234@192.168.178.3/action/panelCondGet").content.find("Arm")>0):
		telegramMsg(alarmsysteem, "%s - Alarmsysteem gaat af" % time.strftime("%a om %H:%M:%S") )
		time.sleep(60) # minuutje pauze, teveel berichten is ook niet goed
	return

def telegramMsg(chat_id="12463680", message="..."):
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage?chat_id=%s&text=%s" % (chat_id, message) )
	return r.status_code
	
def tgSendPhoto( chat_id="12463680", imagePath="" ):
	data	= {'chat_id': chat_id}
	files	= {'photo': (imagePath, open(imagePath, "rb"))}
	r = requests.post("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendPhoto", data=data, files=files)
	return r.status_code

def nachtlicht(ipledstrip = "http://192.168.178.211"):
	if nacht():		
		if json.loads(requests.get("http://192.168.178.46/keuken.php/?lamp").text)["lamp"]:
			with open('/var/tmp/ledstrip.sh', 'w') as script:
				script.write("curl -m1 -ss %s?aan > /dev/null 2>&1\nsleep 60\ncurl -m1 -ss %s?uit > /dev/null 2>&1\n"%(ipledstrip,ipledstrip))
			os.chmod("/var/tmp/ledstrip.sh", 0775)
			subprocess.call("/var/tmp/ledstrip.sh & > /dev/null 2>&1", shell=True)
	return
	
def nacht():
	#Latitude en Longitude van sibeliusweg 66, capelle
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

def magstoren():
	with open('/var/www/html/remote.json') as remote:
		data = json.load(remote)

	slapen	= int(data["start"].replace(":",""))
	opstaan = int(data["einde"].replace(":",""))
	extrnip	= data["extip"]
	
	uurnu	= int( "%02d%02d"% (datetime.datetime.now().hour, datetime.datetime.now().minute))
	print ("\033[32m\033[KNiet storen tussen %04d en %04d, het is nu %04d, extern ip is %s\033[0m"%(slapen, opstaan, uurnu, extrnip))
	
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
			
GPIO.setmode(GPIO.BCM)

GPIO.setup(geluidpin, GPIO.IN, GPIO.PUD_DOWN)
GPIO.add_event_detect(geluidpin, GPIO.RISING, callback=alarmGaatAf)

GPIO.setup(deurblpin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(deurblpin, GPIO.FALLING, callback=erWordtGebeld, bouncetime=500)

# Instellen UDP listener
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.setblocking(0)
sock.settimeout(0.1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', UDP_PORT)) # udp port 5005

print ("\033[2JMonitor geluid, deurbel, UDP/5005")
print ("\033[3mControl-C om te stoppen\033[0m")

magstoren()	# even om te testen of de instellingen goed ingelezen worden

try:
	startijd = time.time()
	while True:
	#	check de status van het alarmsysteem
		w = requests.get("http://admin:admin1234@192.168.178.3/action/panelCondGet")
		if (w.content.find("Disarm")>0):
			age = int( ( time.time() - os.stat('/var/tmp/alarmsysteem').st_mtime ) / 60)
			if (age > 45 ): # na 45 minuten waarschuwen
				print ( ((time.time()-startijd)/60) )
				if ((time.time()-startijd)/60>5): # om de vijf minuten
					if (magstoren()):
						bericht = "Al %s minuten niemand gezien in huis. Alarm aanzetten?\nhttp://%s:100/remote.php?alarmsysteem"%(age, extrnip)
						telegramMsg(Johannes_Smits, bericht)
						startijd = time.time() # reset timer
						
		elif (w.content.find("Arm")>0):
			touch('/var/tmp/alarmsysteem');
			
		elif (w.content.find("Armhome")>0):
			touch('/var/tmp/alarmsysteem');

		try :
			jsonstr, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			print ("[%s] UDP: %s" % (time.strftime("%a om %H:%M:%S"), jsonstr.strip()) )
			if "tuinhuisdeur" in jsonstr:
				ontvangen = int(json.loads(jsonstr.strip())["tuinhuisdeur"])
				opendicht = "gaat open" if (ontvangen == 1) else "is weer dicht"
				telegramMsg ("12463680", "Tuinhuisdeur %s"%opendicht )
				
			elif "keukendeur" in jsonstr:
				ontvangen = int(json.loads(jsonstr.strip())["keukendeur"])
				nachtlicht() if (ontvangen == 1) else None	#lampje in de keuken aan doen
				opendicht = "gaat open" if (ontvangen == 1) else "is weer dicht"
				telegramMsg ("12463680", "Keukendeur %s"%opendicht )
				
#			elif "kattenluik" in jsonstr:
#				print json.loads(jsonstr.strip())["kattenluik"]
#				opendicht = "gaat open" if (json.loads(jsonstr.strip())["kattenluik"] == 0) else "is weer dicht"
#				telegramMsg ("12463680", "Kattenluik %s"%opendicht )
				
		except socket.timeout:
			continue

except (KeyboardInterrupt):#, RuntimeError, TypeError, NameError, ValueError):
	print time.strftime("%a om %H:%M:%S")+ " Shutting down..."
	sock.close()
	GPIO.remove_event_detect(geluidpin)
	GPIO.remove_event_detect(deurblpin)
	GPIO.cleanup()
	print "Done"