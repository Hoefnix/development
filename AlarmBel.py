# monitor voor aantal zaken
# - deurbel
# - geluidssensor (voor het alarm)

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

# telegram adressen
Johannes_Smits	=  "12463680"
alarmsysteem	= "-24143102"
deurbel			= "-15033899"

alarmStart		= time.time()
		
class initDeurbel(object):
	def __init__(self):
		self.start = time.time()
		
	def trigger(self, pin):
		if time.time()-self.start > 1: # maximaal een foto per seconde
			self.start = time.time()
			telegram(deurbel, image = "/var/tmp/deurbel.jpg")
		else:
			berichtje("Te snel, foto niet verstuurd")
		udp5005.broadcast( '{"deurbel":%s}'%GPIO.input(pin))
		
def alarmGaatAf(pin):
	global alarmStart
	# alleen een bericht sturen als het alarmsysteem ingeschakeld is
	if (requests.get("http://admin:admin1234@192.168.178.3/action/panelCondGet").text.find("Arm")>0):
		if time.time()-alarmStart > 30: # maximaal een bericht per 30 seconden
			alarmStart = time.time()
			telegramMsg(alarmsysteem, "ALARM GAAT AF" )
	else:
		telegram(message="<i>Geluid in meterkast</i>" )
	return

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
			
def telegramMsg(chat_id="12463680", message="..."):
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage?chat_id=%s&text=%s" % (chat_id, message) )
	print( message )
	return r.status_code
	
def telegram( chat_id="12463680", message = None, image = None ):
	if not message is None: 
		print("telegram bericht %s"%message)
		payload	= {"chat_id":chat_id, "text":message, "parse_mode":"HTML"}
		r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage", params=payload)	
		return (r.json()["ok"])
		
	elif not image is None:
		print("telegam foto %s"%image)
		url	= "https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendPhoto"
		data	= {'chat_id': chat_id}
		files	= {'photo': (image, open(image, "rb"))}
		r = requests.post(url , data=data, files=files)
		return (r.json()["ok"])
				
def berichtje(tekst = ""):
	print("\033[3m%s\033[0m - %s"%(time.strftime("%H:%M:%S"),tekst))
		
GPIO.setmode(GPIO.BCM)

GPIO.setup(geluidpin, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(deurblpin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

deBel = initDeurbel()

GPIO.add_event_detect(deurblpin, GPIO.BOTH, callback=deBel.trigger )
GPIO.add_event_detect(geluidpin, GPIO.RISING, callback=alarmGaatAf)

# Instellen UDP listener
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.setblocking(0)
sock.settimeout(10)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', UDP_PORT)) # udp port 5005

udp5005 = udpinit(5005, 1)

print ("\033[0;0H\033[2JMonitor geluid, deurbel")
print ("\033[3mControl-C om te stoppen\033[0m")

try:
	while True:
		try :
			jsonstr, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			jsonstr = jsonstr.decode("utf8")
			berichtje("\033[33mUDP: %s (%s)" % (jsonstr.strip(), addr) )
			if "kerstverlichting" in jsonstr:
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

		except socket.timeout:
			continue

except (KeyboardInterrupt):#, RuntimeError, TypeError, NameError, ValueError):
	berichtje("Shutting down...")
	sock.close()
	
	GPIO.remove_event_detect(geluidpin)
	GPIO.remove_event_detect(deurblpin)
	GPIO.cleanup()
	
	berichtje("Starting %s..."%__file__)
	subprocess.call("screen -dmS monitor python3 %s"%__file__, shell=True)
